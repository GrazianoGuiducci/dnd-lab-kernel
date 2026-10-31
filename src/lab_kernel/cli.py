"""Receiver-owned local commands; neither source data nor model output runs commands."""
import argparse
import math
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from .engine import Lab, LabError, canonical, digest, instructions, parse


def read(path):
    return parse(Path(path).read_text(encoding='utf-8-sig'))


def _bounded_exchange(command, payload, environment, state, timeout, stdout_limit, stderr_limit):
    """Drain both pipes with bounded storage and stop the direct producer early."""
    try:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, shell=False, bufsize=0, cwd=state, env=environment)
    except OSError as exc:
        raise LabError('provider_transport_failed') from exc
    output = bytearray()
    failure, guard = [], threading.Lock()
    deadline = time.monotonic() + timeout

    def stop(kind):
        with guard:
            if not failure:
                failure.append(kind)
        try:
            process.kill()
        except OSError:
            pass

    def drain(stream, limit, kind, keep):
        count = 0
        try:
            while True:
                chunk = stream.read(min(8192, limit - count + 1))
                if not chunk:
                    break
                count += len(chunk)
                if count > limit:
                    stop(kind)
                    break
                if keep:
                    output.extend(chunk)
        except (OSError, ValueError):
            stop('provider_transport_failed')
        finally:
            stream.close()

    def send():
        try:
            view = memoryview(payload)
            while view:
                written = process.stdin.write(view)
                if not written:
                    break
                view = view[written:]
        except (BrokenPipeError, OSError, ValueError):
            pass  # Early child exit is classified from its status or pipe limit.
        finally:
            process.stdin.close()

    workers = [
        threading.Thread(target=drain, args=(process.stdout, stdout_limit,
                         'provider_response_too_large', True), daemon=True),
        threading.Thread(target=drain, args=(process.stderr, stderr_limit,
                         'provider_stderr_too_large', False), daemon=True),
        threading.Thread(target=send, daemon=True),
    ]
    for worker in workers:
        worker.start()
    try:
        process.wait(timeout=max(0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired:
        stop('provider_transport_timeout')
        process.wait()
    for worker in workers:
        worker.join(timeout=max(0, deadline - time.monotonic()))
    if any(worker.is_alive() for worker in workers):
        stop('provider_transport_timeout')
        # A descendant retaining pipe handles is outside direct-child control.
        # Daemon readers still cannot collect beyond the configured byte cap.
    if failure:
        raise LabError(failure[0])
    if process.returncode:
        raise LabError('provider_nonzero_exit')
    try:
        return output.decode('utf-8', errors='strict')
    except UnicodeError as exc:
        raise LabError('provider_transport_failed') from exc


def invoke(config, packet, state):
    if not isinstance(config, dict):
        raise LabError('provider_config_must_be_object')
    command = config.get('command')
    if not isinstance(command, list) or not command or not all(isinstance(x, str) and x for x in command):
        raise LabError('provider_command_must_be_argument_list')
    allowed = config.get('allow_env', [])
    if not isinstance(allowed, list) or not all(isinstance(x, str) for x in allowed):
        raise LabError('provider_environment_invalid')
    timeout = config.get('timeout_seconds', 120)
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise LabError('provider_timeout_invalid')
    stdout_limit = config.get('max_stdout_bytes', 4 * 1024 * 1024)
    stderr_limit = config.get('max_stderr_bytes', 64 * 1024)
    if any(type(limit) is not int or limit < 1 for limit in (stdout_limit, stderr_limit)):
        raise LabError('provider_output_limit_invalid')
    basic = {'path', 'systemroot', 'windir', 'temp', 'tmp', 'home', 'userprofile', 'lang', 'lc_all'}
    environment = {k: v for k, v in os.environ.items() if k.casefold() in basic or k in allowed}
    environment['PYTHONUTF8'] = '1'
    environment['PYTHONIOENCODING'] = 'utf-8'
    payload = canonical({'instructions': instructions(), 'contact': packet}).encode('utf-8')
    response = _bounded_exchange(command, payload, environment, state,
                                 timeout, stdout_limit, stderr_limit)
    return parse(response)


def run(lab, config, *, focus=None, competences=(), intent='', occurrences=1, seconds=None):
    results = []
    deadline = time.monotonic() + seconds if seconds is not None else None
    # Config/command identity changes contact; time and wake labels never do.
    if not isinstance(config, dict):
        raise LabError('provider_config_must_be_object')
    profile = digest({k: config.get(k) for k in ('command', 'profile', 'allow_env')})
    for _ in range(occurrences):
        if deadline is not None and time.monotonic() >= deadline:
            break
        packet = lab.prepare(focus=focus, competences=competences, intent=intent, profile=profile)
        if packet.get('status') == 'potential':
            results.append(packet)
            break
        try:
            result = invoke(config, packet, lab.root)
            results.append(lab.accept(packet['packet_id'], result))
        except (LabError, ValueError) as exc:
            lab.incident(packet['packet_id'], str(exc) if isinstance(exc, LabError) else 'invalid_response')
            results.append({'status': 'incident', 'kind': str(exc) if isinstance(exc, LabError) else 'invalid_response'})
            break  # No semantic repair or automatic retry of an incident.
    return results


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    p = argparse.ArgumentParser(description='Lab research kernel — receiver-owned state')
    p.add_argument('--state', help='Directory for this Lab instance only')
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('kernel')
    sub.add_parser('status')
    sub.add_parser('available')
    o = sub.add_parser('observe')
    o.add_argument('--id', required=True)
    o.add_argument('--file', required=True)
    o.add_argument('--owner', default='receiver')
    o.add_argument('--related', action='append', default=[])
    o.add_argument('--text', action='store_true')
    s = sub.add_parser('source')
    s.add_argument('--id', required=True)
    s.add_argument('--revision')
    c = sub.add_parser('competence')
    c.add_argument('--id', required=True)
    q = sub.add_parser('prepare')
    r = sub.add_parser('run')
    w = sub.add_parser('watch')
    for a in (q, r, w):
        a.add_argument('--focus', action='append')
        a.add_argument('--competence', action='append', default=[])
        a.add_argument('--intent', default='')
    q.add_argument('--profile', default='host')
    for a in (r, w):
        a.add_argument('--provider-file', required=a is r)
        a.add_argument('--occurrences', type=int, default=1)
        a.add_argument('--seconds', type=float)
    w.add_argument('--id', required=True)
    w.add_argument('--file', required=True)
    w.add_argument('--owner', default='receiver-monitor')
    w.add_argument('--ticks', type=int, default=1)
    w.add_argument('--interval', type=float, default=1)
    a = sub.add_parser('record')
    a.add_argument('--packet-file', required=True)
    a.add_argument('--event-file', required=True)
    e = sub.add_parser('event')
    e.add_argument('--id', required=True)
    sub.add_parser('verify')
    args = p.parse_args(argv)
    lab = None
    try:
        if args.action == 'kernel':
            print(instructions())
            return 0
        if args.state is None:
            raise LabError('receiver_state_directory_required')
        if getattr(args, 'occurrences', 1) < 1 or getattr(args, 'ticks', 1) < 1:
            raise LabError('positive_run_budget_required')
        if getattr(args, 'interval', 1) < 0 or (getattr(args, 'seconds', None) is not None and args.seconds <= 0):
            raise LabError('invalid_time_budget')
        lab = Lab(args.state)
        if args.action == 'status':
            value = lab.status()
        elif args.action == 'available':
            value = lab.available()
        elif args.action == 'observe':
            payload = Path(args.file).read_text(encoding='utf-8') if args.text else read(args.file)
            value = lab.observe(args.id, payload, owner=args.owner, related=args.related)
        elif args.action == 'source':
            value = lab.source(args.id, args.revision)
        elif args.action == 'competence':
            value = lab.competence(args.id)
        elif args.action == 'prepare':
            value = lab.prepare(focus=args.focus, competences=args.competence,
                                intent=args.intent, profile=args.profile)
        elif args.action == 'record':
            value = lab.accept(read(args.packet_file)['packet_id'], read(args.event_file))
        elif args.action == 'event':
            value = lab.event(args.id)
        elif args.action in ('run', 'watch'):
            config = read(args.provider_file) if args.provider_file else None
            options = dict(focus=args.focus, competences=args.competence, intent=args.intent,
                           occurrences=args.occurrences, seconds=args.seconds)
            if args.action == 'run':
                value = run(lab, config, **options)
            else:
                value = []
                for tick in range(args.ticks):
                    observed = lab.observe(args.id, read(args.file), owner=args.owner)
                    result = run(lab, config, **options) if config else []
                    value.append({'observation': observed, 'occurrences': result})
                    if tick + 1 < args.ticks:
                        time.sleep(args.interval)
        else:
            ids = [row[0] for row in lab.db.execute('SELECT id FROM events ORDER BY seq')]
            for event_id in ids:
                lab.event(event_id)
            for row in lab.db.execute('SELECT rev,body FROM versions'):
                if digest(parse(row['body'])) != row['rev']:
                    raise LabError('source_digest_mismatch')
            value = {'events_verified': len(ids), 'source_versions_verified':
                     lab.db.execute('SELECT count(*) FROM versions').fetchone()[0]}
        print(canonical(value))
        return 0
    except (LabError, OSError, KeyError, ValueError) as exc:
        # Do not print arbitrary provider output or data in controller errors.
        print(canonical({'error': str(exc) if isinstance(exc, LabError) else type(exc).__name__}), file=sys.stderr)
        return 2
    finally:
        if lab:
            lab.close()
