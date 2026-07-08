"""
Role changes (Member ↔ Contributor ↔ Admin). The reported bug was that the
dropdown's auto-submit never fired because the CSP blocked inline event handlers;
the server route itself was fine. These lock both the CSP allowance and the route.
"""
from app import db
from app.models import User, Person


def _member(app, email='rolemember@pease-family.com'):
    admin = User.query.filter_by(email='admin@pease-family.com').first()
    p = Person(name='Role Member', family_id=admin.family_id)
    db.session.add(p); db.session.flush()
    u = User(family_id=admin.family_id, person_id=p.id, first_name='Role',
             last_name='Member', email=email, status='approved',
             email_verified=True, is_admin=False)
    u.set_password('Password1!')
    db.session.add(u); db.session.commit()
    return u.id


def test_csp_is_pure_nonce_no_inline_allowance(app, client):
    # The role dropdown auto-submits via data-autosubmit (delegated listener),
    # so the CSP needs no inline-handler allowance — it stays pure-nonce.
    csp = client.get('/login').headers.get('Content-Security-Policy', '')
    assert "'nonce-" in csp
    assert "script-src-attr 'unsafe-inline'" not in csp


def test_set_role_cycles_member_contributor_admin(app, auth_client):
    with app.app_context():
        uid = _member(app)

    auth_client.post(f'/admin/set-role/{uid}', data={'role': 'contributor'}, follow_redirects=True)
    with app.app_context():
        u = db.session.get(User, uid)
        assert u.is_delegate is True and u.is_admin is False

    auth_client.post(f'/admin/set-role/{uid}', data={'role': 'admin'}, follow_redirects=True)
    with app.app_context():
        u = db.session.get(User, uid)
        assert u.is_admin is True and u.is_delegate is False

    auth_client.post(f'/admin/set-role/{uid}', data={'role': ''}, follow_redirects=True)
    with app.app_context():
        u = db.session.get(User, uid)
        assert u.is_admin is False and u.is_delegate is False


def test_set_role_confirms_with_flash(app, auth_client):
    with app.app_context():
        uid = _member(app, 'rolemember2@pease-family.com')
    r = auth_client.post(f'/admin/set-role/{uid}', data={'role': 'contributor'}, follow_redirects=True)
    assert b'is now a contributor' in r.data
