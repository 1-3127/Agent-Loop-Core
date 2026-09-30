"""L7-M2 local fixtures: every production Worker, renderer and Reviewer is mocked."""
import contextlib
import copy
import io
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
from unittest import mock

PROJECT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'src'))
from scenario_a import l7_feedback_controller as controller
from scenario_a import l7_geometry_review as bridge
import tests.test_l7_geometry_review as bridge_tests


class FeedbackControllerTests(unittest.TestCase):
    def setUp(self):
        self.fixture=bridge_tests.GeometryBridgeTests();self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        f=self.fixture;f.verdict='REVISE'
        self.assertEqual(f.execute()['state'],'GEOMETRY_REVIEWED')
        self.source=f.run_dir;self.comfy=f.fixture.comfy
        self.run_id='l7-feedback-test';self.run_dir=f.fixture.repo/'runs/l7'/self.run_id
        self.worker=f.fixture.worker_mock;self.worker.reset_mock();self.worker.side_effect=self.fake_worker
        self.renderer=f.renderer;self.renderer.reset_mock();self.renderer.side_effect=self.fake_render
        self.reviewer=f.reviewer;self.reviewer.reset_mock();self.reviewer.side_effect=self.fake_review
        for name,value in [('ROOT',f.fixture.repo),('SOURCE_DIR',self.source),('SOURCE_TERMINAL_SHA',controller.l6.digest(self.source/'terminal.json'))]:
            patch=mock.patch.object(controller,name,value);patch.start();self.addCleanup(patch.stop)
        self.final_verdict='PASS';self.multiview_verdict='PASS'
        self.worker_error=None;self.render_error=None;self.review_error=None
        self.worker_after=None;self.review_after=None;self.render_after=None
        self.old_glb=False;self.invalid_glb=False;self.invalid_png=False
        self.source_snapshot={p.name:p.read_bytes() for p in self.source.iterdir() if p.is_file()}

    def configure_source(self,verdict='REVISE',code='REGENERATE_GEOMETRY',target='geometry'):
        result=controller.read(self.source/'review_result.json')
        if verdict=='PASS':code,target='NONE',None
        if verdict=='HUMAN_REQUIRED':code,target='HUMAN_REQUIRED',None
        result.update(verdict=verdict,blocking_issues=['Synthetic blocker'] if verdict=='REVISE' else [],suggested_action={'code':code,'target':target})
        controller.l6.worker.write_report(self.source/'review_result.json',result)
        invocation=controller.read(self.source/'review_invocation.json')
        invocation.update(verdict=verdict,result_sha256=controller.l6.digest(self.source/'review_result.json'))
        controller.l6.worker.write_report(self.source/'review_invocation.json',invocation)
        terminal=controller.read(self.source/'terminal.json');terminal['review_verdict']=verdict
        terminal['records']['review_result']=controller.ref(self.source/'review_result.json')
        terminal['records']['review_invocation']=controller.ref(self.source/'review_invocation.json')
        controller.l6.worker.write_report(self.source/'terminal.json',terminal)
        controller.SOURCE_TERMINAL_SHA=controller.l6.digest(self.source/'terminal.json')

    def fake_worker(self,plan_path,report_path,comfy_root,timeout):
        if self.worker_error:raise self.worker_error
        f=self.fixture.fixture;f.worker_after=None
        code=f.fake_worker(plan_path,report_path,comfy_root,timeout)
        plan=controller.read(plan_path);role=plan['task_id'].rsplit('-',1)[-1]
        report=controller.read(report_path)
        if report['status']=='SUCCESS':
            output=Path(report['outputs'][0]['path'])
            if role=='geometry':
                graph={node:{'inputs':plan['patches'][node], 'is_changed':[controller.l6.digest(self.comfy/'work/input'/plan['patches'][node]['image'])]}
                       for node in controller.l6.MAPPING.values()}
                graph['14']={'inputs':plan['patches']['14']}
                payload=json.dumps({'asset':{'version':'2.0','extras':{'prompt':json.dumps(graph)}}}).encode()
                payload+=b' '*(-len(payload)%4)
                data=struct.pack('<4sII',b'glTF',2,20+len(payload))+struct.pack('<I4s',len(payload),b'JSON')+payload
                if self.old_glb:data=Path(controller.validate_source(self.source)['input']['artifact']['path']).read_bytes()
                output.write_bytes(data[:-1] if self.invalid_glb else data)
                report['outputs'][0].update(bytes=output.stat().st_size,sha256=controller.l6.digest(output),declared_length=len(data))
                controller.l6.worker.write_report(report_path,report)
            else:
                from PIL import Image
                Image.new('RGB',(768,768),(plan['patches']['11']['seed'] % 256,70,90)).save(output)
                if self.invalid_png:output.write_bytes(b'INVALID_SYNTHETIC_PNG')
        if self.worker_after:self.worker_after(role,plan_path,report_path)
        return code

    def fake_render(self,command,**kwargs):
        if self.render_error:raise self.render_error
        f=self.fixture;prior=f.run_id;f.run_id=controller.read(Path(command[-1]))['run_id']
        try:result=f.fake_render(command,**kwargs)
        finally:f.run_id=prior
        if self.render_after:self.render_after(command)
        return result

    def fake_review(self,request_path,result_path,report_path,**kwargs):
        if self.review_error:raise self.review_error
        f=self.fixture;f.verdict=self.multiview_verdict if 'multiview_review' in request_path.name else self.final_verdict
        f.action={'code':'MULTIVIEW_REVISE','target':'back'} if f.verdict=='REVISE' and 'multiview_review' in request_path.name else None
        result=f.fake_review(request_path,result_path,report_path,**kwargs)
        if self.review_after:self.review_after(request_path,result_path,report_path)
        return result

    def execute(self):
        return controller.run_feedback(self.run_id,self.source,self.comfy,self.fixture.executable,1,1,1,execute=True)

    def counts(self,worker,render,review):
        self.assertEqual((self.worker.call_count,self.renderer.call_count,self.reviewer.call_count),(worker,render,review))
        self.fixture.fixture.network.assert_not_called()

    def test_default_and_cli_preflight_effect_free(self):
        result=controller.run_feedback(self.run_id,self.source,self.comfy,self.fixture.executable)
        self.assertEqual(result['action'],{'code':'REGENERATE_GEOMETRY','target':'geometry'})
        self.assertEqual(result['revision_seed'],528364197559478)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as ex:controller.main(['--help'])
            self.assertEqual(ex.exception.code,0)
            for mode in ([],['--preflight']):
                self.assertEqual(controller.main(mode+['--source-review-run',str(self.source),'--comfy-root',str(self.comfy),'--blender',str(self.fixture.executable)]),0)
        self.assertFalse(self.run_dir.exists());self.counts(0,0,0)

    def test_source_pass_no_revision(self):
        self.configure_source('PASS');state=self.execute()
        self.assertEqual(state['state'],'INTERNAL_ACCEPT');self.counts(0,0,0)
        self.assertFalse((self.run_dir/'revision_action.json').exists())

    def test_source_human_no_revision(self):
        self.configure_source('HUMAN_REQUIRED');state=self.execute()
        self.assertEqual((state['state'],state['reason']),('ABORT','HUMAN_REQUIRED'));self.counts(0,0,0)

    def test_geometry_path_pass_exact_staging_seed_only_lineage(self):
        state=self.execute();self.assertEqual(state['state'],'INTERNAL_ACCEPT');self.counts(1,1,1)
        self.assertEqual([controller.read(c.args[0])['task_id'].rsplit('-',1)[-1] for c in self.worker.call_args_list],['geometry'])
        source=controller.validate_source(self.source)
        manifest=controller.read(self.run_dir/'multiview_manifest.json')
        self.assertEqual(manifest['references'],source['input']['references'])
        prior=controller.l6.read_ref(source['input']['geometry_plan']);plan=controller.read(self.run_dir/'geometry_plan.json')
        self.assertEqual(plan['patches']['14']['seed'],prior['patches']['14']['seed']+1)
        expected=copy.deepcopy(prior);expected['task_id']=self.run_id+'-geometry'
        expected['patches']['14']['seed']+=1;expected['patches']['17']['filename_prefix']='mesh/l7/'+self.run_id+'/geometry'
        for role,node in controller.l6.MAPPING.items():
            expected['patches'][node]['image']='hunyuan-official-demo-padded.png' if role=='front' else f'l7/{self.run_id}/{role}.png'
        self.assertEqual(plan,expected)
        staging=controller.read(self.run_dir/'staging.json')
        for item in staging['views']:
            self.assertEqual(Path(item['original']['path']).read_bytes(),Path(item['staged']['path']).read_bytes())
        order=controller.read(self.run_dir/'geometry_work_order.json')
        self.assertEqual(order['inputs']['artifacts'],manifest['references'])
        self.assertEqual(order['source_review'],source['result'])
        self.assertEqual(order['revision_seed'],528364197559478)
        self.assertEqual(order['previous_execution'],source['input']['geometry_execution'])
        instruction=(self.run_dir/'geometry_review_instructions.md').read_text(encoding='utf-8')
        self.assertIn('exact CURRENT geometry generation inputs',instruction);self.assertNotIn('exact L6 generation inputs',instruction)
        review=controller.read(self.run_dir/'geometry_review_request.json')
        self.assertEqual([a['role'] for a in review['artifacts']],list(bridge.ROLES))
        self.assertEqual([a['sha256'] for a in review['artifacts'][:4]],[a['sha256'] for a in manifest['references']])
        action=controller.read(self.run_dir/'revision_action.json');self.assertEqual(action['revision_ordinal'],1)
        self.assertEqual(state['budgets'],{'revision':{'limit':1,'consumed':1,'remaining':0},'worker':{'limit':2,'consumed':1,'remaining':1},
                                          'reviewer':{'limit':2,'consumed':1,'remaining':1},'renderer':{'limit':1,'consumed':1,'remaining':0}})
        self.assertFalse(state['delivered'])
        self.assertEqual(self.source_snapshot,{p.name:p.read_bytes() for p in self.source.iterdir() if p.is_file()})
        terminal=controller.read(self.run_dir/'terminal.json')
        for item in terminal['records'].values():controller.l6.reviewer.checked_ref(item)

    def test_final_revise_no_second_action(self):
        self.final_verdict='REVISE';state=self.execute()
        self.assertEqual((state['state'],state['reason']),('ABORT','REVISION_BUDGET_EXHAUSTED'));self.counts(1,1,1)
        self.assertEqual(state['budgets']['revision']['consumed'],1)

    def test_final_human_no_second_action(self):
        self.final_verdict='HUMAN_REQUIRED';state=self.execute()
        self.assertEqual((state['state'],state['reason']),('ABORT','HUMAN_REQUIRED'));self.counts(1,1,1)

    def view_path(self,target):
        self.configure_source(code='REGENERATE_VIEW',target=target)
        state=self.execute();self.assertEqual(state['state'],'INTERNAL_ACCEPT');self.counts(2,1,2)
        self.assertEqual([controller.read(c.args[0])['task_id'].rsplit('-',1)[-1] for c in self.worker.call_args_list],[target,'geometry'])
        source=controller.validate_source(self.source);images=controller.read(self.run_dir/'multiview_manifest.json')['references']
        for prior,current in zip(source['input']['references'],images):
            if current['role']==target:
                self.assertNotEqual(current['path'],prior['path']);self.assertNotEqual(current['sha256'],prior['sha256'])
            else:self.assertEqual(current,prior)
        plan=controller.read(self.run_dir/(target+'_plan.json'));prior=controller.l6.read_ref(source['view_plans'][target])
        self.assertEqual(plan['patches']['11']['seed'],prior['patches']['11']['seed']+1)
        expected=copy.deepcopy(prior);expected['task_id']=self.run_id+'-'+target;expected['patches']['11']['seed']+=1
        expected['patches']['13']['filename_prefix']=f'l7/{self.run_id}/{target}';self.assertEqual(plan,expected)
        geometry=controller.read(self.run_dir/'geometry_work_order.json');self.assertEqual(geometry['inputs']['artifacts'],images)
        instruction=(self.run_dir/'geometry_review_instructions.md').read_text(encoding='utf-8')
        self.assertIn('exact CURRENT geometry generation inputs',instruction);self.assertNotIn('exact L6 generation inputs',instruction)
        mv=controller.read(self.run_dir/'multiview_review_request.json');final=controller.read(self.run_dir/'geometry_review_request.json')
        self.assertEqual([a['sha256'] for a in mv['artifacts']],[a['sha256'] for a in images])
        self.assertEqual([a['sha256'] for a in final['artifacts'][:4]],[a['sha256'] for a in images])
        self.assertEqual(geometry['inputs']['approved_review'],controller.ref(self.run_dir/'multiview_review_result.json'))
        for item in controller.read(self.run_dir/'staging.json')['views']:
            self.assertEqual(Path(item['original']['path']).read_bytes(),Path(item['staged']['path']).read_bytes())
        self.assertEqual(state['budgets']['worker']['consumed'],2);self.assertEqual(state['budgets']['reviewer']['consumed'],2)

    def test_view_right(self):self.view_path('right')
    def test_view_left(self):self.view_path('left')
    def test_view_back(self):self.view_path('back')

    def test_multiview_revise_stops_geometry(self):
        self.configure_source(code='REGENERATE_VIEW',target='back');self.multiview_verdict='REVISE';state=self.execute()
        self.assertEqual((state['state'],state['reason']),('ABORT','REVISION_BUDGET_EXHAUSTED'));self.counts(1,0,1)
        self.assertFalse((self.run_dir/'geometry_plan.json').exists())

    def test_multiview_human_stops_geometry(self):
        self.configure_source(code='REGENERATE_VIEW',target='right');self.multiview_verdict='HUMAN_REQUIRED';state=self.execute()
        self.assertEqual((state['state'],state['reason']),('ABORT','HUMAN_REQUIRED'));self.counts(1,0,1)

    def test_source_result_hash_mutation(self):
        with (self.source/'review_result.json').open('ab') as stream:stream.write(b' ')
        with self.assertRaisesRegex(ValueError,'hash'):controller.preflight(self.source,self.comfy,self.fixture.executable)
        self.counts(0,0,0)

    def test_source_invocation_mismatch(self):
        report=controller.read(self.source/'review_invocation.json');report['request_sha256']='0'*64
        controller.l6.worker.write_report(self.source/'review_invocation.json',report)
        terminal=controller.read(self.source/'terminal.json');terminal['records']['review_invocation']=controller.ref(self.source/'review_invocation.json')
        controller.l6.worker.write_report(self.source/'terminal.json',terminal);controller.SOURCE_TERMINAL_SHA=controller.l6.digest(self.source/'terminal.json')
        with self.assertRaisesRegex(ValueError,'invocation'):controller.preflight(self.source,self.comfy,self.fixture.executable)
        self.counts(0,0,0)

    def test_source_terminal_run_mismatch(self):
        terminal=controller.read(self.source/'terminal.json');terminal['run_id']='wrong'
        controller.l6.worker.write_report(self.source/'terminal.json',terminal);controller.SOURCE_TERMINAL_SHA=controller.l6.digest(self.source/'terminal.json')
        with self.assertRaisesRegex(ValueError,'terminal/run'):controller.preflight(self.source,self.comfy,self.fixture.executable)
        self.counts(0,0,0)

    def test_old_glb_replay_rejected(self):
        self.old_glb=True;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,0,0)

    def test_invalid_glb(self):
        self.invalid_glb=True;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,0,0)

    def test_invalid_view_png(self):
        self.configure_source(code='REGENERATE_VIEW',target='back');self.invalid_png=True
        state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,0,0)

    def test_known_worker_failure_no_refund(self):
        self.fixture.fixture.worker_status['geometry']='FAILED';state=self.execute()
        self.assertEqual((state['state'],state['reason']),('FAILED','REVISION_WORKER_STAGE'));self.counts(1,0,0)
        self.assertEqual(state['budgets']['worker']['consumed'],1)

    def test_uncertain_worker_no_resume_retry(self):
        self.fixture.fixture.worker_status['geometry']='UNRESOLVED';state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,0,0)
        with self.assertRaisesRegex(ValueError,'ALREADY_EXISTS'):self.execute()
        self.counts(1,0,0)

    def test_worker_transport_uncertain(self):
        self.worker_error=OSError('synthetic transport uncertainty');state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,0,0)
        self.assertEqual(state['budgets']['worker']['consumed'],1)

    def test_renderer_timeout(self):
        self.render_error=subprocess.TimeoutExpired('synthetic-blender',1);state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,1,0)
        self.assertEqual(state['budgets']['renderer']['consumed'],1)

    def test_renderer_failure(self):
        self.fixture.return_code=1;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,1,0)

    def test_reviewer_timeout(self):
        self.review_error=subprocess.TimeoutExpired('synthetic-reviewer',1);state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,1,1)
        self.assertEqual(state['budgets']['reviewer']['consumed'],1)

    def test_reviewer_known_failure(self):
        def mutate(req,res,report):
            data=controller.read(report);data['invocation_status']='FAILED';controller.l6.worker.write_report(report,data)
        self.review_after=mutate
        # The callable must return the same durable status, as the existing adapter does.
        original=self.fake_review
        def failed(*args,**kwargs):original(*args,**kwargs);return controller.read(args[2])
        self.reviewer.side_effect=failed;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,1,1)

    def test_malformed_review_uncertain(self):
        self.review_after=lambda req,res,report:res.write_text('{invalid',encoding='utf-8')
        state=self.execute();self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,1,1)

    def test_final_reference_mutation_blocks_reviewer(self):
        def mutate(command):
            item=controller.read(self.run_dir/'staging.json')['views'][0]['staged']
            Path(item['path']).write_bytes(b'mutated-staged-PNG')
        self.render_after=mutate;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,1,0)

    def test_terminal_reentry_no_effect_and_no_writes(self):
        self.execute();snapshot={p.name:p.read_bytes() for p in self.run_dir.iterdir()}
        self.assertEqual(self.execute()['status'],'ALREADY_TERMINAL')
        for call in (lambda:controller.reserve(self.run_dir,'revision',self.run_dir/'revision_action.json'),
                     lambda:controller.run_worker(self.run_dir,'geometry',1),lambda:controller.run_renderer(self.run_dir,1),
                     lambda:controller.run_review(self.run_dir,'geometry',1)):
            with self.assertRaisesRegex(ValueError,'ALREADY_TERMINAL'):call()
        self.assertEqual(snapshot,{p.name:p.read_bytes() for p in self.run_dir.iterdir()});self.counts(1,1,1)

    def test_reservation_bypass_and_second_action_rejected(self):
        def probe(role,plan,report):
            for stage in ('revision','geometry'):
                with self.assertRaisesRegex(ValueError,'STAGE_ALREADY_RESERVED'):
                    controller.reserve(self.run_dir,stage,controller.stage_path(self.run_dir,stage))
                with self.assertRaisesRegex(ValueError,'alternate'):
                    controller.reserve(self.run_dir,stage,self.run_dir/'alternate.json')
            with self.assertRaisesRegex(ValueError,'unknown'):
                controller.reserve(self.run_dir,'another_action',self.run_dir/'alternate.json')
        self.worker_after=probe;self.assertEqual(self.execute()['state'],'INTERNAL_ACCEPT');self.counts(1,1,1)

    def test_incomplete_namespace_rejected(self):
        self.run_dir.mkdir(parents=True)
        with self.assertRaisesRegex(ValueError,'ALREADY_EXISTS'):self.execute()
        self.counts(0,0,0)

    def test_unknown_usage_null(self):
        self.execute();usage=controller.read(self.run_dir/'usage.json')
        self.assertTrue(all(x is None for x in usage['frontier'].values()));self.assertEqual(usage['automatic_retries'],0)
        self.assertEqual(usage['workers'][0]['invocations'],1);self.assertEqual(usage['reviewers'][0]['invocations'],1)
        self.assertEqual(usage['renderer']['invocations'],1)


    def test_work_order_reference_mismatch_blocks_worker(self):
        original=controller.publish_order
        def mutate(run_dir,role):
            path=original(run_dir,role);order=controller.read(path)
            order['inputs']['artifacts'][1]['sha256']='0'*64
            controller.l6.worker.write_report(path,order);return path
        with mock.patch.object(controller,'publish_order',side_effect=mutate):state=self.execute()
        self.assertEqual(state['state'],'FAILED');self.counts(0,0,0)

    def test_embedded_glb_wrong_reference_rejected(self):
        def mutate(role,plan_path,report_path):
            report=controller.read(report_path);path=Path(report['outputs'][0]['path'])
            data=path.read_bytes();length,kind=struct.unpack_from('<I4s',data,12)
            body=json.loads(data[20:20+length]);graph=json.loads(body['asset']['extras']['prompt'])
            graph['4']['is_changed']=['0'*64];body['asset']['extras']['prompt']=json.dumps(graph)
            payload=json.dumps(body).encode();payload+=b' '*(-len(payload)%4)
            data=struct.pack('<4sII',b'glTF',2,20+len(payload))+struct.pack('<I4s',len(payload),kind)+payload
            path.write_bytes(data);report['outputs'][0].update(bytes=len(data),sha256=controller.l6.digest(path),declared_length=len(data))
            controller.l6.worker.write_report(report_path,report)
        self.worker_after=mutate;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,0,0)
        self.assertIn('embedded current references',state['errors'][0])

    def test_view_path_old_final_reference_rejected(self):
        self.configure_source(code='REGENERATE_VIEW',target='back')
        original=controller.prepare_review
        def mutate(run_dir,kind):
            request=original(run_dir,kind)
            if kind=='geometry':
                prior=controller.validate_source(self.source)['input']['references'][3]
                request['artifacts'][3]['path']=prior['path'];request['artifacts'][3]['sha256']=prior['sha256']
                controller.l6.worker.write_report(run_dir/'geometry_review_request.json',request)
            return request
        with mock.patch.object(controller,'prepare_review',side_effect=mutate):state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(2,1,1)

    def test_source_mutation_after_worker_stops_and_records_failure(self):
        self.worker_after=lambda role,plan,report:(self.source/'review_result.json').write_bytes(b'changed source fixture')
        state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,0,0)
        self.assertTrue((self.run_dir/'terminal.json').exists())

    def test_revision_record_seed_mutation_stops_before_worker(self):
        original=controller.reserve
        def mutate(run_dir,stage,path):
            original(run_dir,stage,path)
            if stage=='revision':
                record=controller.read(path);record['revision_seed']+=1;controller.l6.worker.write_report(path,record)
        with mock.patch.object(controller,'reserve',side_effect=mutate):state=self.execute()
        self.assertEqual((state['state'],state['reason']),('FAILED','REVISION_POLICY'));self.counts(0,0,0)

    def test_multiview_timeout_stops_before_geometry(self):
        self.configure_source(code='REGENERATE_VIEW',target='left')
        self.review_error=subprocess.TimeoutExpired('synthetic-reviewer',1);state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,0,1)
        self.assertEqual(state['budgets']['reviewer']['consumed'],1)


    def test_execute_invalid_source_durable_zero_effect_failure(self):
        (self.source/'review_result.json').write_bytes(b'invalid source fixture')
        state=self.execute();self.assertEqual((state['state'],state['reason']),('FAILED','SOURCE_REVIEW_INVALID'))
        self.counts(0,0,0);self.assertTrue((self.run_dir/'terminal.json').exists())
        self.assertTrue(all(b['consumed']==0 for b in state['budgets'].values()))
        self.assertEqual(self.execute()['status'],'ALREADY_TERMINAL');self.counts(0,0,0)

    def test_invalid_seed_execute_durable_zero_effect_failure(self):
        with mock.patch.object(controller,'next_seed',side_effect=controller.l6.StageFailure('FAILED','REVISION_POLICY')):
            state=self.execute()
        self.assertEqual((state['state'],state['reason']),('FAILED','REVISION_POLICY'));self.counts(0,0,0)


    def test_alternate_review_identity_blocked_before_process(self):
        original=controller.prepare_review
        def mutate(run_dir,kind):
            request=original(run_dir,kind);request['review_id']='alternate-review-id'
            controller.l6.worker.write_report(run_dir/(kind+'_review_request.json'),request);return request
        with mock.patch.object(controller,'prepare_review',side_effect=mutate):state=self.execute()
        self.assertEqual(state['state'],'UNRESOLVED');self.counts(1,1,0)
        self.assertEqual(state['budgets']['reviewer']['consumed'],0)

    def test_incomplete_render_set_rejected_before_review(self):
        def mutate(command):
            path=self.run_dir/'render_manifest.json';manifest=controller.read(path);manifest['outputs'].pop()
            controller.l6.worker.write_report(path,manifest)
        self.render_after=mutate;state=self.execute();self.assertEqual(state['state'],'FAILED');self.counts(1,1,0)


    def test_invalid_action_execute_revision_policy_zero_effect(self):
        self.configure_source(code='REGENERATE_VIEW',target='front')
        state=self.execute();self.assertEqual((state['state'],state['reason']),('FAILED','REVISION_POLICY'));self.counts(0,0,0)


class ActionPolicyTests(unittest.TestCase):
    def test_seed_validation_and_overflow(self):
        self.assertEqual(controller.next_seed(29481),29482)
        self.assertEqual(controller.next_seed(528364197559477),528364197559478)
        for seed in (True,False,-1,None,'1',1.5,2**64-1,2**64):
            with self.subTest(seed=seed),self.assertRaises(controller.l6.StageFailure):controller.next_seed(seed)

    def test_action_vocabulary_and_no_free_text_planning(self):
        for code,target in [('REGENERATE_GEOMETRY','geometry')]+[('REGENERATE_VIEW',r) for r in controller.l6.VIEWS]:
            result={'verdict':'REVISE','blocking_issues':['regenerate all inputs'], 'suggested_action':{'code':code,'target':target}}
            self.assertEqual(controller.resolve_action(result),result['suggested_action'])
        for code,target in [('REGENERATE_VIEW','front'),('REGENERATE_VIEW','all'),('REGENERATE_VIEW',None),('REGENERATE_VIEW',['right']),
                            ('REGENERATE_GEOMETRY','right'),('UNRECOGNIZED','geometry'),('NONE',None)]:
            with self.subTest(code=code,target=target),self.assertRaises(ValueError):
                controller.resolve_action({'verdict':'REVISE','blocking_issues':['REGENERATE_GEOMETRY geometry'], 'suggested_action':{'code':code,'target':target}})
        with self.assertRaises(ValueError):controller.resolve_action({'verdict':'PASS','blocking_issues':['blocker'],'suggested_action':{'code':'NONE','target':None}})


class ActualSourcePreflightTests(unittest.TestCase):
    def test_actual_m1_static_preflight_effect_zero(self):
        with mock.patch.object(controller.l6.worker,'run',side_effect=AssertionError('production Worker forbidden')) as worker, \
             mock.patch.object(controller.subprocess,'run',side_effect=AssertionError('production process forbidden')) as process, \
             mock.patch.object(controller.l6.worker,'request_json',side_effect=AssertionError('production transport forbidden')) as network, \
             mock.patch.object(controller.l6.reviewer,'review_once',side_effect=AssertionError('production review forbidden')) as review:
            result=controller.preflight()
            self.assertEqual(result['action'],{'code':'REGENERATE_GEOMETRY','target':'geometry'})
            self.assertEqual(result['source']['previous_geometry_seed'],528364197559477)
            self.assertEqual(result['revision_seed'],528364197559478)
            self.assertEqual(result['effects'],{'comfy':0,'blender':0,'frontier':0})
            for effect in (worker,process,network,review):effect.assert_not_called()


if __name__=='__main__':unittest.main()
