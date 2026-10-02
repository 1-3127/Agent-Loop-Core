"""Immutable portable Skill packages; no execution or Session transitions."""
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re

from session.session_boundary import FileIdentity, file_identity

FIELDS = frozenset({'skill_id', 'version', 'content_hash', 'status', 'provenance',
    'community_sources', 'input_artifact_types', 'output_artifact_types',
    'required_capabilities', 'candidate_tools', 'candidate_models', 'callable_skills',
    'review_gates', 'known_failure_modes', 'restart_conditions', 'created_from_session',
    'created_from_production_run', 'validated_scenarios', 'last_validated', 'files'})
LISTS = ('input_artifact_types', 'output_artifact_types', 'required_capabilities',
    'candidate_tools', 'candidate_models', 'review_gates', 'known_failure_modes',
    'restart_conditions', 'validated_scenarios')


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest_bytes(data):
    return hashlib.sha256(data).hexdigest()


def write_once(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(canonical_bytes(value) + b'\n')


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,63}', value):
        raise ValueError('invalid Skill identity/version')


@dataclass(frozen=True)
class SkillRef:
    skill_id: str
    version: str
    content_hash: str
    metadata: FileIdentity
    vcs_revision: str

    def validate(self):
        identifier(self.skill_id)
        identifier(self.version)
        if not re.fullmatch(r'[0-9a-f]{64}', self.content_hash) or not re.fullmatch(r'[0-9a-f]{40,64}', self.vcs_revision):
            raise ValueError('invalid Skill hash/VCS pin')
        self.metadata.validate()
        metadata = load_metadata(Path(self.metadata.path).parent)
        if (metadata['skill_id'], metadata['version'], metadata['content_hash']) != (self.skill_id, self.version, self.content_hash):
            raise ValueError('SKILL_VERSION_MISMATCH')
        return metadata


def package_hash(metadata):
    return digest_bytes(canonical_bytes({key: value for key, value in metadata.items() if key != 'content_hash'}))


def check_metadata(metadata):
    if not isinstance(metadata, dict) or set(metadata) != FIELDS:
        raise ValueError('Skill metadata fields differ')
    identifier(metadata['skill_id'])
    identifier(metadata['version'])
    # Lifecycle is an append-only validation record; the used package never mutates.
    if metadata['status'] != 'CANDIDATE' or metadata['validated_scenarios'] or metadata['last_validated'] is not None:
        raise ValueError('new immutable package must be CANDIDATE')
    for name in LISTS:
        values = metadata[name]
        if not isinstance(values, list) or any(not isinstance(v, str) or not v.strip() for v in values) or len(values) != len(set(values)):
            raise ValueError('invalid Skill ' + name)
    if not metadata['input_artifact_types'] or not metadata['output_artifact_types']:
        raise ValueError('Skill input/output meaning required')
    if not isinstance(metadata['provenance'], dict) or not metadata['provenance']:
        raise ValueError('Skill provenance required')
    if not isinstance(metadata['community_sources'], list) or not isinstance(metadata['callable_skills'], list):
        raise ValueError('Skill source/dependency selections required')
    for dependency in metadata['callable_skills']:
        if not isinstance(dependency, dict) or set(dependency) != {'skill_id', 'version', 'content_hash'}:
            raise ValueError('exact dependency pin required')
        identifier(dependency['skill_id'])
        identifier(dependency['version'])
        if not re.fullmatch(r'[0-9a-f]{64}', dependency['content_hash']):
            raise ValueError('exact dependency content hash required')
    for name in ('created_from_session', 'created_from_production_run'):
        if metadata[name] is not None and (not isinstance(metadata[name], str) or not metadata[name].strip()):
            raise ValueError('invalid creation lineage')
    if not isinstance(metadata['files'], dict) or 'SKILL.md' not in metadata['files']:
        raise ValueError('portable SKILL.md required')
    for name, digest in metadata['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or ':' in name or name == 'core.json' or not re.fullmatch(r'[0-9a-f]{64}', str(digest)):
            raise ValueError('invalid Skill file manifest')
    if metadata['content_hash'] != package_hash(metadata):
        raise ValueError('SKILL_HASH_MISMATCH')
    return metadata


def load_metadata(directory):
    directory = Path(directory).resolve()
    metadata = check_metadata(json.loads((directory / 'core.json').read_text(encoding='utf-8')))
    actual = {p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file() and p != directory / 'core.json'}
    if actual != set(metadata['files']):
        raise ValueError('Skill file inventory differs')
    for name, expected in metadata['files'].items():
        path = directory / name
        if path.is_symlink() or not path.resolve().is_relative_to(directory) or digest_bytes(path.read_bytes()) != expected:
            raise ValueError('SKILL_HASH_MISMATCH')
    check_guidance((directory / 'SKILL.md').read_text(encoding='utf-8'), metadata['skill_id'])
    return metadata


def check_guidance(text, skill_id):
    header = text.split('---', 2)
    if len(header) != 3 or header[0].strip() or not re.search(r'^name:\s*[\"\']?' + re.escape(skill_id) + r'[\"\']?\s*$', header[1], re.M) or not re.search(r'^description:\s*\S', header[1], re.M):
        raise ValueError('portable Skill name/description required')


def create_skill(registry_root, metadata, files):
    """Write a new version exclusively; never run its scripts."""
    metadata = dict(metadata)
    if not isinstance(files, dict) or any(not isinstance(data, bytes) for data in files.values()):
        raise ValueError('explicit Skill file bytes required')
    metadata['files'] = {name: digest_bytes(data) for name, data in files.items()}
    metadata['content_hash'] = package_hash(metadata)
    check_metadata(metadata)
    check_guidance(files['SKILL.md'].decode('utf-8'), metadata['skill_id'])
    directory = Path(registry_root) / metadata['version'] / metadata['skill_id']
    if directory.exists():
        raise ValueError('SKILL_VERSION_COLLISION')
    directory.mkdir(parents=True)
    for name, data in files.items():
        path = directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
    write_once(directory / 'core.json', metadata)
    load_metadata(directory)
    return directory


def checked_actual_success(skill, actual_success_ref):
    """Bind promotion to actual inference, current acceptance and closed handoff.

    These are local evidence contracts, not a tamper-proof runtime attestation.
    A caller's ACTUAL label alone never upgrades synthetic evidence.
    """
    skill.validate()
    actual_success_ref.validate()
    evidence = json.loads(Path(actual_success_ref.path).read_text(encoding='utf-8'))
    if (evidence.get('scope') != 'ACTUAL' or evidence.get('INTERNAL_ACCEPT') is not True
            or evidence.get('session_terminal') != 'CLOSED' or not evidence.get('session_id')
            or not evidence.get('production_run_id') or evidence.get('skill_refs') is None
            or asdict(skill) not in evidence['skill_refs'] or not evidence.get('review_refs')
            or not evidence.get('frontier_invocation_refs') or evidence.get('known_limitations') is None
            or not evidence.get('terminal_ref') or not evidence.get('acceptance_gate_ref')):
        raise ValueError('ACTUAL_SUCCESS_REQUIRED')
    for item in evidence['review_refs'] + evidence['frontier_invocation_refs']:
        FileIdentity(**item).validate()
    terminal_ref, gate_ref = FileIdentity(**evidence['terminal_ref']), FileIdentity(**evidence['acceptance_gate_ref'])
    terminal_ref.validate()
    gate_ref.validate()
    terminal = json.loads(Path(terminal_ref.path).read_text(encoding='utf-8'))
    gate = json.loads(Path(gate_ref.path).read_text(encoding='utf-8'))
    state = {k: evidence[k] for k in ('session_id', 'production_run_id')}
    if (terminal.get('status') != 'CLOSED' or terminal.get('session_id') != state['session_id']
            or gate.get('INTERNAL_ACCEPT') is not True or gate.get('mode') != 'ACTUAL'
            or any(gate.get(k) != v for k, v in state.items())
            or gate.get('current_review_refs') != evidence['review_refs']):
        raise ValueError('ACTUAL_SUCCESS_REQUIRED: current acceptance/terminal lineage')
    workflow_ref = FileIdentity(**gate['workflow_ref']['file'])
    workflow_ref.validate()
    workflow = json.loads(Path(workflow_ref.path).read_text(encoding='utf-8'))
    if asdict(skill) not in workflow['skill_refs']:
        raise ValueError('ACTUAL_SUCCESS_REQUIRED: Skill absent from accepted Workflow')
    for item in evidence['frontier_invocation_refs']:
        invocation = json.loads(Path(item['path']).read_text(encoding='utf-8'))
        if invocation.get('mode') != 'ACTUAL' or invocation.get('status') != 'SUCCESS':
            raise ValueError('ACTUAL_SUCCESS_REQUIRED: synthetic/failed Frontier')
        FileIdentity(**invocation['request_ref']).validate()
        FileIdentity(**invocation['result_ref']).validate()
    covered = set()
    for item in evidence['review_refs']:
        review = json.loads(Path(item['path']).read_text(encoding='utf-8'))
        if (review.get('inference_mode') != 'ACTUAL' or review.get('verdict') != 'PASS'
                or any(review.get(k) != v for k, v in state.items())
                or review.get('attempt_id') != gate['attempt_id'] or review.get('workflow_ref') != gate['workflow_ref']):
            raise ValueError('ACTUAL_SUCCESS_REQUIRED: synthetic/stale/unmet Review')
        invocation_ref = FileIdentity(**review['invocation_ref'])
        invocation_ref.validate()
        invocation = json.loads(Path(invocation_ref.path).read_text(encoding='utf-8'))
        if (invocation.get('mode') != 'ACTUAL' or invocation.get('status') != 'SUCCESS'
                or invocation['result_ref'] != review['result_ref'] or invocation['request_ref'] != review['request_ref']):
            raise ValueError('ACTUAL_SUCCESS_REQUIRED: Review invocation mismatch')
        for ref in (review['result_ref'], review['request_ref']):
            FileIdentity(**ref).validate()
        result = json.loads(Path(review['result_ref']['path']).read_text(encoding='utf-8'))
        if result['criterion_results_json'] != review['criterion_results_json'] or result['verdict'] != 'PASS':
            raise ValueError('ACTUAL_SUCCESS_REQUIRED: Review result mismatch')
        outcomes = json.loads(review['criterion_results_json'])
        if any(o['outcome'] != 'MET' for o in outcomes):
            raise ValueError('ACTUAL_SUCCESS_REQUIRED: unmet criterion')
        covered.update(o['criterion_id'] for o in outcomes)
    if not set(gate['mandatory_criterion_ids']) <= covered:
        raise ValueError('ACTUAL_SUCCESS_REQUIRED: mandatory coverage incomplete')
    decision_ref = FileIdentity(**gate['decision_ref'])
    decision_ref.validate()
    decision = json.loads(Path(decision_ref.path).read_text(encoding='utf-8'))
    if (decision['selected_action'] != 'ACCEPT' or decision['inference_mode'] != 'ACTUAL'
            or decision['frontier_invocation_ref'] not in evidence['frontier_invocation_refs']):
        raise ValueError('ACTUAL_SUCCESS_REQUIRED: accepted Frontier decision absent')
    return evidence


def record_validation(skill, actual_success_ref, output_path):
    """Persist an immutable promotion after validating actual successful lineage."""
    evidence = checked_actual_success(skill, actual_success_ref)
    record = {'status': 'VALIDATED', 'skill_ref': asdict(skill), 'actual_success': asdict(actual_success_ref),
        'session_id': evidence['session_id'], 'production_run_id': evidence['production_run_id'],
        'review_refs': evidence['review_refs'], 'known_limitations': evidence['known_limitations']}
    write_once(output_path, record)
    return file_identity(output_path, skill.skill_id + ':' + skill.version + ':validation')


def validation_status(skill, validation_ref=None):
    skill.validate()
    if validation_ref is None:
        return 'CANDIDATE'
    validation_ref.validate()
    record = json.loads(Path(validation_ref.path).read_text(encoding='utf-8'))
    if record['status'] != 'VALIDATED' or record['skill_ref'] != asdict(skill):
        raise ValueError('Skill validation identity differs')
    checked_actual_success(skill, FileIdentity(**record['actual_success']))
    return 'VALIDATED'
