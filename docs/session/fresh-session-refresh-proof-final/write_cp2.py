import pathlib,json,sys,subprocess,shutil
ROOT=pathlib.Path(r'D:\VSCODE-WorkSpace\Others\Agent-Loop-Core')
WORK=pathlib.Path(__file__).resolve().parent
PROOF=ROOT/'docs/session/fresh-session-refresh-proof-final'
sys.path.insert(0,str(ROOT/'src'))
from scenario_a import l6_pipeline as l6
prepared=l6.read_json(PROOF/'PREPARED_BINDING.json')
validation=l6.read_json(PROOF/'ACTUAL_VALIDATION.json')
baseline=l6.read_json(PROOF/'starting_snapshot.json')
ids=prepared['ids']
cp1=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),'rev-parse','HEAD'],encoding='utf-8').strip()
assert cp1=='5b0be678abf53aad7a7689c18860eb121d54a8c8'
refs=subprocess.check_output(['git','-c','safe.directory='+str(ROOT),'-C',str(ROOT),'show-ref'],encoding='utf-8').strip()
old={line.split()[1]:line.split()[0] for line in baseline['protected_refs'].splitlines()}
new={line.split()[1]:line.split()[0] for line in refs.splitlines()}
assert all(new.get(name)==value for name,value in old.items() if name!='refs/heads/fresh-session-refresh-proof-final')
assert validation['proof_verdict']=='RUNTIME_FAILED' and validation['counts']=={'worker':3,'comfy_submissions':3,'blender':0,'production_semantic_reviewer':1,'correction':0,'delivery':0}
invocation=validation['reviewers'][0]['invocation']
assert invocation['process_exit_code']==1 and invocation['invocation_status']=='FAILED'
assert invocation['stdout_sha256']=='e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'
for history in validation['histories']:
    assert history['status']['status_str']=='success' and history['status']['completed'] is True
assert len(validation['actual_images'])==3 and all((x['width'],x['height'])==(768,768) for x in validation['actual_images'])
for name in ('collect_result.py','write_cp2.py','freeze_cp1.py','actual_execution.log'):
    shutil.copyfile(WORK/name,PROOF/name)
review_path=ROOT/'runs/l6'/ids['l6']/'review_result.json'
cp2={'time':l6.now(),'proof_verdict':'RUNTIME_FAILED','entry_state':'FAILED','failed_stage':'REVIEW_STAGE','cp1':cp1,'new_ids':ids,'production_entry_calls':1,'canonical_reviewer_invocation':invocation,'review_result_bytes':review_path.stat().st_size,'final_semantic_verdict':None,'root_cause':'Unknown beyond actual Codex CLI exit 1 and empty stdout. Unchanged adapter preserves stderr SHA only, not stderr text; do not infer image transfer success or underlying policy/network/auth cause. No production or image diagnostic rerun.','counts':validation['counts'],'normalization_actual_verified':True,'history_success_count':3,'all_current_views_768_square':True,'internal_accept':False,'source_test_changes':0,'historical_tracked_files_unchanged':len(baseline['tracked_hashes']),'protected_local_refs_unchanged':True,'previous_state_reused':False,'same_session_reruns':0,'delivery':False,'push_required':True}
l6.write_once(PROOF/'CP2_RESULT.json',cp2)
rows=[
('최종 verdict','RUNTIME_FAILED / FAILED / REVIEW_STAGE; FRESH SESSION / REFRESH PROOF = NOT VERIFIED'),
('시작 branch / HEAD','stabilization-reference-dimension-normalization / 5b1a3c8a918cb9fcabaa7c7c7824b3755b2e5a2c; clean; local = tracking = live remote 확인'),
('새 proof branch','fresh-session-refresh-proof-final'),
('Request 해석','직접 첨부 석등의 주요 실루엣과 실제 중앙 사각 개구부를 가진 3D GLB. 사람·앞 기둥·배경은 비대상. 가려진 측면은 합리적 추론.'),
('질문','결정적 Specification ambiguity 없음; 질문 0'),
('Reference original',prepared['original']['sha256']+'; 362412 bytes; 467×539 RGB; 현재 첨부 원본이 authority'),
('Normalized execution',prepared['normalization']['normalized_sha256']+'; 273422 bytes; 768×768 RGB'),
('Transform','centered padding: left150/top114/right151/bottom115; 원본 467×539 픽셀 불변; upscale/crop/stretch 0'),
('Session',ids['session']),('Loop',ids['loop']),('L6',ids['l6']),('bridge',ids['bridge']+' (예약 ID만; 미실행)'),('correction',ids['correction']+' (예약 ID만; 미실행)'),
('Frozen Specification','FROZEN_WORK_SPECIFICATION_v1.md; identity SHA '+prepared['specification_identity_sha256']+'; 새 독립 작성; 이전 candidate/Spec 복사 0'),
('Stage applicability','multiview: MV_SILHOUETTE, MV_OPENING; geometry: GEO_SILHOUETTE, GEO_OPENING. 모두 mandatory. 이미지 외관과 실제 geometry 구멍을 분리해 C-01 적용.'),
('namespace/runtime readiness','I-03: 3 repository child / 7 external namespace absent. Canonical preflight PASS; ComfyUI live, 4 workflow pins / 6 model size, required node registration, Blender version, ChatGPT auth 및 no-image CLI transport 확인.'),
('회귀검증','244개 검증 완료: 초기 full discovery 243 PASS + Windows audit 래퍼 import-only 오류1; 해당 기존 test targeted rerun1 PASS. source/test 변경0. 단일 clean full-run PASS로 표현하지 않음. 초기 로그/결과 보존.'),
('실제 lineage','원본→CurrentReference→Frozen Spec→binding→Scenario→normalization record→attempt-local front.png→Work Order→3 real POST 모두 검증. old fixed source fallback0.'),
('실제 호출 수','Worker3 / ComfyUI3 / Blender0 / production semantic Reviewer1 / correction0 / Delivery0. 별도 no-image readiness transport1은 production Review 수에 포함하지 않음.'),
('실제 PNG/history','right/left/back 모두 실제 history success·completed, PNG decode·hash·768×768 확인; ACTUAL_VALIDATION.json과 comfy_history 및 artifact_archive 참조'),
('Reviewer 실패','CODEX_CLI process_started=true; CHATGPT_ACCOUNT; exit_code1; stdout empty; invocation FAILED; result file0 bytes; 최종 semantic verdict 없음'),
('stderr 및 원인 한계','stderr SHA '+invocation['stderr_sha256']+'; 기존 adapter가 원문을 보존하지 않아 하위 원인 미확인. 전송 성공·policy/auth/network 원인 추정하지 않음.'),
('INTERNAL_ACCEPT','미도달; geometry Worker/Blender stage로 진입하지 않음; mandatory criteria SATISFIED 미생성'),
('종료','canonical entry1회; Session terminal FAILED; same-Session 재실행0; 숨은 retry0; workaround0; source/test/contract 수정0'),
('역사 보존',str(len(baseline['tracked_hashes']))+' starting tracked files byte hash 불변; 기존 local refs 불변(새 proof branch 제외); 이전 Session/Loop/Review/current reasoning state 재사용0'),
('CP1',cp1+' — docs(proof): freeze final fresh-session stone-lantern readiness; generation0'),
('CP2 / push','이 결과와 raw 증거를 정상 commit/push한다. CP2 hash와 publication 후 local/tracking/live equality 및 clean tree는 별도 FINAL_PUBLICATION.json으로 실제 확인.'),
]
report='# Fresh Session / Refresh Proof Final — 실제 결과\n\n2026-10-01 (Asia/Seoul). **RUNTIME_FAILED / REVIEW_STAGE. INTERNAL_ACCEPT 미도달.**\n\n정규화된 실제 입력과 세 실제 view의 768×768 contract는 확인됐다. multiview semantic Reviewer가 exit1로 실패해 판정을 생성하지 못했다. geometry·correction·Delivery는 실행하지 않았으며 단일 attempt를 종료했다.\n\n| 항목 | 확인 결과 |\n|---|---|\n'+'\n'.join('| '+k+' | '+v.replace('\n',' ')+' |' for k,v in rows)+'\n\n별도 private PNG readiness 진단은 자동 승인 검토가 일반 proof 권한이 별도 진단 전송까지 명확히 포함하지 않는다는 이유로 거부했다. 해당 진단은 미실행했고 이를 우회하지 않았다. 실제 요청된 canonical production entry는 별도로 승인되어 1회 실행됐다. no-image readiness transport 결과는 production semantic Review 성공으로 대체하지 않는다.\n\n현재 증거: PREPARED_BINDING.json, CP1_READINESS.json, CP2_RESULT.json, ACTUAL_ENTRY_RESULT.json, ACTUAL_VALIDATION.json, CURRENT_EVIDENCE_INDEX.json, pre_submission_1/2/3.json, comfy_history/, artifact_archive/ 및 새 runs/session·runs/l6 기록.\n\nGit diff whitespace 검사는 Windows CR-at-EOL을 인정하는 per-command 설정으로 PASS. 전역 설정·Git history 수정은 0. 최초 기본 whitespace 검사에서 CRLF를 trailing-whitespace로 표시한 결과는 bytes나 bound identity를 변경하여 해결하지 않았다.\n'
with (PROOF/'FINAL_RESULT.md').open('x',encoding='utf-8',newline='\n') as stream: stream.write(report)
print(json.dumps({'result':'RUNTIME_FAILED','cp1':cp1,'current_tracked_unchanged':len(baseline['tracked_hashes']),'history_success':3,'reviewer_exit':1,'production_counts':validation['counts']}),flush=True)
