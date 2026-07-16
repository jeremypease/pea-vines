"""Cartoon-animal generic avatars a member can pick instead of uploading a photo.

Each id maps to a static SVG at `static/assets/avatars/<id>.svg`. The starter art
is intentionally simple and flat; design can swap the SVG files without touching
this list, and new options only need an entry here + a matching SVG.
"""

# (id, human label) — order is the order shown in the picker.
ANIMAL_AVATARS = [
    ('fox', 'Fox'),
    ('cat', 'Cat'),
    ('dog', 'Dog'),
    ('bear', 'Bear'),
    ('panda', 'Panda'),
    ('rabbit', 'Rabbit'),
    ('koala', 'Koala'),
    ('frog', 'Frog'),
    ('owl', 'Owl'),
    ('penguin', 'Penguin'),
]

AVATAR_IDS = {a[0] for a in ANIMAL_AVATARS}


def is_valid_avatar(avatar_id):
    return avatar_id in AVATAR_IDS


def avatar_static_file(avatar_id):
    """Static-relative path for use with url_for('static', filename=...)."""
    return f'assets/avatars/{avatar_id}.svg'
