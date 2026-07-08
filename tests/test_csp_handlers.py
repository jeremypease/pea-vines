"""
CSP-safe event handling: the app carries a strict nonce CSP (no inline handler
allowance), so every interaction must use addEventListener / delegated
data-attributes rather than inline on*="" attributes.

NOTE: pytest can't execute the JS, so this proves *structure* (no inline
handlers, right data-attributes, pages render). Behavior needs a browser pass.
"""
import re
from app import db
from app.models import User, Person

INLINE = re.compile(r'\son(?:click|change|submit|input|load|error)=')


def _member(app):
    admin = User.query.filter_by(email='admin@pease-family.com').first()
    p = Person(name='Role X', family_id=admin.family_id)
    db.session.add(p); db.session.flush()
    u = User(family_id=admin.family_id, person_id=p.id, first_name='Role',
             last_name='X', email='rolex@pease-family.com', status='approved',
             email_verified=True, is_admin=False)
    u.set_password('Password1!')
    db.session.add(u); db.session.commit()
    return u.id


def test_key_pages_have_no_inline_handlers(app, auth_client):
    with app.app_context():
        _member(app)
    for path in ('/home', '/members', '/admin/users', '/notifications', '/profile'):
        html = auth_client.get(path).data.decode()
        m = INLINE.search(html)
        assert not m, f'{path} still has an inline handler near: {html[m.start()-10:m.start()+40]!r}'


def test_role_dropdown_uses_data_autosubmit(app, auth_client):
    with app.app_context():
        _member(app)
    html = auth_client.get('/admin/users').data.decode()
    assert 'data-autosubmit' in html and 'set-role' in html


def test_base_registers_delegators(app, auth_client):
    html = auth_client.get('/home').data.decode()
    assert 'data-action="toggle-notif"' in html            # notif bell converted
    assert "closest('[data-autosubmit]')" in html          # the change delegator is present


def test_csp_is_pure_nonce(app, client):
    csp = client.get('/login').headers.get('Content-Security-Policy', '')
    assert "'nonce-" in csp
    assert "script-src-attr 'unsafe-inline'" not in csp     # no inline-handler allowance
