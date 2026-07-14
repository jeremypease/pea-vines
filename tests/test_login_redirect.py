"""
The post-login `?next=` redirect must only ever send the user to a local,
same-site path — never to an attacker-controlled external host (open redirect).
Guarded by `_safe_next` in app/routes/__init__.py (CodeQL #49).
"""
from app.routes import _safe_next


# ── unit: the guard itself ────────────────────────────────────────────────────

def test_safe_next_allows_local_paths():
    for good in ('/home', '/events/3', '/members?tab=all'):
        assert _safe_next(good) == good


def test_safe_next_rejects_external_and_tricks():
    for bad in (
        'https://evil.com/steal',      # absolute URL
        'http://evil.com',
        '//evil.com',                  # protocol-relative
        '/\\evil.com',                 # backslash → external host in browsers
        'javascript:alert(1)',         # scheme, not a path
        'evil.com',                    # no leading slash
        '',                            # empty
        None,
    ):
        assert _safe_next(bad) is None


# ── integration: the login route honours it ──────────────────────────────────

def test_login_ignores_external_next(app):
    client = app.test_client()
    rv = client.post('/login?next=https://evil.com/steal',
                     data={'email': 'admin@pease-family.com', 'password': 'Password1!'},
                     follow_redirects=False)
    assert rv.status_code == 302
    # Never redirect off-site; falls back to a local page.
    assert 'evil.com' not in rv.headers['Location']
    assert rv.headers['Location'].startswith('/') or '/home' in rv.headers['Location']


def test_login_honours_local_next(app):
    client = app.test_client()
    rv = client.post('/login?next=/members',
                     data={'email': 'admin@pease-family.com', 'password': 'Password1!'},
                     follow_redirects=False)
    assert rv.status_code == 302
    assert rv.headers['Location'].endswith('/members')
