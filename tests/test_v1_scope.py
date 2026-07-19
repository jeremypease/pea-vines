"""
v1 scope decisions (founders' call):
- chat is live by default; photos are live but event-scoped (no general albums)
- event meal-planning + sleeping are cut from the event UI, gated behind
  EVENT_EXTRAS so they stay dormant/reversible. Assignments + carpool stay.
"""


def test_chat_and_photos_live_by_default():
    from app.features import DEFAULT_FEATURES
    assert 'chat' in DEFAULT_FEATURES
    assert 'photos' in DEFAULT_FEATURES


def test_event_extras_hidden_by_default(app, auth_client):
    html = auth_client.get('/events/add').data.decode()
    assert "Sign-up sheet for who's bringing what" not in html   # meals toggle gone
    assert 'Rooms and spots assigned by admin' not in html       # sleeping toggle gone
    assert 'Task list members can claim' in html                 # assignments kept
    assert 'Coordinate rides to the event' in html               # carpool kept


def test_event_extras_return_when_flag_on(app, auth_client):
    app.config['EVENT_EXTRAS'] = True
    html = auth_client.get('/events/add').data.decode()
    assert "Sign-up sheet for who's bringing what" in html
    assert 'Rooms and spots assigned by admin' in html


# ── photos: event-scoped only (D1) ─────────────────────────────────────────────

def test_no_photos_nav_item(app, auth_client):
    """The sidebar nav has no Photos item (event-scoped photos have no general
    hub to link to). Scoped to the <nav> block itself — the home page's own
    "Photos" card (a different, still-valid feature) shouldn't false-positive
    this check."""
    html = auth_client.get('/home').data.decode()
    nav = html[html.index('<nav class="nav">'):html.index('</nav>')]
    assert '>Photos<' not in nav
    assert 'href="/albums"' not in nav


def test_album_without_event_is_rejected(app, auth_client):
    r = auth_client.post('/albums/add', data={'name': 'General Album'},   # no event_id
                         follow_redirects=False)
    assert r.status_code == 302
    with app.app_context():
        from app.models import Album
        assert Album.query.filter_by(name='General Album').count() == 0


def test_album_with_event_is_created(app, auth_client, seeded_event_id):
    r = auth_client.post('/albums/add', data={'name': 'Reunion Pics', 'event_id': seeded_event_id},
                         follow_redirects=False)
    assert r.status_code == 302
    with app.app_context():
        from app.models import Album
        album = Album.query.filter_by(name='Reunion Pics').first()
        assert album is not None and album.event_id == seeded_event_id


def test_albums_hub_offers_no_general_option_when_events_exist(app, auth_client, seeded_event_id):
    html = auth_client.get('/albums').data.decode()
    assert '-- None --' not in html
