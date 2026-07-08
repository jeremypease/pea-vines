"""Members (not just contributors/admins) can add photos to an album.
Album creation stays with contributors/admins; the paid gate is unchanged."""
from app import db
from app.models import User, Person, Album


def _member(app, email='photomember@pease-family.com'):
    admin = User.query.filter_by(email='admin@pease-family.com').first()
    p = Person(name='Photo Member', family_id=admin.family_id)
    db.session.add(p); db.session.flush()
    u = User(family_id=admin.family_id, person_id=p.id, first_name='Photo',
             last_name='Member', email=email, status='approved', email_verified=True,
             is_admin=False, is_delegate=False)
    u.set_password('Password1!')
    db.session.add(u); db.session.commit()
    return u.id


def _album(app):
    admin = User.query.filter_by(email='admin@pease-family.com').first()
    a = Album(family_id=admin.family_id, name='Family Album')
    db.session.add(a); db.session.commit()
    return a.id


def _login(app, email):
    c = app.test_client()
    c.post('/login', data={'email': email, 'password': 'Password1!'})
    return c


def test_member_sees_upload_form_on_album(app):
    with app.app_context():
        _member(app); aid = _album(app)
    html = _login(app, 'photomember@pease-family.com').get(f'/albums/{aid}').data.decode()
    assert 'Upload photos' in html


def test_member_upload_is_not_role_blocked(app):
    # A plain member reaches the upload route (paid seed family) instead of being
    # bounced by the old contributor/admin gate.
    with app.app_context():
        _member(app); aid = _album(app)
    r = _login(app, 'photomember@pease-family.com').post(
        f'/albums/{aid}/upload', data={}, follow_redirects=False)
    assert r.status_code == 302
    assert '/albums' in r.headers['Location']   # processed → back to album, not home/billing


def test_member_still_cannot_create_album(app):
    # Album creation remains a contributor/admin action.
    with app.app_context():
        _member(app)
    r = _login(app, 'photomember@pease-family.com').post(
        '/albums/add', data={'name': 'Sneaky Album'}, follow_redirects=False)
    with app.app_context():
        assert Album.query.filter_by(name='Sneaky Album').first() is None
