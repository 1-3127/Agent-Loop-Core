"""Local exact-version resolution and reviewed-copy boundary, with no execution."""
from pathlib import Path
import json

from session.session_boundary import file_identity
from core.skill_artifact import SkillRef, create_skill, digest_bytes, identifier, load_metadata


class SkillRegistry:
    def __init__(self, directory, vcs_revision):
        self.directory = Path(directory).resolve()
        self.vcs_revision = vcs_revision

    def resolve(self, skill_id, version):
        identifier(skill_id)
        identifier(version)
        directory = self.directory / version / skill_id
        if not directory.is_dir():
            raise ValueError('DEPENDENCY_MISSING / VERSION_UNRESOLVED: ' + skill_id + ':' + version)
        metadata = load_metadata(directory)
        ref = SkillRef(skill_id, version, metadata['content_hash'], file_identity(directory / 'core.json', skill_id + ':' + version), self.vcs_revision)
        ref.validate()
        return ref

    def search(self, artifact_type=None):
        result = []
        for path in sorted(self.directory.glob('*/*/core.json')):
            metadata = load_metadata(path.parent)
            if artifact_type is None or artifact_type in metadata['input_artifact_types']:
                result.append(self.resolve(metadata['skill_id'], metadata['version']))
        return tuple(result)

    def composition_preflight(self, selected, available_capabilities):
        order, visiting, visited = [], set(), set()
        def visit(ref):
            key = (ref.skill_id, ref.version)
            metadata = ref.validate()
            local = self.resolve(ref.skill_id, ref.version)
            if local != ref:
                raise ValueError('VERSION_UNRESOLVED')
            if key in visiting:
                raise ValueError('DEPENDENCY_CYCLE')
            if key in visited:
                return
            if not set(metadata['required_capabilities']) <= set(available_capabilities):
                raise ValueError('CAPABILITY_UNAVAILABLE')
            visiting.add(key)
            for dependency in metadata['callable_skills']:
                child = self.resolve(dependency['skill_id'], dependency['version'])
                visit(child)
                if child.content_hash != dependency['content_hash']:
                    raise ValueError('VERSION_UNRESOLVED')
            visiting.remove(key)
            visited.add(key)
            order.append(ref)
        for ref in selected:
            visit(ref)
        return tuple(order)

    def import_reviewed_copy(self, metadata, files, review_ref):
        """Import bytes only after exact-file review/license attestation; never execute."""
        review_ref.validate()
        review = json.loads(Path(review_ref.path).read_text(encoding='utf-8'))
        required = {'source_url', 'source_revision', 'source_files', 'license', 'copy_allowed', 'content_reviewed', 'review_summary'}
        if (set(review) != required or review['copy_allowed'] is not True or review['content_reviewed'] is not True
                or any(not isinstance(review[k], str) or not review[k].strip() for k in ('source_url', 'source_revision', 'license', 'review_summary'))
                or review['source_files'] != {name: digest_bytes(data) for name, data in files.items()}):
            raise ValueError('UNREVIEWED_SOURCE')
        reviewed_metadata = dict(metadata)
        reviewed_metadata['community_sources'] = [review]
        reviewed_metadata['provenance'] = {'kind': 'LOCAL_REVIEWED_COPY', 'review_ref': review_ref.__dict__}
        return create_skill(self.directory, reviewed_metadata, files)
