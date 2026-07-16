"""
Generic cartoon-animal avatars (Person.avatar_id): pickable when a member doesn't
upload a photo. A real photo always takes precedence.
"""
from app import db
from app.models import User


def _me():
    return User.query.filter_by(email='admin@pease-family.com').first().person


def test_set_valid_avatar(app, auth_client):
    r = auth_client.post('/profile/avatar', json={'avatar_id': 'fox'})
    assert r.status_code == 200 and r.get_json()['avatar_id'] == 'fox'
    with app.app_context():
        assert _me().avatar_id == 'fox'


def test_reject_invalid_avatar(app, auth_client):
    r = auth_client.post('/profile/avatar', json={'avatar_id': 'dragon'})
    assert r.status_code == 400
    with app.app_context():
        assert _me().avatar_id is None


def test_clear_avatar(app, auth_client):
    with app.app_context():
        _me().avatar_id = 'cat'; db.session.commit()
    r = auth_client.post('/profile/avatar', json={'avatar_id': ''})
    assert r.status_code == 200
    with app.app_context():
        assert _me().avatar_id is None


def test_avatar_rendered_when_no_photo(app, auth_client):
    with app.app_context():
        _me().avatar_id = 'owl'; db.session.commit()
        pid = _me().id
    html = auth_client.get(f'/person/{pid}').data.decode()
    assert 'assets/avatars/owl.svg' in html          # shown as the avatar
    assert 'id="avatarPicker"' in html                # picker offered on own profile


def test_photo_takes_precedence_over_avatar(app, auth_client):
    with app.app_context():
        p = _me(); p.avatar_id = 'owl'; p.photo_path = 'photos/x.jpg'; db.session.commit()
        pid = p.id
    html = auth_client.get(f'/person/{pid}').data.decode()
    assert 'assets/avatars/owl.svg' not in html       # photo wins everywhere
    assert 'id="profilePhotoImg"' in html


def test_every_catalog_avatar_has_an_svg(app):
    import os
    from app.avatars import ANIMAL_AVATARS
    root = os.path.join(app.root_path, 'static', 'assets', 'avatars')
    for aid, _ in ANIMAL_AVATARS:
        assert os.path.exists(os.path.join(root, f'{aid}.svg')), aid
