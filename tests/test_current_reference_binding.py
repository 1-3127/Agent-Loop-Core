"""Current single-image binding regressions; all production transports are tripwired."""
from dataclasses import asdict, replace
from pathlib import Path
import unittest
from unittest import mock

from PIL import Image, ImageDraw

import tests.test_l6_pipeline as fixtures
from session import session_boundary as session
from scenario_a import session_binding as bound
from scenario_a import l6_pipeline as l6
from scenario_a import l7_feedback_controller as controller


class CurrentReferenceTests(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.L6PipelineTests()
        self.f.setUp()
        self.addCleanup(self.f.doCleanups)
        self.source = self.f.root / 'external-lantern.png'
        image = Image.new('RGB', (768, 768), 'white')
        draw = ImageDraw.Draw(image)
        draw.polygon([(100,200),(380,90),(670,200)], fill='gray')
        draw.rectangle((250,220,510,460), fill='gray')
        draw.rectangle((315,280,445,395), fill='white')
        draw.rectangle((330,460,430,640), fill='gray')
        draw.rectangle((200,640,565,695), fill='gray')
        image.save(self.source)
        self.parent, self.current, self.boundary, self.binding = self.prepare('lantern-a', self.source)

    def prepare(self, label, path, **overrides):
        file = session.file_identity(path, 'USER_CURRENT_REFERENCE')
        authority = bound.reference_authority(file)
        doc = self.f.root / (label+'.md')
        doc.write_text('Goal: create lantern GLB.\nMust-Have: square opening.\nReference: '+authority,
                       encoding='utf-8')
        fields = session.FinalizedFields(label, 'v1', 'NEW_WORK', True, (),
            (session.AcceptanceCriterion('AC1','REF',True,'preserve lantern'),),
            (session.AuthorityReference('USER','current request'),
             session.AuthorityReference('REF',authority)), ('single PNG',))
        spec = session.freeze_specification(doc, fields)
        boundary = session.SessionBoundary(label, self.f.root/(label+'-session'))
        binding = boundary.create_binding(spec, label+'-loop')
        current = bound.freeze_current_reference(binding, file, 'REF')
        ids = dict(l6=label+'-l6', bridge=label+'-bridge', correction=label+'-correction')
        options = dict(goal=dict(text='create lantern GLB.',authority_ref='USER'),
            must_haves=(dict(text='square opening.',authority_ref='REF'),),
            stage_criteria=dict(multiview=('AC1',),geometry=('AC1',)),
            child_ids=ids, current_reference=current)
        options.update(overrides)
        parent = bound.prepare(boundary,binding,**options)
        return parent,current,boundary,binding

    def run_l6(self, parent=None, *, execute=False):
        parent = parent or self.parent
        return l6.run_pipeline(l6.read_ref(parent)['child_ids']['l6'], self.f.comfy,
                               execute=execute, session_binding=parent)

    def tag_review(self, request_path, result_path, report_path):
        result=l6.read_json(result_path)
        result['observations']=['[AC1@REF] SATISFIED: fixture input identity']
        l6.worker.write_report(result_path,result)
        report=l6.read_json(report_path)
        report['result_sha256']=l6.digest(result_path)
        l6.worker.write_report(report_path,report)

    def zero_effects(self):
        self.f.worker_mock.assert_not_called()
        self.f.review_mock.assert_not_called()
        self.f.network.assert_not_called()
        self.f.process.assert_not_called()

    def assert_current_plan(self, parent):
        data=l6.read_ref(parent)
        run_dir=self.f.repo/'runs/l6'/data['child_ids']['l6']
        staging=l6.read_json(run_dir/'reference_staging.json')
        self.assertEqual(staging['current_reference'],data['current_reference'])
        self.assertEqual(staging['staged']['sha256'],data['current_reference']['file']['sha256'])
        self.assertEqual(Path(staging['staged']['path']).read_bytes(), Path(data['current_reference']['file']['path']).read_bytes())
        input_name='l6/'+run_dir.name+'/front.png'
        for stage in l6.VIEWS+('geometry',):
            plan=l6.read_json(run_dir/(stage+'_plan.json'))
            self.assertEqual(plan['patches']['1']['image'],input_name)
            self.assertNotIn('hunyuan-official-demo-padded.png',str(plan))
            order=l6.read_json(run_dir/(stage+'_work_order.json'))
            execution=l6.read_json(run_dir/(stage+'_execution.json'))
            self.assertEqual(order['initial_contract'],l6.reference(run_dir/'initial.json'))
            self.assertEqual(execution['plan'],order['plan'])
            if stage != 'geometry':
                self.assertEqual(order['inputs']['source']['sha256'],data['current_reference']['file']['sha256'])
            else:
                self.assertEqual(order['inputs']['artifacts'][0]['sha256'],data['current_reference']['file']['sha256'])
        l6.validate_current_staging(run_dir)
        return run_dir

    def test_fresh_session_lantern_blocker_regression_and_staged_worker_plan(self):
        self.f.review_after=self.tag_review
        original=self.f.source.read_bytes()
        # Bound production has no dependency on the historical input file.
        self.f.source.unlink()
        self.assertEqual(self.run_l6()['status'],'PREFLIGHT_PASS')
        self.zero_effects()
        self.assertEqual(self.run_l6(execute=True)['state'],'GEOMETRY_READY')
        self.assert_current_plan(self.parent)
        self.assertFalse(self.f.source.exists())
        self.assertNotEqual(self.current.file.sha256,l6.hashlib.sha256(original).hexdigest())
        self.assertEqual(self.f.worker_mock.call_count,4)
        self.f.network.assert_not_called()
        self.f.process.assert_not_called()

    def test_two_references_never_cross_attempts(self):
        second=self.f.root/'external-b.png'
        Image.new('RGB',(768,768),'purple').save(second)
        parent_b,current_b,_,_=self.prepare('lantern-b',second)
        self.f.review_after=self.tag_review
        for parent in (self.parent,parent_b):
            self.assertEqual(self.run_l6(parent,execute=True)['state'],'GEOMETRY_READY')
            self.assert_current_plan(parent)
        self.assertNotEqual(self.current.file.sha256,current_b.file.sha256)
        self.assertNotEqual(l6.read_ref(self.parent)['child_ids'],l6.read_ref(parent_b)['child_ids'])
        self.f.network.assert_not_called()

    def test_missing_reference_prepare_and_entry_reject_without_fallback(self):
        with self.assertRaisesRegex(ValueError,'CURRENT_REFERENCE_REQUIRED'):
            self.prepare('missing-binding',self.source,current_reference=None)
        data=l6.read_ref(self.parent)
        data['current_reference']=None
        path=self.f.root/'missing-parent.json'
        l6.write_once(path,data)
        with self.assertRaisesRegex(ValueError,'CURRENT_REFERENCE_REQUIRED'):
            self.run_l6(l6.reference(path),execute=True)
        self.zero_effects()

    def test_wrong_expected_hash_rejected_before_prepare_or_worker(self):
        bad=replace(self.current,file=replace(self.current.file,sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            bound.checked_current_reference(asdict(bad),self.binding)
        data=l6.read_ref(self.parent); data['current_reference']=asdict(bad)
        path=self.f.root/'wrong-hash-parent.json'; l6.write_once(path,data)
        with self.assertRaisesRegex(ValueError,'hash mismatch'):
            self.run_l6(l6.reference(path),execute=True)
        self.zero_effects()

    def test_mutation_after_freeze_blocks_first_effect(self):
        Image.new('RGB',(768,768),'red').save(self.source)
        with self.assertRaisesRegex(ValueError,'size mismatch|hash mismatch'):
            self.run_l6(execute=True)
        self.assertFalse((self.f.repo/'runs/l6/lantern-a-l6').exists())
        self.zero_effects()

    def test_missing_source_blocks_first_effect(self):
        self.source.unlink()
        with self.assertRaisesRegex(ValueError,'regular file'):
            self.run_l6(execute=True)
        self.zero_effects()

    def test_wrong_session_spec_and_authority_reject(self):
        for key,value in [('session_id','other-session'),
                          ('specification_identity_sha256','0'*64),
                          ('authority_ref','USER'),('authority_source','current request')]:
            with self.subTest(key=key):
                data=l6.read_ref(self.parent); data['current_reference'][key]=value
                path=self.f.root/(key+'.json'); l6.write_once(path,data)
                with self.assertRaisesRegex(ValueError,'Session/Specification/authority mismatch'):
                    self.run_l6(l6.reference(path),execute=True)
        self.zero_effects()

    def test_another_frozen_spec_cannot_supply_reference(self):
        _,other,_,_=self.prepare('other-spec',self.source)
        data=l6.read_ref(self.parent); data['current_reference']=asdict(other)
        path=self.f.root/'other-spec-parent.json'; l6.write_once(path,data)
        with self.assertRaisesRegex(ValueError,'Session/Specification/authority mismatch'):
            self.run_l6(l6.reference(path),execute=True)
        self.zero_effects()

    def test_staging_collision_both_modes_and_direct_l6(self):
        destination=self.f.comfy/'work/input/l6/lantern-a-l6'
        destination.mkdir(parents=True)
        marker=destination/'front.png'; marker.write_bytes(b'existing bytes')
        for execute in (False,True):
            with self.subTest(execute=execute),self.assertRaisesRegex(ValueError,'external namespace exists'):
                self.run_l6(execute=execute)
        self.assertEqual(marker.read_bytes(),b'existing bytes')
        self.assertFalse((self.f.repo/'runs/l6/lantern-a-l6').exists())
        self.zero_effects()

    def test_full_entry_uses_current_reference_and_i03_gate(self):
        from scenario_a import l7_geometry_review as bridge
        with mock.patch.object(bridge,'blender_identity',return_value={'executable':'fixture'}):
            checks=bound.run_session(self.parent,comfy_root=self.f.comfy)
            self.assertEqual(checks['status'],'PREFLIGHT_PASS')
            destination=self.f.comfy/'work/output/l7/lantern-a-bridge'
            destination.mkdir(parents=True)
            with self.assertRaisesRegex(ValueError,'external namespace exists'):
                bound.run_session(self.parent,comfy_root=self.f.comfy,execute=True)
        self.zero_effects()

    def test_non_png_source_type_rejected(self):
        self.source.write_bytes(b'not an image')
        with self.assertRaises(ValueError):
            self.prepare('not-png',self.source)
        self.zero_effects()

    def test_source_changes_between_gate_and_staging_rejected(self):
        original=l6.stage_current_reference
        def mutate(*args):
            Image.new('RGB',(768,768),'blue').save(self.source)
            return original(*args)
        with mock.patch.object(l6,'stage_current_reference',side_effect=mutate):
            with self.assertRaisesRegex(ValueError,'size mismatch|hash mismatch'):
                self.run_l6(execute=True)
        self.zero_effects()

    def test_staged_mutation_blocks_first_worker(self):
        original=l6.stage_current_reference
        def mutate(run_dir,root,parent):
            record=original(run_dir,root,parent)
            staged=Path(l6.read_ref(record)['staged']['path'])
            Image.new('RGB',(768,768),'blue').save(staged)
            return record
        with mock.patch.object(l6,'stage_current_reference',side_effect=mutate):
            result=self.run_l6(execute=True)
        self.assertEqual(result['state'],'FAILED')
        self.zero_effects()

    def test_geometry_correction_keeps_bound_front_patch(self):
        self.f.review_after=self.tag_review
        self.run_l6(execute=True)
        run_dir=self.assert_current_plan(self.parent)
        prior=l6.reference(run_dir/'geometry_plan.json')
        initial={'source':{'input':{'geometry_plan':prior}},
                 'action':{'code':'REGENERATE_GEOMETRY','target':'geometry'}}
        corrected=self.f.root/'correction'; corrected.mkdir()
        with mock.patch.object(controller,'guard',return_value=initial), \
             mock.patch.object(controller,'validate_staging'):
            plan=controller.revised_plan(corrected,'geometry')
        self.assertEqual(plan['patches']['1']['image'],'l6/lantern-a-l6/front.png')
        self.assertNotIn('hunyuan-official-demo-padded.png',str(plan))

    def test_explicit_legacy_fixture_preserves_old_plan(self):
        parent,_,_,_=self.prepare('compat',self.source,current_reference=None,legacy_fixture=True)
        data=l6.read_ref(parent)
        self.assertEqual(data['input_mode'],'legacy_fixture')
        self.assertEqual(self.run_l6(parent)['status'],'PREFLIGHT_PASS')
        self.assertEqual(l6.make_plan('compat-l6','right',self.f.assets)['patches']['1']['image'],self.f.source.name)
        self.zero_effects()


class CurrentReferenceIntegrationTests(unittest.TestCase):
    def setUp(self):
        import tests.test_session_scenario_binding as integration
        self.s=integration.SessionScenarioTests()
        self.s.setUp()
        self.addCleanup(self.s.doCleanups)
        source=self.s.f.root/'new-bound-image.png'
        Image.new('RGB',(768,768),'gray').save(source)
        file=session.file_identity(source,'USER_CURRENT_REFERENCE')
        authority=bound.reference_authority(file)
        self.s.doc.write_text(self.s.doc.read_text(encoding='utf-8')+'\nReference: '+authority,encoding='utf-8')
        fields=replace(self.s.spec.fields,authority_references=self.s.spec.fields.authority_references+
                       (session.AuthorityReference('REF',authority),))
        self.s.spec=session.freeze_specification(self.s.doc,fields)
        self.s.session=session.SessionBoundary('session-test',self.s.f.root/'new-bound-session')
        self.s.binding=self.s.session.create_binding(self.s.spec,'logical-loop')
        current=bound.freeze_current_reference(self.s.binding,file,'REF')
        self.s.parent=self.s.prepare(current_reference=current,legacy_fixture=False)

    def test_current_geometry_correction_through_existing_adapters(self):
        h=self.s.correction_fixture()
        result=self.s.execute_correction(h.source)
        self.assertEqual(result['state'],'INTERNAL_ACCEPT',result)
        path=self.s.f.repo/'runs/l7'/self.s.ids['correction']
        plan=l6.read_json(path/'geometry_plan.json')
        self.assertEqual(plan['patches']['1']['image'],'l6/'+self.s.ids['l6']+'/front.png')
        self.assertNotIn('hunyuan-official-demo-padded.png',str(plan))
        bound.internal_accept_candidate(self.s.parent,path).validate()
        self.assertFalse(self.s.session.outcome.delivered)
        self.s.f.network.assert_not_called()

    def test_current_view_correction_through_existing_adapters(self):
        h=self.s.correction_fixture('right')
        result=self.s.execute_correction(h.source)
        self.assertEqual(result['state'],'INTERNAL_ACCEPT',result)
        path=self.s.f.repo/'runs/l7'/self.s.ids['correction']
        for stage in ('right','geometry'):
            plan=l6.read_json(path/(stage+'_plan.json'))
            self.assertEqual(plan['patches']['1']['image'],'l6/'+self.s.ids['l6']+'/front.png')
            self.assertNotIn('hunyuan-official-demo-padded.png',str(plan))
        bound.internal_accept_candidate(self.s.parent,path).validate()
        self.s.f.network.assert_not_called()

    def test_mutated_staged_front_blocks_correction_before_first_effect(self):
        h=self.s.correction_fixture()
        self.s.f.worker_mock.reset_mock()
        staged=self.s.f.comfy/'work/input/l6'/self.s.ids['l6']/'front.png'
        Image.new('RGB',(768,768),'blue').save(staged)
        with self.assertRaisesRegex(ValueError,'image bytes/hash/dimensions differ|file reference missing or hash differs'):
            self.s.execute_correction(h.source)
        self.s.f.worker_mock.assert_not_called()
        self.s.renderer.assert_not_called()
        self.s.reviewer.assert_not_called()
        self.s.f.network.assert_not_called()
