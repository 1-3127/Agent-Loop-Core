"""Read the exact committed Final-2 source under a write/transport tripwire."""
import json
import os
from pathlib import Path
import sys
from unittest import mock

ROOT = Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
sys.path[:0] = [str(ROOT / 'src'), str(ROOT)]
from scenario_a import l7_feedback_controller as controller
from scenario_a import l7_geometry_review as bridge
source_dir = ROOT / 'runs/l7/fsf2-bridge-20261001-194618-9febb329'
counts = {'writes': 0, 'network': 0, 'process': 0}
def audit(event, args):
    if event == 'open':
        mode, flags = args[1:3]
        if (isinstance(mode, str) and any(x in mode for x in 'wax+')) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC):
            counts['writes'] += 1
            raise RuntimeError('Historical write forbidden')
    if event.startswith('socket.') and event in ('socket.connect', 'socket.getaddrinfo', 'socket.gethostbyname'):
        counts['network'] += 1
        raise RuntimeError('Network forbidden')
    if event == 'subprocess.Popen':
        counts['process'] += 1
        raise RuntimeError('Process forbidden')
sys.addaudithook(audit)
with mock.patch.object(controller.l6.worker, 'run', side_effect=AssertionError('Worker forbidden')) as worker, \
     mock.patch.object(controller.l6.reviewer, 'review_once', side_effect=AssertionError('Reviewer forbidden')) as reviewer:
    source = controller.validate_source(source_dir)
    worker.assert_not_called()
    reviewer.assert_not_called()
terminal = controller.read(source_dir / 'terminal.json')
print(json.dumps({'source_validation': 'PASS', 'run_id': source['run_id'], 'verdict': source['verdict'],
    'action': source['action'], 'terminal': source['terminal'], 'record_keys': sorted(terminal['records']),
    'observed_stream_records': {k: v for k, v in terminal['records'].items() if k.endswith(('.stdout', '.stderr'))},
    'tripwires': counts, 'correction_dispatches': 0,
    'scope': 'Read-only historical source validation; Session remains FAILED and is not resumed'}), flush=True)
