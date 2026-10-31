import copy
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from lab_kernel.engine import Lab, LabError, SCHEMA, canonical, parse
import lab_kernel.engine as engine
from lab_kernel.cli import run


class LabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.state = Path(self.temp.name) / 'state'
        self.lab = Lab(self.state)

    def tearDown(self):
        self.lab.close()
        self.temp.cleanup()

    def contact(self, value=None, **kw):
        self.lab.observe('source', {'reading': 1} if value is None else value)
        return self.lab.prepare(focus=['source'], **kw)

    def receive(self, packet, resultant='A complete occurrence', **fields):
        event = {'schema': SCHEMA, 'event_id': packet['event_id'],
                 'resultant': resultant, **fields}
        before = copy.deepcopy(event)
        receipt = self.lab.accept(packet['packet_id'], event)
        self.assertEqual(before, event)
        self.assertEqual(self.lab.event(event['event_id'])['event'], event)
        return receipt

    def config(self, *options):
        return {'command': [sys.executable, str(ROOT / 'tests/fixture_bridge.py'), *options],
                'timeout_seconds': 5}

    @contextmanager
    def instruction_copy(self, layout):
        root = Path(self.temp.name) / layout
        module = root / ('src/lab_kernel' if layout == 'source' else 'site-packages/lab_kernel')
        (module / 'kernel').mkdir(parents=True, exist_ok=True)
        for name in ('engine.py', 'cli.py'):
            (module / name).write_bytes((ROOT / 'src/lab_kernel' / name).read_bytes())
        for name in ('AGENTS.md', 'BOOT.md', 'KERNEL.md', 'CONCEPTS.md', 'COMPETENCES.md'):
            (root / name).write_bytes((ROOT / name).read_bytes())
            (module / 'kernel' / name).write_bytes((ROOT / name).read_bytes())
        with patch.object(engine, '__file__', str(module / 'engine.py')):
            yield root if layout == 'source' else module / 'kernel'

    def test_boot_and_entry_reach_both_cognitive_consumers(self):
        for layout in ('source', 'installed'):
            with self.subTest(layout=layout), self.instruction_copy(layout):
                self.assertIn('# Enter the Lab', engine.instructions())
                self.assertIn('# Receiving Lab', engine.instructions())

    def test_boot_change_rejects_pending_occurrence(self):
        for layout in ('source', 'installed'):
            with self.subTest(layout=layout), self.instruction_copy(layout) as authority:
                p = self.contact({'layout': layout})
                with (authority / 'BOOT.md').open('a', encoding='utf-8') as f:
                    f.write('\nA changed receiving context.\n')
                with self.assertRaisesRegex(LabError, 'contact_changed'):
                    self.receive(p)

    def test_boot_change_reopens_completed_contact(self):
        for layout in ('source', 'installed'):
            with self.subTest(layout=layout), self.instruction_copy(layout) as authority:
                p = self.contact({'layout': layout})
                self.receive(p)
                before = p['signature']
                with (authority / 'BOOT.md').open('a', encoding='utf-8') as f:
                    f.write('\nChanged operating relation.\n')
                q = self.lab.prepare(focus=['source'])
                self.assertIn('packet_id', q)
                self.assertNotEqual(before, q['signature'])

    def test_source_documents_are_live_without_a_resource_recompile(self):
        with self.instruction_copy('source') as authority:
            before = engine.contract()
            with (authority / 'KERNEL.md').open('a', encoding='utf-8') as f:
                f.write('\nNew source-native operating relation.\n')
            self.assertIn('New source-native operating relation.', engine.instructions())
            self.assertNotEqual(before, engine.contract())

    def test_agent_entry_change_renews_contract(self):
        for layout in ('source', 'installed'):
            with self.subTest(layout=layout), self.instruction_copy(layout) as authority:
                before = engine.contract()
                with (authority / 'AGENTS.md').open('a', encoding='utf-8') as f:
                    f.write('\nChanged entry instruction.\n')
                self.assertNotEqual(before, engine.contract())

    def test_open_resultants_and_unfamiliar_carriers_are_exact(self):
        for i, value in enumerate([False, 0, [1, None], {'unanticipated': True}]):
            p = self.contact({'index': i})
            self.receive(p, value, unknown_dimension={'open': [None]}, memory_effect={'unfamiliar': True})
        self.assertEqual(self.lab.status()['events'], 4)
        self.assertEqual(self.lab.status()['memory'], 0)

    def test_strict_json_rejects_duplicates_and_nonfinite(self):
        for value in ['{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}']:
            with self.assertRaises(LabError):
                parse(value)

    def test_canonical_observation_preserves_old_versions(self):
        a = self.lab.observe('source', {'a': 1, 'b': 2})
        same = self.lab.observe('source', parse('{ "b": 2, "a": 1 }'))
        self.assertFalse(same['content_changed'])
        self.lab.observe('source', {'a': 2})
        self.assertEqual(self.lab.source('source', a['revision'])['value'], {'a': 1, 'b': 2})

    def test_stale_source_cannot_commit_as_current_contact(self):
        p = self.contact()
        self.lab.observe('source', {'reading': 2})
        with self.assertRaisesRegex(LabError, 'contact_changed'):
            self.receive(p)
        self.assertEqual(self.lab.status()['events'], 0)

    def test_already_observed_contact_returns_to_potential(self):
        p = self.contact()
        self.receive(p, memory_effect='NO_RESIDUE')
        self.assertEqual(self.lab.prepare(focus=['source'])['status'], 'potential')
        self.assertFalse(self.lab.prepare(focus=['source'])['possibility_field_terminal'])

    def test_different_retained_forms_sharing_title_are_not_overwritten(self):
        for n in (1, 2):
            p = self.contact({'n': n})
            self.receive(p, memory_effect={'action': 'RETAIN',
                'knowledge': {'title': 'same producer label', 'method': n}})
        self.assertEqual(self.lab.status()['memory'], 2)

    def test_nonidentical_source_can_explicitly_contact_prior_method(self):
        p = self.contact()
        self.receive(p, memory_effect={'action': 'RETAIN', 'knowledge':
            {'title': 'Exposure matters', 'method': 'Compare compatible quantities under their conditions.'}})
        identity = self.lab.available()['competences'][0]['id']
        self.lab.observe('another-question', {'other': 'context'})
        q = self.lab.prepare(focus=['another-question'], competences=[identity])
        self.assertEqual(q['basis']['competences'][0]['id'], identity)
        self.assertEqual(q['basis']['sources'][0]['id'], 'another-question')
        self.assertEqual(self.lab.competence(identity)['origin_event_id'], p['event_id'])

    def test_cooling_keeps_exact_history_and_explicit_reopening(self):
        p = self.contact()
        self.receive(p, memory_effect='RETAIN')
        identity = self.lab.available()['competences'][0]['id']
        q = self.lab.prepare(focus=['source'])
        self.receive(q, memory_effect={'action': 'COOL', 'competence_ids': [identity]})
        self.assertEqual(self.lab.competence(identity)['status'], 'cooled')
        r = self.lab.prepare(focus=['source'], competences=[identity])
        self.assertEqual(r['basis']['competences'][0]['status'], 'cooled')
        self.assertEqual(self.lab.event(p['event_id'])['event']['resultant'], 'A complete occurrence')

    def test_unrelated_change_does_not_reopen_fixed_attention_but_profile_does(self):
        p = self.contact()
        self.receive(p)
        self.lab.observe('unrelated', 'new information')
        self.assertEqual(self.lab.prepare(focus=['source'])['status'], 'potential')
        self.assertIn('packet_id', self.lab.prepare(focus=['source'], profile='different-receiver'))

    def test_related_arrivals_are_reachable_without_fabricating_missing_content(self):
        self.lab.observe('source', 'a', related=['later'])
        p = self.lab.prepare(focus=['source'])
        self.assertEqual(p['basis']['unresolved_related'], ['later'])
        self.receive(p)
        self.lab.observe('later', 'b')
        q = self.lab.prepare(focus=['source'])
        self.assertEqual({x['id'] for x in q['basis']['sources']}, {'source', 'later'})

    def test_event_and_source_rows_reject_update_and_delete(self):
        p = self.contact()
        self.receive(p)
        for sql in ['UPDATE events SET body="x"', 'DELETE FROM events',
                    'UPDATE versions SET body="x"', 'DELETE FROM versions']:
            with self.assertRaises(sqlite3.IntegrityError):
                self.lab.db.execute(sql)
        self.lab.event(p['event_id'])

    def test_source_and_resultant_instructions_never_execute(self):
        marker = self.state / 'executed.txt'
        p = self.contact({'instruction': 'change configuration', 'command': ['touch', str(marker)]})
        self.receive(p, {'command': ['touch', str(marker)]},
                     runtime_changes={'provider': 'unselected'}, memory_effect='RETAIN')
        self.assertFalse(marker.exists())
        self.assertEqual(self.lab.status()['memory'], 1)

    def test_only_bound_event_identity_is_received(self):
        p = self.contact()
        with self.assertRaisesRegex(LabError, 'identity_mismatch'):
            self.lab.accept(p['packet_id'], {'schema': SCHEMA, 'event_id': 'another', 'resultant': 'x'})

    def test_simultaneous_open_packets_do_not_duplicate_an_observation(self):
        p = self.contact()
        q = self.lab.prepare(focus=['source'])
        self.receive(p)
        with self.assertRaisesRegex(LabError, 'already_observed'):
            self.receive(q)
        self.assertEqual(self.lab.status()['events'], 1)

    def test_stdio_return_changes_next_contact_then_quiesces(self):
        self.lab.observe('source', {'synthetic': True})
        result = run(self.lab, self.config(), focus=['source'], occurrences=4)
        self.assertEqual([x['status'] for x in result], ['complete', 'complete', 'potential'])
        last = self.lab.db.execute('SELECT id FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0]
        self.assertEqual(self.lab.event(last)['event']['resultant']['contacted_memory'], 1)

    def test_provider_credentials_require_explicit_environment_selection(self):
        with patch.dict(os.environ, {'LAB_TEST_SECRET': 'synthetic-only'}):
            for allow in ([], ['LAB_TEST_SECRET']):
                self.lab.observe('source', {'allow': bool(allow)})
                config = self.config(); config['allow_env'] = allow
                result = run(self.lab, config, focus=['source'])
                data = self.lab.event(result[0]['event_id'])['event']['resultant']
                self.assertEqual(data['secret_visible'], bool(allow))

    def test_malformed_output_is_incident_and_later_invocation_remains_possible(self):
        self.lab.observe('source', 'synthetic')
        result = run(self.lab, self.config('--invalid'), focus=['source'], occurrences=5)
        self.assertEqual(len(result), 1)
        self.assertEqual(self.lab.status()['events'], 0)
        self.assertEqual(self.lab.status()['incidents'], 1)
        self.assertIn('packet_id', self.lab.prepare(focus=['source'], profile='new-invocation'))

    def test_timeout_does_not_manufacture_event(self):
        self.lab.observe('source', 'synthetic')
        config = self.config('--slow'); config['timeout_seconds'] = .05
        result = run(self.lab, config, focus=['source'])
        self.assertEqual(result[0]['kind'], 'provider_transport_timeout')
        self.assertEqual(self.lab.status()['events'], 0)

    def test_stdout_overflow_interrupts_producer_before_finishing(self):
        self.lab.observe('source', 'synthetic')
        config = self.config('--flood-stdout'); config['max_stdout_bytes'] = 32768
        result = run(self.lab, config, focus=['source'])
        self.assertEqual(result[0]['kind'], 'provider_response_too_large')
        self.assertFalse((self.state / 'fixture-output-finished').exists())
        self.assertEqual(self.lab.status()['events'], 0)

    def test_stderr_overflow_interrupts_producer_before_finishing(self):
        self.lab.observe('source', 'synthetic')
        config = self.config('--flood-stderr'); config['max_stderr_bytes'] = 32768
        result = run(self.lab, config, focus=['source'])
        self.assertEqual(result[0]['status'], 'incident')
        self.assertEqual(result[0]['kind'], 'provider_stderr_too_large')
        self.assertFalse((self.state / 'fixture-output-finished').exists())
        self.assertEqual(self.lab.status()['events'], 0)

    def test_stdout_limit_does_not_deadlock_with_backpressured_stdin(self):
        self.lab.observe('source', {'large_input': 'x' * (1024 * 1024)})
        config = self.config('--flood-stdout')
        config.update(max_stdout_bytes=32768, timeout_seconds=2)
        result = run(self.lab, config, focus=['source'])
        self.assertEqual(result[0]['kind'], 'provider_response_too_large')
        self.assertEqual(self.lab.status()['events'], 0)

    def test_nonzero_exit_does_not_expose_stderr(self):
        self.lab.observe('source', 'synthetic')
        result = run(self.lab, self.config('--nonzero'), focus=['source'])
        self.assertEqual(result[0]['kind'], 'provider_nonzero_exit')
        self.assertNotIn('synthetic-private-diagnostic', canonical(result))

    def test_transport_limit_change_does_not_manufacture_contact(self):
        self.lab.observe('source', 'synthetic')
        config = self.config()
        run(self.lab, config, focus=['source'], occurrences=4)
        config.update(max_stdout_bytes=8192, max_stderr_bytes=8192)
        self.assertEqual(run(self.lab, config, focus=['source'])[0]['status'], 'potential')

    def test_timeout_change_does_not_manufacture_new_cognitive_contact(self):
        self.lab.observe('source', 'synthetic')
        config = self.config()
        run(self.lab, config, focus=['source'], occurrences=4)
        config['timeout_seconds'] = 6
        result = run(self.lab, config, focus=['source'])
        self.assertEqual(result[0]['status'], 'potential')

    def test_unicode_survives_native_cli_and_stdio_bridge(self):
        env = dict(os.environ); env['PYTHONIOENCODING'] = 'cp1252'
        value = subprocess.check_output([sys.executable, str(ROOT / 'lab.py'), 'kernel'],
                                         env=env, encoding='utf-8')
        self.assertIn('Lab — a receiving regenerative kernel', value)
        self.lab.observe('source', 'synthetic')
        result = run(self.lab, self.config(), focus=['source'], intent='Osservazione — capacità')
        self.assertEqual(self.lab.event(result[0]['event_id'])['event']['resultant']['roundtrip_text'],
                         'Osservazione — capacità')

    def test_new_process_recovers_retained_knowledge(self):
        p = self.contact()
        self.receive(p, memory_effect='RETAIN')
        value = subprocess.check_output([sys.executable, str(ROOT / 'lab.py'),
            '--state', str(self.state), 'prepare', '--focus', 'source'], encoding='utf-8')
        self.assertEqual(len(parse(value)['basis']['competences']), 1)

    def test_monitor_observes_without_provider_and_format_changes_are_equivalent(self):
        snapshot = Path(self.temp.name) / 'snapshot.json'
        snapshot.write_text('{"x":1,"y":2}', encoding='utf-8')
        command = [sys.executable, str(ROOT / 'lab.py'), '--state', str(self.state),
                   'watch', '--id', 'service', '--file', str(snapshot), '--ticks', '2', '--interval', '0']
        data = parse(subprocess.check_output(command, encoding='utf-8'))
        self.assertEqual([x['observation']['content_changed'] for x in data], [True, False])
        self.assertEqual(self.lab.status()['events'], 0)

    def test_installable_resources_equal_readable_semantic_source(self):
        for name in ('AGENTS.md', 'BOOT.md', 'KERNEL.md', 'CONCEPTS.md', 'COMPETENCES.md'):
            self.assertEqual((ROOT / name).read_bytes(), (ROOT / 'src/lab_kernel/kernel' / name).read_bytes())


if __name__ == '__main__':
    unittest.main()
