import json
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from core.skill_artifact import create_skill, digest_bytes, load_metadata, record_validation, validation_status
from core.skill_registry import SkillRegistry
from session.session_boundary import file_identity


def candidate(name, dependencies=(), capabilities=()):
    return {'skill_id': name, 'version': 'v1', 'content_hash': '', 'status': 'CANDIDATE',
        'provenance': {'kind': 'INDEPENDENT_LOCAL', 'purpose': 'synthetic contract fixture'},
        'community_sources': [], 'input_artifact_types': ['reference'], 'output_artifact_types': ['geometry'],
        'required_capabilities': list(capabilities), 'candidate_tools': [], 'candidate_models': [],
        'callable_skills': list(dependencies), 'review_gates': ['geometry'], 'known_failure_modes': ['conditioning'],
        'restart_conditions': ['strategy inadequate'], 'created_from_session': None,
        'created_from_production_run': None, 'validated_scenarios': [], 'last_validated': None, 'files': {}}


def guidance(name):
    return {'SKILL.md': ('---\nname: ' + name + '\ndescription: Inspect reference evidence before planning geometry.\n---\n\nPreserve reference authority.\n').encode()}


class SkillArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.registry = SkillRegistry(self.root / 'skills', '1' * 40)

    def make(self, name, dependencies=(), capabilities=()):
        create_skill(self.registry.directory, candidate(name, dependencies, capabilities), guidance(name))
        return self.registry.resolve(name, 'v1')

    def test_exact_version_hash_and_mutation(self):
        skill = self.make('inspect-reference')
        self.assertEqual(validation_status(skill), 'CANDIDATE')
        self.assertEqual(self.registry.search('reference'), (skill,))
        Path(skill.metadata.path).with_name('SKILL.md').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'SKILL_HASH_MISMATCH'):
            skill.validate()

    def test_version_cannot_overwrite_or_change_its_identity(self):
        self.make('geometry')
        with self.assertRaisesRegex(ValueError, 'SKILL_VERSION_COLLISION'):
            self.make('geometry')
        metadata = candidate('geometry')
        metadata['status'] = 'VALIDATED'
        with self.assertRaisesRegex(ValueError, 'CANDIDATE'):
            create_skill(self.registry.directory, metadata, guidance('geometry'))

    def test_guidance_and_path_preflight_before_writing(self):
        with self.assertRaises(ValueError):
            create_skill(self.registry.directory, candidate('geometry'), {'SKILL.md': b'invalid'})
        self.assertFalse((self.registry.directory / 'v1/geometry').exists())
        files = guidance('geometry') | {'../outside': b'bad'}
        with self.assertRaises(ValueError):
            create_skill(self.registry.directory, candidate('geometry'), files)
        self.assertFalse(self.registry.directory.exists())

    def test_extra_support_file_cannot_escape_manifest(self):
        skill = self.make('geometry')
        directory = Path(skill.metadata.path).parent
        (directory / 'nested').mkdir()
        (directory / 'nested/core.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            load_metadata(directory)

    def test_dependency_capability_and_exact_hash_resolution(self):
        leaf = self.make('leaf', capabilities=('comfy',))
        dependency = {'skill_id': leaf.skill_id, 'version': leaf.version, 'content_hash': leaf.content_hash}
        parent = self.make('parent', (dependency,))
        self.assertEqual(self.registry.composition_preflight((parent,), ('comfy',)), (leaf, parent))
        with self.assertRaisesRegex(ValueError, 'CAPABILITY_UNAVAILABLE'):
            self.registry.composition_preflight((parent,), ())
        missing = self.make('missing', ({'skill_id': 'absent', 'version': 'v1', 'content_hash': '0' * 64},))
        with self.assertRaisesRegex(ValueError, 'DEPENDENCY_MISSING'):
            self.registry.composition_preflight((missing,), ('comfy',))
        wrong = self.make('wrong', (dependency | {'content_hash': '0' * 64},))
        with self.assertRaisesRegex(ValueError, 'VERSION_UNRESOLVED'):
            self.registry.composition_preflight((wrong,), ('comfy',))

    def test_cycle_precedes_effect_even_with_unresolvable_recursive_hash_pins(self):
        first = self.make('first', ({'skill_id': 'second', 'version': 'v1', 'content_hash': '0' * 64},))
        self.make('second', ({'skill_id': 'first', 'version': 'v1', 'content_hash': first.content_hash},))
        with self.assertRaisesRegex(ValueError, 'DEPENDENCY_CYCLE'):
            self.registry.composition_preflight((first,), ())

    def test_duplicate_selection_still_validates_every_pin(self):
        skill = self.make('leaf')
        forged = replace(skill, content_hash='0' * 64)
        with self.assertRaises(ValueError):
            self.registry.composition_preflight((skill, forged), ())

    def test_unreviewed_or_wrong_license_copy_has_no_write(self):
        review = {'source_url': 'https://example.invalid/fixture', 'source_revision': 'fixture-v1',
            'source_files': {}, 'license': 'UNKNOWN', 'copy_allowed': False, 'content_reviewed': False,
            'review_summary': 'Synthetic unreviewed source, never execute'}
        path = self.root / 'review.json'
        path.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'UNREVIEWED_SOURCE'):
            self.registry.import_reviewed_copy(candidate('copy'), guidance('copy'), file_identity(path, 'review'))
        self.assertFalse(self.registry.directory.exists())

    def test_synthetic_success_cannot_promote_skill(self):
        skill = self.make('geometry')
        path = self.root / 'success.json'
        path.write_text(json.dumps({'scope': 'SYNTHETIC', 'INTERNAL_ACCEPT': True, 'session_terminal': 'CLOSED'}))
        with self.assertRaisesRegex(ValueError, 'ACTUAL_SUCCESS_REQUIRED'):
            record_validation(skill, file_identity(path, 'synthetic'), self.root / 'validation.json')
        self.assertFalse((self.root / 'validation.json').exists())
        self.assertEqual(validation_status(skill), 'CANDIDATE')

    def test_reviewed_copy_pins_source_bytes_and_never_runs_script(self):
        files = guidance('copy') | {'scripts/unused.py': b'raise AssertionError("import must not execute community scripts")\n'}
        review = {'source_url': 'https://example.invalid/synthetic-fixture', 'source_revision': 'fixture-v1',
            'source_files': {name: digest_bytes(data) for name, data in files.items()}, 'license': 'Synthetic fixture permission',
            'copy_allowed': True, 'content_reviewed': True, 'review_summary': 'Only a local synthetic import fixture'}
        path = self.root / 'review.json'
        path.write_text(json.dumps(review))
        self.registry.import_reviewed_copy(candidate('copy'), files, file_identity(path, 'review'))
        skill = self.registry.resolve('copy', 'v1')
        metadata = skill.validate()
        self.assertEqual(metadata['community_sources'][0]['source_revision'], 'fixture-v1')
        self.assertEqual(validation_status(skill), 'CANDIDATE')
        review['source_files']['SKILL.md'] = '0' * 64
        changed = self.root / 'changed-review.json'
        changed.write_text(json.dumps(review))
        with self.assertRaisesRegex(ValueError, 'UNREVIEWED_SOURCE'):
            self.registry.import_reviewed_copy(candidate('copy'), files, file_identity(changed, 'changed'))


if __name__ == '__main__':
    unittest.main()
