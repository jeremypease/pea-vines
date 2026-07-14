"""
The local-dev filesystem store must never let a key or folder traverse outside
static/uploads/. `_local_upload_path` is the containment guard (CodeQL #11-16,
py/path-injection). Production uses R2 and never hits these paths, but the guard
keeps the sinks safe regardless of caller.
"""
import os
import pytest
from app import storage


def test_local_path_allows_normal_keys(app):
    with app.app_context():
        p = storage._local_upload_path('photos/abc123.jpg')
        root = os.path.realpath(os.path.join(app.root_path, 'static', 'uploads'))
        assert p.startswith(root + os.sep)
        assert p.endswith(os.path.join('photos', 'abc123.jpg'))


def test_local_path_neutralizes_traversal(app):
    """Traversal is stripped (secure_filename per segment); the resolved path
    can never escape the uploads root."""
    with app.app_context():
        root = os.path.realpath(os.path.join(app.root_path, 'static', 'uploads'))
        for evil in ('../../etc/passwd', 'photos/../../../../etc/passwd',
                     '/etc/passwd', '..', '....//....//etc/passwd'):
            p = storage._local_upload_path(evil)
            assert p == root or p.startswith(root + os.sep)


def test_get_object_bytes_cannot_escape_uploads(app):
    with app.app_context():
        # A crafted 'uploads/..' key is neutralised into the uploads dir, so it
        # can't read a file outside it — the neutralised path doesn't exist.
        with pytest.raises(OSError):
            storage.get_object_bytes('uploads/../../../../etc/passwd')


def test_delete_object_cannot_escape_uploads(app):
    with app.app_context():
        real_passwd = os.path.realpath('/etc/hosts')  # a real file outside uploads
        before = os.path.exists(real_passwd)
        # Neutralised to a non-existent path inside uploads → safe no-op.
        storage.delete_object('uploads/../../../../etc/hosts')
        assert os.path.exists(real_passwd) == before   # untouched


def test_raw_gif_upload_round_trips_locally(app):
    """The unprocessed branch (GIF) now writes via _store_upload; confirm the
    bytes land inside static/uploads/ and read back unchanged."""
    import io
    from werkzeug.datastructures import FileStorage
    # A minimal valid GIF89a header + payload.
    raw = b'GIF89a' + b'\x00' * 20
    with app.app_context():
        f = FileStorage(stream=io.BytesIO(raw), filename='clip.gif')
        key = storage.upload_photo(f, folder='photos')
        assert key and key.startswith('uploads/photos/')
        data, ctype = storage.get_object_bytes(key)
        assert data == raw
        assert ctype == 'image/gif'
        storage.delete_object(key)
