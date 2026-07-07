"""
Empty-state scaffolding: a brand-new circle (just the creator, no content) gets
a warm, guided prompt with one clear action on each MVP screen. (Assertions use
apostrophe-free substrings since Jinja escapes ' → &#39;.)
"""
from app import db
from app.models import User, Person


def test_events_empty_state_has_action(app, auth_client):
    html = auth_client.get('/events').data.decode()
    assert 'No gatherings yet' in html
    assert '/events/add' in html and 'Create an event' in html


def test_photos_empty_state(app, auth_client):
    html = auth_client.get('/albums').data.decode()
    assert 'No photos yet' in html


def test_activity_empty_state_is_mvp_accurate(app, auth_client):
    html = auth_client.get('/activity').data.decode()
    assert 'Nothing here yet' in html
    # Copy references only live MVP features (events/photos), not hidden ones.
    assert 'the highlights will show up here' in html


def test_members_just_you_nudge_for_fresh_circle(app, auth_client):
    # Seed family has only the creator → the first-run nudge shows.
    html = auth_client.get('/members').data.decode()
    assert 'just you so far' in html
    assert '/admin/add-member' in html and 'Add a family member' in html


def test_members_nudge_disappears_once_family_added(app, auth_client):
    with app.app_context():
        admin = User.query.filter_by(email='admin@pease-family.com').first()
        db.session.add(Person(name='Second Person', family_id=admin.family_id))
        db.session.commit()
    html = auth_client.get('/members').data.decode()
    assert 'just you so far' not in html


def test_empty_state_macro_renders_shared_classes(app, auth_client):
    # The reusable component exposes stable hooks for Jeffrey to style.
    html = auth_client.get('/events').data.decode()
    assert 'class="empty-state"' in html and 'empty-state-title' in html
