"""Fixed dimension corrective; production adapters/transport are tripwired."""
from dataclasses import replace
from io import BytesIO
from pathlib import Path
import unittest
from unittest import mock

from PIL import Image

from scenario_a import l6_pipeline as l6
from scenario_a import session_binding as bound
from scenario_a import reference_normalization as normalization
from scenario_a import l7_feedback_controller as controller
from session import session_boundary as session
from tests import test_current_reference_binding as fixtures

PROJECT = Path(__file__).resolve().parents[1]
STONE = PROJECT / 'docs/session/fresh-session-refresh-proof-retry/CURRENT_REFERENCE.png'
STONE_HASH = '9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5'


class DimensionNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.h = fixtures.CurrentReferenceTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        self.h.source.write_bytes(STONE.read_bytes())
        self.h.parent, self.h.current, self.h.boundary, self.h.binding = self.h.prepare('stone', self.h.source)
        self.h.f.review_after = self.h.tag_review

    def test_exact_failed_reference_normalization_and_l6_plans(self):
        h = self.h
        original = h.source.read_bytes()
        self.assertEqual(l6.digest(h.source), STONE_HASH)
        # Dry entry writes nothing; mocked execution exercises real normalization,
        # actual staging/plan/order/manifest validators, with zero production effects.
        self.assertEqual(h.run_l6()['status'], 'PREFLIGHT_PASS')
        h.zero_effects()
        h.f.source.unlink()  # Old fixed source must never be consulted.
        self.assertEqual(h.run_l6(execute=True)['state'], 'GEOMETRY_READY')
        run = h.f.repo / 'runs/l6/stone-l6'
        record = l6.read_json(run/'reference_staging.json')
        source = record['staged']
        self.assertEqual(record['current_reference']['file']['sha256'], STONE_HASH)
        self.assertEqual(h.source.read_bytes(), original)
        self.assertNotEqual(source['sha256'], STONE_HASH)
        self.assertEqual((source['width'], source['height']), (768, 768))
        self.assertEqual(record['normalized_execution']['sha256'], source['sha256'])
        transform = record['normalization']
        self.assertEqual(transform['original_dimensions'], [467, 539])
        self.assertEqual(transform['resized_dimensions'], [467, 539])
        self.assertEqual(transform['padding_offsets'], dict(left=150, top=114, right=151, bottom=115))
        with Image.open(source['path']) as output, Image.open(h.source) as input_image:
            self.assertEqual(output.crop((150,114,617,653)).tobytes(), input_image.tobytes())
            self.assertEqual(output.getpixel((0,0)), (255,255,255))
        for role in l6.VIEWS+('geometry',):
            plan = l6.read_json(run/(role+'_plan.json'))
            self.assertEqual(plan['patches']['1']['image'], 'l6/stone-l6/front.png')
            self.assertNotIn('hunyuan-official-demo-padded.png', str(plan))
            order = l6.read_json(run/(role+'_work_order.json'))
            front = order['inputs']['artifacts'][0] if role == 'geometry' else order['inputs']['source']
            self.assertEqual(front['sha256'], source['sha256'])
            self.assertEqual((front['width'],front['height']), (768,768))
            # The fixed VAE compression crop cannot change a 768-square input.
            self.assertEqual(tuple(d//8*8 for d in (front['width'],front['height'])), (768,768))
            self.assertEqual(order['initial_contract'], l6.reference(run/'initial.json'))
        l6.validate_current_staging(run)
        h.f.network.assert_not_called()
        h.f.process.assert_not_called()

    def test_portrait_landscape_and_large_fit_keep_all_content(self):
        for dimensions in [(137,511),(511,137),(1001,2003),(2003,1001)]:
            with self.subTest(dimensions=dimensions):
                input_image=Image.new('RGB',dimensions,'red')
                stream=BytesIO(); input_image.save(stream,format='PNG')
                payload, record=normalization.normalize_reference(stream.getvalue())
                w,h=record['resized_dimensions']
                pad=record['padding_offsets']; x,y=pad['left'],pad['top']
                self.assertEqual(record['contract']['crop'],False)
                self.assertLessEqual(abs(w/h-dimensions[0]/dimensions[1]), 1/h+1/w)
                with Image.open(BytesIO(payload)) as output:
                    self.assertEqual(output.size,(768,768))
                    self.assertEqual(output.crop((x,y,x+w,y+h)).tobytes(),Image.new('RGB',(w,h),'red').tobytes())
                    if max(dimensions)<=768:
                        self.assertEqual((w,h),dimensions)
                self.assertEqual(pad['left']+w+pad['right'],768)
                self.assertEqual(pad['top']+h+pad['bottom'],768)

    def test_already_768_identity_keeps_bytes_and_metadata(self):
        from PIL.PngImagePlugin import PngInfo
        info=PngInfo(); info.add_text('fixture','preserve-on-identity')
        stream=BytesIO(); Image.new('RGBA',(768,768),(40,80,120,150)).save(stream,format='PNG',pnginfo=info)
        original=stream.getvalue()
        payload,record=normalization.normalize_reference(original)
        self.assertEqual(payload,original)
        self.assertEqual(record['operation'],'identity')
        self.assertEqual(record['padding_offsets'],dict(left=0,top=0,right=0,bottom=0))

    def test_rgba_padding_and_transformed_metadata_policy(self):
        from PIL.PngImagePlugin import PngInfo
        info=PngInfo(); info.add_text('fixture','discard-on-transform')
        image=Image.new('RGBA',(467,539),(50,100,150,90))
        stream=BytesIO(); image.save(stream,format='PNG',pnginfo=info)
        payload,record=normalization.normalize_reference(stream.getvalue())
        with Image.open(BytesIO(payload)) as output:
            self.assertEqual(output.mode,'RGBA')
            self.assertEqual(output.getpixel((0,0)),(255,255,255,0))
            self.assertEqual(output.crop((150,114,617,653)).tobytes(),image.tobytes())
            self.assertEqual(output.info,{})

    def test_reproducible_derivative_across_distinct_session_attempts(self):
        h=self.h
        parent,_,_,_=h.prepare('stone-b',h.source)
        hashes=[]
        for reference in (h.parent,parent):
            self.assertEqual(h.run_l6(reference,execute=True)['state'],'GEOMETRY_READY')
            run=h.f.repo/'runs/l6'/l6.read_ref(reference)['child_ids']['l6']
            record=l6.read_json(run/'reference_staging.json')
            self.assertEqual(record['session_binding'],reference)
            hashes.append(record['normalized_execution']['sha256'])
        self.assertEqual(hashes[0],hashes[1])
        self.assertNotEqual(hashes[0],STONE_HASH)
        h.f.network.assert_not_called()
        h.f.process.assert_not_called()

    def test_source_mutation_rejected_before_normalization_or_effect(self):
        self.h.source.write_bytes(b'mutated')
        with mock.patch.object(normalization,'normalize_reference') as transform:
            with self.assertRaisesRegex(ValueError,'size mismatch|hash mismatch'):
                self.h.run_l6(execute=True)
            transform.assert_not_called()
        self.h.zero_effects()

    def test_namespace_collision_rejected_before_normalization(self):
        dest=self.h.f.comfy/'work/input/l6/stone-l6'
        dest.mkdir(parents=True)
        marker=dest/'front.png'; marker.write_bytes(b'protected')
        with mock.patch.object(normalization,'normalize_reference') as transform:
            with self.assertRaisesRegex(ValueError,'external namespace exists'):
                self.h.run_l6(execute=True)
            transform.assert_not_called()
        self.assertEqual(marker.read_bytes(),b'protected')
        self.h.zero_effects()

    def test_derivative_mutation_rejected_before_first_worker(self):
        original=l6.stage_current_reference
        def mutate(run,root,parent):
            ref=original(run,root,parent)
            Path(l6.read_ref(ref)['staged']['path']).write_bytes(b'changed derivative')
            return ref
        with mock.patch.object(l6,'stage_current_reference',side_effect=mutate):
            self.assertEqual(self.h.run_l6(execute=True)['state'],'FAILED')
        self.h.zero_effects()

    def test_wrong_session_spec_attempt_and_transform_records_reject(self):
        original=l6.stage_current_reference
        for label,field in [('session','current_reference'),('spec','current_reference'),
                            ('attempt','run_id'),('transform','normalization'),('identity','normalized_execution')]:
            with self.subTest(field=label):
                parent,_,_,_=self.h.prepare('wrong-'+label,self.h.source)
                def tamper(run,root,reference):
                    ref=original(run,root,reference)
                    record=l6.read_ref(ref)
                    if label=='session': record[field]['session_id']='other-session'
                    elif label=='spec': record[field]['specification_identity_sha256']='0'*64
                    elif label=='attempt': record[field]='other-attempt'
                    elif label=='transform': record[field]['contract']['crop']=True
                    else: record[field]['identity']='USER_CURRENT_REFERENCE'
                    l6.worker.write_report(Path(ref['path']),record)
                    return l6.reference(ref['path'])
                with mock.patch.object(l6,'stage_current_reference',side_effect=tamper):
                    self.assertEqual(self.h.run_l6(parent,execute=True)['state'],'FAILED')
        self.h.zero_effects()

    def test_cross_attempt_derivative_reuse_rejected_even_same_bytes(self):
        h=self.h
        self.assertEqual(h.run_l6(execute=True)['state'],'GEOMETRY_READY')
        old=l6.read_json(h.f.repo/'runs/l6/stone-l6/reference_staging.json')
        parent,_,_,_=h.prepare('cross',h.source)
        h.f.worker_mock.reset_mock(); h.f.review_mock.reset_mock()
        original=l6.stage_current_reference
        def reuse(run,root,reference):
            ref=original(run,root,reference); record=l6.read_ref(ref)
            record['normalized_execution']=old['normalized_execution']
            record['staged']=old['staged']
            l6.worker.write_report(Path(ref['path']),record)
            return l6.reference(ref['path'])
        with mock.patch.object(l6,'stage_current_reference',side_effect=reuse):
            self.assertEqual(h.run_l6(parent,execute=True)['state'],'FAILED')
        h.zero_effects()


class DimensionCorrectionPropagationTests(unittest.TestCase):
    def setUp(self):
        self.h=fixtures.CurrentReferenceIntegrationTests()
        self.h.setUp()
        self.addCleanup(self.h.doCleanups)
        s=self.h.s
        source=s.f.root/'stone-correction.png'; source.write_bytes(STONE.read_bytes())
        file=session.file_identity(source,'USER_CURRENT_REFERENCE')
        authority=bound.reference_authority(file)
        s.doc.write_text(s.doc.read_text(encoding='utf-8')+'\nCurrent stone: '+authority,encoding='utf-8')
        fields=replace(s.spec.fields,authority_references=tuple(
            session.AuthorityReference('REF',authority) if a.reference_id=='REF' else a
            for a in s.spec.fields.authority_references))
        s.spec=session.freeze_specification(s.doc,fields)
        s.session=session.SessionBoundary('session-test',s.f.root/'normalized-session', mode='SYNTHETIC')
        s.binding=s.session.create_binding(s.spec,'logical-loop')
        current=bound.freeze_current_reference(s.binding,file,'REF')
        s.parent=s.prepare(current_reference=current,legacy_fixture=False)

    def assert_lineage(self):
        s=self.h.s
        l6run=s.f.repo/'runs/l6'/s.ids['l6']
        record=l6.read_json(l6run/'reference_staging.json')
        run=s.f.repo/'runs/l7'/s.ids['correction']
        manifest=l6.read_json(run/'multiview_manifest.json')
        front=manifest['references'][0]
        self.assertEqual(front['sha256'],record['normalized_execution']['sha256'])
        self.assertEqual((front['width'],front['height']),(768,768))
        self.assertEqual(record['current_reference']['file']['sha256'],STONE_HASH)
        for role in ('right','geometry'):
            p=run/(role+'_plan.json')
            if p.exists():
                plan=l6.read_json(p)
                self.assertEqual(plan['patches']['1']['image'],'l6/'+s.ids['l6']+'/front.png')
                self.assertNotIn('hunyuan-official-demo-padded.png',str(plan))
        bound.internal_accept_candidate(s.parent,run).validate()
        self.assertFalse(s.session.outcome.delivered)
        s.f.network.assert_not_called()

    def test_l7_geometry_correction_uses_normalized_lineage(self):
        h=self.h.s.correction_fixture()
        self.assertEqual(self.h.s.execute_correction(h.source)['state'],'INTERNAL_ACCEPT')
        self.assert_lineage()

    def test_l7_view_and_geometry_correction_use_normalized_lineage(self):
        h=self.h.s.correction_fixture('right')
        self.assertEqual(self.h.s.execute_correction(h.source)['state'],'INTERNAL_ACCEPT')
        self.assert_lineage()

    def test_mutated_derivative_stops_l7_before_first_effect(self):
        h=self.h.s.correction_fixture()
        self.h.s.f.worker_mock.reset_mock()
        self.h.s.reviewer.reset_mock()
        path=self.h.s.f.comfy/'work/input/l6'/self.h.s.ids['l6']/'front.png'
        Image.new('RGB',(768,768),'blue').save(path)
        with self.assertRaises(ValueError):
            self.h.s.execute_correction(h.source)
        self.h.s.f.worker_mock.assert_not_called()
        self.h.s.reviewer.assert_not_called()
        self.h.s.f.network.assert_not_called()
