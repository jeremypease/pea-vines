"""
Bulk "sleeping rooms" parser (CodeQL #50). The trailing-capacity regex was
polynomial-backtracking (ReDoS) on user input; the rewrite is anchored/linear.
These lock the parsing behavior and guard against the regex regressing.
"""
import time
from datetime import date
from app import db
from app.models import User, Event, EventSleepingSpot


def _event(app):
    admin = User.query.filter_by(email='admin@pease-family.com').first()
    ev = Event(family_id=admin.family_id, name='Reunion',
               start_date=date(2026, 8, 1), has_sleeping=True)
    db.session.add(ev); db.session.commit()
    return ev.id


def test_bulk_rooms_parses_names_and_capacities(app, auth_client):
    with app.app_context():
        eid = _event(app)
    auth_client.post(f'/events/{eid}/sleeping/bulk-add',
                     data={'bulk_rooms': 'Master bedroom 2\nBunk room (4)\nCabin\nLoft [6]'},
                     follow_redirects=True)
    with app.app_context():
        spots = {s.name: s.capacity for s in EventSleepingSpot.query.filter_by(event_id=eid)}
    assert spots == {'Master bedroom': 2, 'Bunk room': 4, 'Cabin': None, 'Loft': 6}


def test_bulk_rooms_no_redos_on_adversarial_input(app, auth_client):
    with app.app_context():
        eid = _event(app)
    # The inputs that made the regexes backtrack: a long ambiguous line, and a
    # long run of digits (CodeQL's "many repetitions of '9'"). The linear scan
    # must handle both instantly.
    for evil in [('a ' * 5000).strip(), '9' * 8000, '(' * 8000 + '4)']:
        start = time.time()
        r = auth_client.post(f'/events/{eid}/sleeping/bulk-add',
                             data={'bulk_rooms': evil}, follow_redirects=False)
        elapsed = time.time() - start
        assert r.status_code == 302
        assert elapsed < 2.0, f'bulk-add took {elapsed:.1f}s — possible ReDoS regression'
