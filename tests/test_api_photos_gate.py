"""
The mobile API photo endpoints must honour the same 'photos' feature flag as the
web. They live outside the /albums prefix, so the web `_gate_disabled_features`
hook doesn't cover them — they carry `@requires_feature('photos')` instead.
A build with photos cut must 404 every photo endpoint (read and write).
"""
import json


def _token(client):
    r = client.post('/api/v1/auth/login',
                    json={'email': 'admin@pease-family.com', 'password': 'Password1!'},
                    content_type='application/json')
    return json.loads(r.data)['access_token']


def test_api_albums_reachable_when_photos_enabled(app, client):
    # conftest enables ALL features
    token = _token(client)
    r = client.get('/api/v1/albums', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert 'albums' in json.loads(r.data)


def test_api_photo_endpoints_404_when_photos_disabled(app, client):
    token = _token(client)
    app.config['ENABLED_FEATURES'] = {'events', 'members', 'activity'}  # photos cut
    hdr = {'Authorization': f'Bearer {token}'}
    for method, path in [
        ('get',  '/api/v1/albums'),
        ('get',  '/api/v1/albums/1'),
        ('get',  '/api/v1/albums/1/photos'),
        ('post', '/api/v1/albums/1/photos'),
        ('get',  '/api/v1/photos/1'),
    ]:
        r = getattr(client, method)(path, headers=hdr)
        assert r.status_code == 404, f'{method} {path} → {r.status_code}'
