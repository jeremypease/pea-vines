"""
Profile-photo focal point (Person.photo_position). The value is rendered into an
inline CSS `object-position` / `background-position`, so the save route must
validate it strictly (no CSS injection).
"""
from app import db
from app.models import User


def _me():
    return User.query.filter_by(email='admin@pease-family.com').first().person


def test_position_saves_valid(app, auth_client):
    with app.app_context():
        p = _me(); p.photo_path = 'photos/x.jpg'; db.session.commit()
    r = auth_client.post('/profile/photo/position', json={'position': '25% 70%'})
    assert r.status_code == 200 and r.get_json()['ok'] is True
    with app.app_context():
        assert _me().photo_position == '25% 70%'


def test_position_rejects_bad_values(app, auth_client):
    with app.app_context():
        p = _me(); p.photo_path = 'photos/x.jpg'; db.session.commit()
    for bad in ('red;}body{display:none', '50%', '50% 200%', '50%;70%',
                'center', '<script>', '50 % 70 %', ''):
        r = auth_client.post('/profile/photo/position', json={'position': bad})
        assert r.status_code == 400, bad
    with app.app_context():
        assert _me().photo_position != 'red;}body{display:none'


def test_position_requires_a_photo(app, auth_client):
    # admin person has no photo_path in the seed
    r = auth_client.post('/profile/photo/position', json={'position': '10% 10%'})
    assert r.status_code == 404


def test_position_applied_in_profile_markup(app, auth_client):
    with app.app_context():
        p = _me(); p.photo_path = 'photos/x.jpg'; p.photo_position = '20% 80%'; db.session.commit()
        pid = _me().id
    html = auth_client.get(f'/person/{pid}').data.decode()
    assert 'object-position: 20% 80%' in html
