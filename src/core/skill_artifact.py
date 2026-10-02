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


def record_validation(skill, actual_success_ref, output_path):
    """Validate a caller's actual-success lineage attestation, never synthetic PASS."""
    skill.validate()
    actual_success_ref.validate()
    evidence = json.loads(Path(actual_success_ref.path).read_text(encoding='utf-8'))
    if (evidence.get('scope') != 'ACTUAL' or evidence.get('INTERNAL_ACCEPT') is not True
            or evidence.get('session_terminal') != 'CLOSED' or not evidence.get('session_id')
            or not evidence.get('production_run_id') or evidence.get('skill_refs') is None
            or asdict(skill) not in evidence['skill_refs'] or not evidence.get('review_refs')
            or not evidence.get('frontier_invocation_refs') or evidence.get('known_limitations') is None):
        raise ValueError('ACTUAL_SUCCESS_REQUIRED')
    for item in evidence['review_refs'] + evidence['frontier_invocation_refs']:
        FileIdentity(**item).validate()
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
    FileIdentity(**record['actual_success']).validate()
    return 'VALIDATED'
