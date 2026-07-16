"""
The mobile API chat endpoints must honour the same 'chat' feature flag as the
web. They live outside the /chat prefix gate for the API, so they carry
`@requires_feature('chat')`. A build with chat cut must 404 every chat endpoint.

Also asserts the serialized user exposes `enabled_features`, which the iOS app
uses to build its tab bar so web and app stay in sync.
"""
import json


def _login(client):
    r = client.post('/api/v1/auth/login',
                    json={'email': 'admin@pease-family.com', 'password': 'Password1!'},
                    content_type='application/json')
    return json.loads(r.data)


def test_login_exposes_enabled_features(app, client):
    # conftest enables ALL features
    body = _login(client)
    feats = body['user']['enabled_features']
    assert isinstance(feats, list)
    assert 'chat' in feats
    assert 'events' in feats


def test_api_chat_reachable_when_chat_enabled(app, client):
    token = _login(client)['access_token']
    r = client.get('/api/v1/chat/messages', headers={'Authorization': f'Bearer {token}'})
    # 200 (paid) or 403 plan_required — either proves the feature gate passed.
    assert r.status_code in (200, 403)


def test_api_chat_endpoints_404_when_chat_disabled(app, client):
    token = _login(client)['access_token']
    app.config['ENABLED_FEATURES'] = {'events', 'members', 'activity'}  # chat cut
    hdr = {'Authorization': f'Bearer {token}'}
    for method, path in [
        ('get',    '/api/v1/chat/messages'),
        ('post',   '/api/v1/chat/messages'),
        ('patch',  '/api/v1/chat/messages/1'),
        ('delete', '/api/v1/chat/messages/1'),
    ]:
        r = getattr(client, method)(path, headers=hdr)
        assert r.status_code == 404, f'{method} {path} → {r.status_code}'
