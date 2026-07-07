"""
Display & accessibility preferences: a per-user larger-text / higher-contrast
setting that persists and drives <html data-text-size> / data-contrast so the
whole UI adapts for older family members.
"""
from app import db
from app.models import User


def test_display_settings_page_renders(app, auth_client):
    r = auth_client.get('/profile/display')
    assert r.status_code == 200
    html = r.data.decode()
    assert 'Text size' in html and 'Higher contrast' in html


def test_defaults_are_normal(app, auth_client):
    with app.app_context():
        u = User.query.filter_by(email='admin@pease-family.com').first()
        assert u.text_size == 'normal' and u.high_contrast is False
    # base template renders the default attribute, no data-contrast
    html = auth_client.get('/home').data.decode()
    assert 'data-text-size="normal"' in html
    assert 'data-contrast' not in html
    assert 'css/accessibility.css' in html   # the layer is loaded


def test_saving_prefs_persists_and_drives_html_attrs(app, auth_client):
    auth_client.post('/profile/display',
                     data={'text_size': 'x-large', 'high_contrast': 'on'},
                     follow_redirects=True)
    with app.app_context():
        u = User.query.filter_by(email='admin@pease-family.com').first()
        assert u.text_size == 'x-large' and u.high_contrast is True
    html = auth_client.get('/home').data.decode()
    assert 'data-text-size="x-large"' in html
    assert 'data-contrast="high"' in html


def test_unchecking_high_contrast_clears_it(app, auth_client):
    auth_client.post('/profile/display', data={'text_size': 'large', 'high_contrast': 'on'})
    auth_client.post('/profile/display', data={'text_size': 'large'})   # checkbox omitted
    with app.app_context():
        u = User.query.filter_by(email='admin@pease-family.com').first()
        assert u.high_contrast is False and u.text_size == 'large'


def test_invalid_text_size_falls_back_to_normal(app, auth_client):
    auth_client.post('/profile/display', data={'text_size': 'ENORMOUS'})
    with app.app_context():
        u = User.query.filter_by(email='admin@pease-family.com').first()
        assert u.text_size == 'normal'
