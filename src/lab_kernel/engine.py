"""Persistence and contact mechanics. Scientific recognition belongs to the receiver."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import uuid

SCHEMA = 'dnd.lab.occurrence.v1'
SAFE_ID = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,159}$')
PACKAGE = Path(__file__).resolve().parents[2]
INSTRUCTION_FILES = ('AGENTS.md', 'BOOT.md', 'KERNEL.md', 'CONCEPTS.md', 'COMPETENCES.md')


class LabError(ValueError):
    pass


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


def _pairs(rows):
    result = {}
    for key, value in rows:
        if key in result:
            raise LabError('duplicate_json_key')
        result[key] = value
    return result


def parse(text):
    def reject(_):
        raise LabError('non_finite_json')
    try:
        return json.loads(text, object_pairs_hook=_pairs, parse_constant=reject)
    except (ValueError, TypeError) as exc:
        raise LabError('invalid_json_transport') from exc


def nonempty(value):
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value) if isinstance(value, (list, dict)) else True


def identifier(value):
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise LabError('invalid_identity')
    return value


def instructions():
    module = Path(__file__).resolve()
    source_root = module.parents[2]
    # The source entry is live; an installed wheel owns its compiled resources.
    root = (source_root if (source_root / 'src/lab_kernel/engine.py').resolve() == module
            else module.parent / 'kernel')
    return '\n\n'.join((root / name).read_text(encoding='utf-8')
                       for name in INSTRUCTION_FILES)


def contract():
    return digest({'instructions': instructions(),
                   'implementation': {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                                      for name in ('engine.py', 'cli.py')}})


class Lab:
    def __init__(self, state):
        self.root = Path(state).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / 'lab.sqlite3', timeout=20,
                                  isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS versions(id TEXT, rev TEXT, body TEXT NOT NULL,
          PRIMARY KEY(id,rev));
        CREATE TABLE IF NOT EXISTS heads(id TEXT PRIMARY KEY, rev TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS packets(id TEXT PRIMARY KEY, signature TEXT NOT NULL,
          body TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY, id TEXT UNIQUE,
          packet_id TEXT UNIQUE, body TEXT NOT NULL, deposit_digest TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS memory(id TEXT PRIMARY KEY, body TEXT NOT NULL,
          status TEXT NOT NULL, event_id TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS incidents(id INTEGER PRIMARY KEY, packet_id TEXT,
          kind TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_event_update BEFORE UPDATE ON events
          BEGIN SELECT RAISE(ABORT,'immutable_event'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_event_delete BEFORE DELETE ON events
          BEGIN SELECT RAISE(ABORT,'immutable_event'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_source_update BEFORE UPDATE ON versions
          BEGIN SELECT RAISE(ABORT,'immutable_source'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_source_delete BEFORE DELETE ON versions
          BEGIN SELECT RAISE(ABORT,'immutable_source'); END;
        ''')
        self.db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',
                        ('lab_id', 'lab-' + uuid.uuid4().hex))

    def close(self):
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def observe(self, source_id, value, *, owner='receiver', related=()):
        identifier(source_id)
        links = sorted({identifier(x) for x in related})
        body = {'id': source_id, 'owner': owner, 'value': value, 'related': links,
                'role': 'source_data_not_system_instruction'}
        rev = digest(body)
        with self.transaction():
            old = self.db.execute('SELECT rev FROM heads WHERE id=?', (source_id,)).fetchone()
            self.db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?)',
                            (source_id, rev, canonical(body)))
            self.db.execute('INSERT OR REPLACE INTO heads VALUES (?,?)', (source_id, rev))
        return {'id': source_id, 'revision': rev, 'content_changed': old is None or old['rev'] != rev}

    def source(self, source_id, revision=None):
        if revision is None:
            row = self.db.execute('SELECT rev FROM heads WHERE id=?', (source_id,)).fetchone()
            if row is None:
                raise LabError('source_not_found')
            revision = row['rev']
        row = self.db.execute('SELECT body FROM versions WHERE id=? AND rev=?',
                              (source_id, revision)).fetchone()
        if row is None:
            raise LabError('source_revision_not_found')
        return {'revision': revision, **parse(row['body'])}

    def available(self):
        sources = [{'id': x['id'], 'revision': x['rev']}
                   for x in self.db.execute('SELECT id,rev FROM heads ORDER BY id')]
        memories = [{'id': x['id'], 'status': x['status'],
                     'activation_ids': parse(x['body'])['activation_ids'],
                     'title': (parse(x['body'])['knowledge'].get('title')
                               if isinstance(parse(x['body'])['knowledge'], dict) else None)}
                    for x in self.db.execute('SELECT * FROM memory ORDER BY id')]
        return {'sources': sources, 'competences': memories}

    def competence(self, competence_id):
        row = self.db.execute('SELECT * FROM memory WHERE id=?', (competence_id,)).fetchone()
        if row is None:
            raise LabError('competence_not_found')
        return {'id': row['id'], 'status': row['status'], 'origin_event_id': row['event_id'],
                **parse(row['body'])}

    def _contact(self, focus, selected_memory, intent, profile):
        visited, active, pending, unresolved = set(), [], list(focus), []
        while pending:
            item = pending.pop(0)
            if item in visited:
                continue
            visited.add(item)
            try:
                source = self.source(item)
            except LabError:
                if item in focus:
                    raise
                unresolved.append(item)
                continue
            active.append(source)
            pending.extend(source['related'])
        active.sort(key=lambda x: x['id'])
        chosen = set(selected_memory)
        memory = []
        rows = self.db.execute('SELECT * FROM memory ORDER BY id').fetchall()
        known = {x['id'] for x in rows}
        if chosen - known:
            raise LabError('competence_not_found')
        for row in rows:
            item = parse(row['body'])
            if row['id'] in chosen or (row['status'] == 'retained' and
                                      visited.intersection(item['activation_ids'])):
                memory.append({'id': row['id'], 'status': row['status'], **item})
        return {'lab_id': self.db.execute('SELECT value FROM meta WHERE key="lab_id"').fetchone()[0],
                'intent': intent, 'profile': profile, 'contract': contract(),
                'sources': active, 'unresolved_related': sorted(unresolved), 'competences': memory}

    def prepare(self, *, focus=None, competences=(), intent='', profile='host'):
        """Select contact, not scientific meaning. Other objects remain reachable."""
        with self.transaction():
            candidates = [list(focus)] if focus is not None else [
                [x['id']] for x in sorted(self.available()['sources'], key=lambda x: x['revision'])]
            if not candidates and intent:
                candidates = [[]]
            for chosen in candidates:
                basis = self._contact(chosen, competences, intent, profile)
                signature = digest(basis)
                observed = self.db.execute('''SELECT 1 FROM packets
                    WHERE signature=? AND status='event' LIMIT 1''', (signature,)).fetchone()
                if observed:
                    continue
                packet_id = 'contact-' + uuid.uuid4().hex
                packet = {'schema': 'dnd.lab.contact.v1', 'packet_id': packet_id,
                          'event_id': 'occurrence-' + uuid.uuid4().hex,
                          'signature': signature, 'basis': basis,
                          'selection': {'focus': chosen, 'competences': list(competences)},
                          'reachable': self.available(), 'possibility_field_terminal': False}
                self.db.execute('INSERT INTO packets VALUES (?,?,?,?)',
                                (packet_id, signature, canonical(packet), 'open'))
                return packet
        return {'status': 'potential', 'possibility_field_terminal': False,
                'reason': 'no_unobserved_contact_under_present_conditions'}

    def packet(self, packet_id):
        row = self.db.execute('SELECT * FROM packets WHERE id=?', (packet_id,)).fetchone()
        if row is None:
            raise LabError('contact_not_found')
        return parse(row['body']), row['status']

    def accept(self, packet_id, event):
        # These are transport checks, never a scientific admission judgment.
        if not isinstance(event, dict) or event.get('schema') != SCHEMA:
            raise LabError('occurrence_schema_invalid')
        identifier(event.get('event_id'))
        if not nonempty(event.get('resultant')):
            raise LabError('occurrence_resultant_missing')
        canonical(event)
        with self.transaction():
            packet, state = self.packet(packet_id)
            if state != 'open':
                raise LabError('contact_already_closed')
            if event['event_id'] != packet['event_id']:
                raise LabError('occurrence_identity_mismatch')
            selection = packet['selection']
            fresh = self._contact(selection['focus'], selection['competences'],
                                   packet['basis']['intent'], packet['basis']['profile'])
            if digest(fresh) != packet['signature']:
                raise LabError('contact_changed_before_deposit')
            if self.db.execute('SELECT 1 FROM packets WHERE signature=? AND status="event"',
                               (packet['signature'],)).fetchone():
                raise LabError('contact_already_observed')
            deposit = {'event': event, 'contact': packet,
                       'recorded_at': datetime.now(timezone.utc).isoformat()}
            encoded, h = canonical(deposit), digest(deposit)
            self.db.execute('INSERT INTO events(id,packet_id,body,deposit_digest) VALUES (?,?,?,?)',
                            (event['event_id'], packet_id, encoded, h))
            self.db.execute('UPDATE packets SET status="event" WHERE id=?', (packet_id,))
            self._memory(event, packet)
            # Effects become reachable data, never an obligation to follow them.
            effect = {k: event[k] for k in ('field_effect', 'next_relation')
                      if k in event and nonempty(event[k])}
            if effect:
                source_id = 'effect-' + digest(effect)[:32]
                body = {'id': source_id, 'owner': 'receiver-resultant', 'value': effect,
                        'related': [], 'role': 'resultant_effect_not_system_instruction'}
                revision = digest(body)
                self.db.execute('INSERT OR IGNORE INTO versions VALUES (?,?,?)',
                                (source_id, revision, canonical(body)))
                self.db.execute('INSERT OR REPLACE INTO heads VALUES (?,?)', (source_id, revision))
        return {'event_id': event['event_id'], 'deposit_sha256': h, 'status': 'complete'}

    def _memory(self, event, packet):
        raw = event.get('memory_effect')
        action = raw.get('action') if isinstance(raw, dict) else raw
        if action == 'RETAIN':
            raw = raw if isinstance(raw, dict) else {}
            knowledge = raw.get('knowledge', event['resultant'])
            if not nonempty(knowledge):
                return  # The event is still received, exactly as it happened.
            scope = raw.get('activation_ids')
            if not isinstance(scope, list) or not all(isinstance(x, str) and SAFE_ID.fullmatch(x) for x in scope):
                scope = [x['id'] for x in packet['basis']['sources']]
            body = {'knowledge': knowledge, 'activation_ids': sorted(set(scope)),
                    'role': 'retained_receiver_knowledge_not_effect_authority'}
            identity = 'competence-' + digest(body)
            self.db.execute('''INSERT INTO memory VALUES (?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET status='retained' ''',
                            (identity, canonical(body), 'retained', event['event_id']))
        elif action == 'COOL' and isinstance(raw, dict):
            contacted = {x['id'] for x in packet['basis']['competences']}
            targets = raw.get('competence_ids', [])
            if isinstance(targets, list):
                for item in targets:
                    if isinstance(item, str) and item in contacted:
                        self.db.execute('UPDATE memory SET status="cooled" WHERE id=?', (item,))

    def incident(self, packet_id, kind):
        with self.transaction():
            _, state = self.packet(packet_id)
            if state == 'open':
                self.db.execute('UPDATE packets SET status="incident" WHERE id=?', (packet_id,))
                self.db.execute('INSERT INTO incidents(packet_id,kind) VALUES (?,?)', (packet_id, kind))

    def event(self, event_id):
        row = self.db.execute('SELECT body,deposit_digest FROM events WHERE id=?', (event_id,)).fetchone()
        if row is None:
            raise LabError('event_not_found')
        value = parse(row['body'])
        if digest(value) != row['deposit_digest']:
            raise LabError('deposit_digest_mismatch')
        return value

    def status(self):
        return {'lab_id': self.db.execute('SELECT value FROM meta WHERE key="lab_id"').fetchone()[0],
                **{table: self.db.execute('SELECT count(*) FROM ' + table).fetchone()[0]
                   for table in ('heads', 'events', 'memory', 'incidents')},
                'possibility_field_terminal': False}
