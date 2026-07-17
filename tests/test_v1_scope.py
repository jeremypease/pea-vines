"""
v1 scope decisions (founders' call):
- chat is live by default; general photos stay cut
- event meal-planning + sleeping are cut from the event UI, gated behind
  EVENT_EXTRAS so they stay dormant/reversible. Assignments + carpool stay.
"""


def test_chat_live_general_photos_cut_by_default():
    from app.features import DEFAULT_FEATURES
    assert 'chat' in DEFAULT_FEATURES
    assert 'photos' not in DEFAULT_FEATURES


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
