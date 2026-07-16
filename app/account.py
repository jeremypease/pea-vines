"""Account and family deletion.

Two paths:
- delete_user_account(user): removes the user's account and personal data.
  Their Person record stays in the family tree (it belongs to the family's
  shared history; an admin can remove it separately).
- purge_family(family): removes the entire family and all its data, including
  stored R2/local objects and the Stripe subscription. Used when the last
  account in a family is deleted.
"""
from . import db
from .models import (
    User, Person, SpouseRelationship, Event, Announcement, Album,
    Photo, Poll, GreetingCard, Checklist, Location, Document, ChatMessage,
    Notification, NotificationPreference, UserDevice, OAuthAccount,
    CalendarToken, UserPodMembership, SupportNote, PlatformAuditLog,
    FamilyPayoutAccount, EventPaymentRecord, StoryPrompt,
)
from .storage import delete_object


class LastAdminError(Exception):
    """User is the family's only admin but other members remain."""


def _scrub_user_rows(user):
    """Delete or detach every row tied to a user account (not their Person)."""
    ChatMessage.query.filter_by(author_id=user.id).delete()
    Notification.query.filter_by(user_id=user.id).delete()
    NotificationPreference.query.filter_by(user_id=user.id).delete()
    UserDevice.query.filter_by(user_id=user.id).delete()
    OAuthAccount.query.filter_by(user_id=user.id).delete()
    CalendarToken.query.filter_by(user_id=user.id).delete()
    SupportNote.query.filter_by(author_id=user.id).delete()
    PlatformAuditLog.query.filter_by(actor_id=user.id).update({'actor_id': None})
    # Payment records are the family's financial history — keep the amounts,
    # drop the person link (GDPR erasure with retained accounting data).
    EventPaymentRecord.query.filter_by(payer_user_id=user.id).update({'payer_user_id': None})
    User.query.filter_by(approved_by_id=user.id).update({'approved_by_id': None})
    User.query.filter_by(invited_by_id=user.id).update({'invited_by_id': None})


def _other_active_users(family_id, user):
    return (
        User.query
        .filter(User.family_id == family_id, User.id != user.id)
        .filter(User.status.in_(['approved', 'pending', 'invited']))
        .all()
    )


def delete_user_account(user):
    """Delete a user account. Returns 'purged' if the whole family was
    removed (user was the last account), or 'deleted' for a user-only delete.

    Raises LastAdminError when the user is the only admin of a family that
    still has other members — they must promote another admin first.
    """
    family = user.family
    others = _other_active_users(family.id, user)
    if not others:
        purge_family(family)
        return 'purged'

    if user.is_admin and not any(u.is_admin for u in others):
        raise LastAdminError()

    _scrub_user_rows(user)
    db.session.delete(user)  # memberships + passkeys cascade
    db.session.commit()
    return 'deleted'


def delete_person(person, purge=False):
    """Fully remove an account-less family member and clean up every reference,
    so no foreign key is left dangling.

    purge=False (detach) — drop the person's relationships and the rows that are
      only about them (tags, RSVPs, story prompts, gift registries, greeting
      cards to them, …), but KEEP shared family content: photos they're tagged
      in stay (just untagged), and anything they created/uploaded stays with its
      authorship cleared.
    purge=True — additionally delete the media directly attributable to them:
      the photos they uploaded, the photos they're tagged in, and the documents
      they uploaded.

    The caller must ensure the person has no user account (account-less only).
    """
    from .models import (
        event_sleeping_assignments, PhotoTag, Photo, EventRSVP, PollVote,
        CardSignature, AnnouncementReaction, EventComment, EventSurveyResponse,
        CarpoolOffer, ScheduledMessage, StoryResponse, GiftRegistry,
        GiftRegistryItem, GreetingCard, Album, Announcement, Poll, Checklist,
        ChecklistItem, EventAssignment, EventMealItem, EventMeal,
    )
    pid = person.id
    delete_object(person.photo_path)

    # ── Rows that are only about this person → always removed ─────────────────
    SpouseRelationship.query.filter(
        db.or_(SpouseRelationship.person1_id == pid, SpouseRelationship.person2_id == pid)
    ).delete(synchronize_session=False)
    db.session.execute(
        event_sleeping_assignments.delete().where(event_sleeping_assignments.c.person_id == pid)
    )
    for cls in (EventRSVP, PollVote, CardSignature, AnnouncementReaction,
                EventComment, EventSurveyResponse, CarpoolOffer):
        cls.query.filter_by(person_id=pid).delete(synchronize_session=False)
    ScheduledMessage.query.filter_by(recipient_person_id=pid).delete(synchronize_session=False)
    for sp in StoryPrompt.query.filter_by(person_id=pid).all():
        db.session.delete(sp)                     # responses cascade (delete-orphan)
    for reg in GiftRegistry.query.filter_by(recipient_person_id=pid).all():
        db.session.delete(reg)                    # items cascade
    for gc in GreetingCard.query.filter_by(recipient_id=pid).all():
        db.session.delete(gc)                     # signatures cascade

    # ── Media directly attributable to them ──────────────────────────────────
    tagged_ids = {t.photo_id for t in PhotoTag.query.filter_by(person_id=pid).all()}
    if purge:
        upload_ids = {p.id for p in Photo.query.filter_by(uploaded_by_id=pid).all()}
        if tagged_ids | upload_ids:
            for ph in Photo.query.filter(Photo.id.in_(tagged_ids | upload_ids)).all():
                delete_object(ph.path)
                delete_object(ph.thumb_path)
                db.session.delete(ph)             # its remaining tags cascade
        for doc in Document.query.filter_by(uploader_id=pid).all():
            delete_object(doc.storage_key)
            db.session.delete(doc)
    else:
        PhotoTag.query.filter_by(person_id=pid).delete(synchronize_session=False)  # untag, keep photo

    # ── Nullable authorship / claims on shared content → cleared (both modes) ─
    # (In purge, the uploaded photos/docs above are already gone, so those
    #  updates simply match nothing.)
    for cls, col in (
        (Photo, 'uploaded_by_id'), (Album, 'created_by_id'), (Announcement, 'author_id'),
        (Poll, 'created_by_id'), (Checklist, 'created_by_id'), (Document, 'uploader_id'),
        (ChecklistItem, 'claimed_by_id'), (EventAssignment, 'claimed_by_id'),
        (EventMealItem, 'assigned_to_id'), (EventMeal, 'assigned_family_id'),
        (PhotoTag, 'tagged_by_id'), (StoryResponse, 'answered_by_id'),
        (GiftRegistryItem, 'claimed_by_person_id'), (GiftRegistry, 'created_by_id'),
        (GreetingCard, 'created_by_id'),
    ):
        cls.query.filter_by(**{col: pid}).update({col: None}, synchronize_session=False)

    db.session.delete(person)                     # parent_relationships cascade
    db.session.commit()


def _delete_family_objects(family):
    """Remove all stored files (R2 or local) belonging to a family."""
    for photo in Photo.query.filter_by(family_id=family.id).all():
        delete_object(photo.path)
        delete_object(photo.thumb_path)
    for person in Person.query.filter_by(family_id=family.id).all():
        delete_object(person.photo_path)
    for event in Event.query.filter_by(family_id=family.id).all():
        delete_object(event.cover_image_path)
    for doc in Document.query.filter_by(family_id=family.id).all():
        delete_object(doc.storage_key)


def _cancel_stripe(family):
    if not family.stripe_subscription_id:
        return
    try:
        from .billing import _stripe
        s = _stripe()
        if s:
            s.Subscription.cancel(family.stripe_subscription_id)
    except Exception:
        # Family is being purged regardless; Stripe will also stop charging
        # when the payment method's invoices fail. Don't block deletion.
        pass


def purge_family(family):
    """Delete a family and everything in it."""
    _delete_family_objects(family)
    _cancel_stripe(family)

    users = User.query.filter_by(family_id=family.id).all()
    for u in users:
        _scrub_user_rows(u)

    ChatMessage.query.filter_by(family_id=family.id).delete()
    SupportNote.query.filter_by(pod_id=family.id).delete()
    Document.query.filter_by(family_id=family.id).delete()
    # StoryPrompt must precede Person/Family deletion — its person_id and
    # family_id are NOT NULL, so leftover rows block the purge. Its responses
    # cascade (StoryPrompt.responses = delete-orphan).
    for model in (Location, Checklist, GreetingCard, Poll, Album,
                  Announcement, Event, StoryPrompt):
        for row in model.query.filter_by(family_id=family.id).all():
            db.session.delete(row)  # per-aggregate cascades handle children
    FamilyPayoutAccount.query.filter_by(family_id=family.id).delete()

    person_ids = [p.id for p in Person.query.filter_by(family_id=family.id).all()]
    if person_ids:
        SpouseRelationship.query.filter(
            db.or_(SpouseRelationship.person1_id.in_(person_ids),
                   SpouseRelationship.person2_id.in_(person_ids))
        ).delete(synchronize_session=False)
    db.session.flush()
    for u in users:
        db.session.delete(u)
    db.session.flush()
    for p in Person.query.filter_by(family_id=family.id).all():
        db.session.delete(p)  # parent relationships cascade
    UserPodMembership.query.filter_by(family_id=family.id).delete(synchronize_session=False)
    db.session.delete(family)
    db.session.commit()
