"""Deterministic transport fixture, never a scientific researcher or default provider."""
import json
import os
import sys
import time
from pathlib import Path

for flag, stream in (('--flood-stdout', sys.stdout.buffer), ('--flood-stderr', sys.stderr.buffer)):
    if flag in sys.argv:
        stream.write(b'x' * (8 * 1024 * 1024))
        stream.flush()
        Path('fixture-output-finished').write_text('completed', encoding='utf-8')
        if flag == '--flood-stdout':
            raise SystemExit(0)

if '--nonzero' in sys.argv:
    sys.stderr.write('synthetic-private-diagnostic')
    raise SystemExit(7)

if '--invalid' in sys.argv:
    print('not an occurrence')
    raise SystemExit(0)
if '--slow' in sys.argv:
    time.sleep(0.4)
request = json.load(sys.stdin)
packet = request['contact']
memory = packet['basis']['competences']
event = {'schema': 'dnd.lab.occurrence.v1', 'event_id': packet['event_id'],
         'resultant': {'fixture': True, 'contacted_memory': len(memory),
                       'roundtrip_text': packet['basis']['intent'],
                       'secret_visible': 'LAB_TEST_SECRET' in os.environ},
         'memory_effect': 'NO_RESIDUE' if memory else {
             'action': 'RETAIN', 'knowledge': {'title': 'Fixture method',
             'method': 'Synthetic transport knowledge, not a cognitive discovery.'}}}
json.dump(event, sys.stdout)
