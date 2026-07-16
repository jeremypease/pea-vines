"""
Adding a member with no birthday must work. The browser's <input type="date">
always submits birthday='' (empty string) when blank; WTForms DateField needs
Optional() or it fails to coerce '' and silently blocks the whole submit.
Regression for the "nothing happens when I leave the birthday blank" bug.
"""
from app.models import User, Person


def test_add_member_with_blank_birthday_creates_person(app, auth_client):
    r = auth_client.post('/admin/add-member', data={
        'first_name': 'Nobirth', 'last_name': 'Pease',
        'gender': 'Male', 'birthday': '',        # <-- empty string, like the browser sends
    }, follow_redirects=False)
    assert r.status_code == 302, 'submit should succeed and redirect, not re-render'
    with app.app_context():
        admin = User.query.filter_by(email='admin@pease-family.com').first()
        p = Person.query.filter_by(family_id=admin.family_id, name='Nobirth Pease').first()
        assert p is not None, 'member should be created even with no birthday'
        assert p.birthday is None


def test_add_member_with_birthday_still_works(app, auth_client):
    auth_client.post('/admin/add-member', data={
        'first_name': 'Hasbirth', 'last_name': 'Pease',
        'gender': 'Female', 'birthday': '1990-05-04',
    }, follow_redirects=False)
    with app.app_context():
        admin = User.query.filter_by(email='admin@pease-family.com').first()
        p = Person.query.filter_by(family_id=admin.family_id, name='Hasbirth Pease').first()
        assert p is not None and p.birthday is not None
        assert p.birthday.year == 1990
