"""
MVP feature gate (app/features.py): hidden features vanish from the nav and 404
at the route layer, while the live set stays reachable — and re-enabling one is a
single config change. (conftest enables ALL features for the rest of the suite;
these tests set the MVP subset explicitly.)
"""
import pytest
from datetime import date, datetime
from app import db
from app.models import User, Announcement, Event

MVP = {'activity', 'events', 'members'}


def _mvp(app):
    app.config['ENABLED_FEATURES'] = set(MVP)


def test_live_features_reachable(app, auth_client):
    _mvp(app)
    for path in ('/activity', '/events', '/members'):
        assert auth_client.get(path).status_code == 200, path


@pytest.mark.parametrize('path', ['/albums', '/chat', '/polls', '/announcements', '/messages',
                                  '/registries', '/stories', '/cards', '/documents', '/timeline'])
def test_hidden_features_404(app, auth_client, path):
    _mvp(app)
    assert auth_client.get(path).status_code == 404


def test_nav_shows_only_live_features(app, auth_client):
    _mvp(app)
    html = auth_client.get('/home').data.decode()
    for live in ('/activity', '/events', '/members'):
        assert f'href="{live}"' in html, live
    for hidden in ('/albums', '/announcements', '/messages', '/registries'):
        assert f'href="{hidden}"' not in html, hidden


def test_reenabling_a_feature_is_one_config_change(app, auth_client):
    _mvp(app)
    assert auth_client.get('/polls').status_code == 404
    app.config['ENABLED_FEATURES'] = MVP | {'polls'}
    assert auth_client.get('/polls').status_code == 200


def test_photos_disabled_leaves_no_album_links(app, auth_client, seeded_event_id):
    """With photos cut, no page may render a link/form into /albums (which 404s),
    and the photo write routes are gone."""
    _mvp(app)  # photos not in the live set
    for path in ('/home', f'/events/{seeded_event_id}', '/search?q=a'):
        html = auth_client.get(path).data.decode()
        assert 'href="/albums' not in html, path
        assert 'action="/albums' not in html, path
        assert '/photos/upload' not in html, path
    # write routes reachable only via the feature are blocked
    assert auth_client.post(f'/events/{seeded_event_id}/photos/upload').status_code == 404


def test_activity_feed_only_shows_live_sources(app, auth_client):
    _mvp(app)
    with app.app_context():
        admin = User.query.filter_by(email='admin@pease-family.com').first()
        db.session.add(Announcement(family_id=admin.family_id, title='Hidden News', body='x',
                                    author_id=admin.person_id, created_at=datetime(2026, 6, 1, 12)))
        db.session.add(Event(family_id=admin.family_id, name='Live Event',
                             start_date=date(2026, 8, 1), created_at=datetime(2026, 6, 1, 13)))
        db.session.commit()
    html = auth_client.get('/activity').data.decode()
    assert 'Live Event' in html        # events source is live
    assert 'Hidden News' not in html    # announcements source is gated out
