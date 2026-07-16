"""
Deleting an account-less family member: the account.delete_person helper must
clean up every reference (no dangling FK / crash), and honor detach vs purge for
the media directly attributable to them.
"""
from datetime import date
from app import db
from app.account import delete_person
from app.models import (
    User, Person, ParentRelationship, SpouseRelationship, Album, Photo, PhotoTag,
    StoryPrompt, StoryResponse, GiftRegistry, GiftRegistryItem, Event, EventRSVP,
)


def _admin():
    return User.query.filter_by(email='admin@pease-family.com').first()


def _seed_member_with_deps(app, name='Elder Pease'):
    """An account-less person wired into relationships + content, returns ids."""
    admin = _admin()
    fid = admin.family_id
    target = Person(name=name, family_id=fid)
    kid = Person(name='Kid Pease', family_id=fid)
    spouse = Person(name='Spouse Pease', family_id=fid)
    db.session.add_all([target, kid, spouse]); db.session.flush()

    db.session.add(ParentRelationship(parent_id=target.id, child_id=kid.id, role='parent'))
    db.session.add(SpouseRelationship(person1_id=target.id, person2_id=spouse.id, confirmed=True))

    album = Album(family_id=fid, name='Reunion'); db.session.add(album); db.session.flush()
    photo = Photo(family_id=fid, album_id=album.id, path='photos/x.jpg',
                  uploaded_by_id=admin.person_id)
    db.session.add(photo); db.session.flush()
    db.session.add(PhotoTag(photo_id=photo.id, person_id=target.id, tagged_by_id=admin.person_id))

    prompt = StoryPrompt(family_id=fid, person_id=target.id, question='Your first job?',
                         source='manual')
    db.session.add(prompt); db.session.flush()
    db.session.add(StoryResponse(prompt_id=prompt.id, answer='Paper route', answered_by_id=admin.person_id))

    reg = GiftRegistry(family_id=fid, recipient_person_id=target.id, title='Birthday',
                       created_by_id=admin.person_id)
    db.session.add(reg); db.session.flush()
    db.session.add(GiftRegistryItem(registry_id=reg.id, name='Book'))

    ev = Event(family_id=fid, name='Picnic', start_date=date(2026, 8, 1))
    db.session.add(ev); db.session.flush()
    db.session.add(EventRSVP(event_id=ev.id, person_id=target.id, status='yes'))

    db.session.commit()
    return dict(target=target.id, kid=kid.id, spouse=spouse.id,
                photo=photo.id, prompt=prompt.id, reg=reg.id, event=ev.id)


def test_detach_removes_person_but_keeps_shared_photo(app, auth_client):
    with app.app_context():
        ids = _seed_member_with_deps(app)
        delete_person(db.session.get(Person, ids['target']), purge=False)

        assert db.session.get(Person, ids['target']) is None            # gone
        assert db.session.get(Person, ids['kid']) is not None           # kid stays
        assert db.session.get(Person, ids['spouse']) is not None        # spouse stays
        # relationships to the deleted person are gone
        assert ParentRelationship.query.filter_by(parent_id=ids['target']).count() == 0
        assert SpouseRelationship.query.filter(
            db.or_(SpouseRelationship.person1_id == ids['target'],
                   SpouseRelationship.person2_id == ids['target'])).count() == 0
        # about-them content removed
        assert db.session.get(StoryPrompt, ids['prompt']) is None
        assert db.session.get(GiftRegistry, ids['reg']) is None
        assert EventRSVP.query.filter_by(person_id=ids['target']).count() == 0
        assert PhotoTag.query.filter_by(person_id=ids['target']).count() == 0
        # DETACH keeps the shared photo (just untagged)
        assert db.session.get(Photo, ids['photo']) is not None


def test_purge_also_deletes_photos_they_are_tagged_in(app, auth_client):
    with app.app_context():
        ids = _seed_member_with_deps(app, name='Purge Pease')
        delete_person(db.session.get(Person, ids['target']), purge=True)
        assert db.session.get(Person, ids['target']) is None
        assert db.session.get(Photo, ids['photo']) is None              # PURGE deletes the photo
        assert PhotoTag.query.filter_by(photo_id=ids['photo']).count() == 0


# ── route + guards ────────────────────────────────────────────────────────────

def _accountless(app, name='Tree Only'):
    admin = _admin()
    p = Person(name=name, family_id=admin.family_id)
    db.session.add(p); db.session.commit()
    return p.id


def _account_holder(app, email):
    admin = _admin()
    p = Person(name='Has Account', family_id=admin.family_id)
    db.session.add(p); db.session.flush()
    u = User(family_id=admin.family_id, person_id=p.id, first_name='Has', last_name='Account',
             email=email, status='approved', email_verified=True, is_admin=False)
    u.set_password('Password1!'); db.session.add(u); db.session.commit()
    return p.id


def test_route_deletes_accountless_member(app, auth_client):
    with app.app_context():
        ids = _seed_member_with_deps(app, name='Route Pease')
        pid, photo = ids['target'], ids['photo']
    r = auth_client.post(f'/admin/member/{pid}/delete', data={'mode': 'detach'}, follow_redirects=False)
    assert r.status_code == 302
    with app.app_context():
        assert db.session.get(Person, pid) is None
        assert db.session.get(Photo, photo) is not None      # detach keeps the photo


def test_route_blocks_member_with_account(app, auth_client):
    with app.app_context():
        pid = _account_holder(app, 'hasacct@pease-family.com')
    r = auth_client.post(f'/admin/member/{pid}/delete', data={'mode': 'purge'}, follow_redirects=False)
    assert r.status_code == 302
    with app.app_context():
        assert db.session.get(Person, pid) is not None       # NOT deleted — has an account


def test_route_requires_admin(app):
    with app.app_context():
        tid = _accountless(app, 'Victim Pease')
        mid = _account_holder(app, 'member2@pease-family.com')  # non-admin account
    c = app.test_client()
    c.post('/login', data={'email': 'member2@pease-family.com', 'password': 'Password1!'})
    r = c.post(f'/admin/member/{tid}/delete', data={'mode': 'detach'}, follow_redirects=False)
    assert r.status_code in (302, 403)
    with app.app_context():
        assert db.session.get(Person, tid) is not None       # non-admin can't delete


def test_route_family_isolation(app, other_auth_client):
    with app.app_context():
        tid = _accountless(app, 'Pease Only')                # belongs to Pease family
    # other-family admin can't delete a Pease member
    other_auth_client.post(f'/admin/member/{tid}/delete', data={'mode': 'detach'})
    with app.app_context():
        assert db.session.get(Person, tid) is not None


def test_delete_ui_shown_for_accountless_only(app, auth_client):
    with app.app_context():
        aid = _accountless(app, 'Tree Only')
        acct_id = _account_holder(app, 'shown@pease-family.com')
        own_id = _admin().person_id
    assert 'delete-member-modal' in auth_client.get(f'/person/{aid}').data.decode()       # account-less → shown
    assert 'delete-member-modal' not in auth_client.get(f'/person/{acct_id}').data.decode()  # has account → hidden
    assert 'delete-member-modal' not in auth_client.get(f'/person/{own_id}').data.decode()   # own profile → hidden
