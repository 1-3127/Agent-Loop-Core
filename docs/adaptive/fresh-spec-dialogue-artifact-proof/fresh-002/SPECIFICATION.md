# Work Specification v1

Session: `fresh-spec-dialogue-artifact-002` · Request: `NEW_WORK` · Specification ready: true

## Goal
첨부 사진 중앙의 흰색 금속 난간과 그 아래 콘크리트 받침을 함께 입체 메쉬로 제작한다. 아래 연석과 양옆에 연결된 노란색 사슬은 제외한다. 주변 사람·도로·보도·건물·별도 기둥은 제작 대상에 포함하지 않는다.

## Authority
제공된 권한 기록을 `request`, `reference`, `clarification-001` 순서로 그대로 보존한다. 원문은 중앙 대상의 3D 메쉬 제작을 요구하고, 사진은 보이는 구조의 근거이며, 실제 사용자 답변은 난간·받침 포함 및 연석·노란 사슬 제외를 확정한다. 이전 미동결 초안과 Skill은 추가 의도 권한이 아니다.

## Deliverable
제공된 Blender 5.2.0 LTS 런타임에서 제작·내보내기 가능한 정적 `glb` 한 개. 난간과 받침은 각각 식별 가능한 입체 메쉬와 구별되는 재질을 포함한다. 명명·구성·제작 기법은 실행자가 결정한다. 최종 GLB는 새 장면에서 독립적으로 가져와 검사할 수 있어야 한다.

## Mandatory acceptance
`finalized_fields_json`의 C01–C07을 모두 적용한다. 필수 기준은 정확한 포함·제외 범위, 수평·수직 관재와 열린 공간, 중앙 부채꼴 곡선 배치, 콘크리트 받침과 두 하단 파임, 난간·받침의 연결 및 상대 비례, 금속·콘크리트 재질 구별, 독립적으로 검사 가능한 입체 GLB이다. 내보내기 성공만으로 형상 기준 충족을 판정하지 않는다.

## Observable evidence
실행 시 최종 GLB를 새 장면에 독립적으로 가져오고 메쉬·재질·경계 크기 진단을 기록한다. 검사용 전면·측면·후면·재질 원근 PNG를 1024×768로 생성하는 방식을 선택한다. 전면과 원근 뷰로 사진의 주요 구조·빈 공간·재질을 비교하고, 측면과 후면으로 추론한 두께와 입체 구성을 검사한다. 독립 검토는 C01–C07 각각의 관찰 근거와 충족 여부를 기록한다. 후면 뷰는 원본 후면과의 일치를 증명하지 않는다. 마스크나 픽셀 일치 점수는 요구하지 않는다.

## Interpretation limits
보정된 절대 크기는 없다. 전체 폭 3.0 m는 작업용 가정이며 상대 비례를 우선한다. 보이지 않는 두께·후면·내부 연결은 합리적으로 추론하고 그 사실을 기록한다. 두 파임의 관통 여부, 숨겨진 토폴로지, 특정 폴리곤 수, 개별 얼룩의 정확한 복제는 수락 조건이 아니다. 관찰 가능한 주요 구조와 재질 구별을 기준으로 판단한다.

## Resource Envelope
총 작업 기한은 5400초이다. 전체 작업 상한은 production_runs 3, attempts 7, worker_calls 10, reviewer_calls 8, frontier_calls 16, diagnostic_calls 20이다. 최초 계획·Run 시작·제작·독립 검토를 허용하며, 검토에서 결함이 발견된 경우에만 근거에 따른 Frontier 진단과 국소 수정을 진행한다. Workflow 변경이 필요하면 변경 결정을 기록하고 명시적인 새 Run에서 다음 Attempt를 진행한다. 각 Run과 Attempt는 별도 식별자를 사용하고 이전 증거를 보존한다. 예산은 복수 Run과 수정·재검토·최종 수락 경로를 허용한다. 최초 결과가 통과하면 적응이나 추가 Run을 강제하지 않는다. 기한 또는 호출 상한에 도달하면 미충족 기준을 보고하고 완료로 선언하지 않는다.

## Execution knowledge
검토된 `blender-modeling-workflow`를 재사용한다. 제공된 reference → glb 제작 지식과 독립 fresh-import 진단 경로가 충분하므로 새 Skill은 요구하지 않는다. 이 지식은 구현을 지원하며 Goal이나 사용자 범위를 변경하지 않는다.

Fresh finalized authority fields:
{"acceptance_criteria":[{"authority_ref":"clarification-001","blocking_when_unmet":true,"criterion_id":"C01","description":"흰색 금속 난간과 콘크리트 받침을 모두 제작하고, 아래 연석과 양옆에 연결된 노란색 사슬은 제외한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"C02","description":"난간의 가로로 긴 비례, 양끝 수직 지지대, 상단·중간·하단 수평 관재와 열린 내부 공간이 사진의 주요 구조로 식별된다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"C03","description":"난간 중앙의 부채꼴 곡선 관재와 중앙 수직 관재를 재현하며, 곡선들이 하단 중앙으로 모이는 배치와 주변 빈 공간을 유지한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"C04","description":"받침은 난간 아래의 길고 낮은 직사각형 콘크리트 덩어리로 재현한다. 드러난 상단 면과 전면 하단의 두 직사각형 파임이 식별되어야 하며, 파임의 관통 여부는 요구하지 않는다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"C05","description":"난간이 받침 위에 놓이고 양끝 지지대가 받침에 연결된 구조로 읽힌다. 난간·받침의 상대 폭과 높이 및 중앙 장식 위치가 사진의 주요 관계를 유지한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"C06","description":"내보낸 결과에서 흰색 도장 금속 난간과 회백색 콘크리트 받침이 서로 다른 재질로 식별된다. 개별 얼룩이나 작은 색점의 정확한 복제는 요구하지 않는다."},{"authority_ref":"request","blocking_when_unmet":true,"criterion_id":"C07","description":"최종 GLB는 새 장면에서 독립적으로 가져올 수 있고, 여러 방향에서 검사 가능한 난간과 받침의 실제 입체 메쉬 및 재질을 포함한다. 사진 평면만으로 대체하지 않는다."}],"authority_references":[{"reference_id":"request","source_ref":"{\"bytes\":85,\"identity\":\"original-user-request\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\fresh-002\\\\authority\\\\ORIGINAL_REQUEST.txt\",\"sha256\":\"ef97302e3f172840d624f59247213d3e51d4245a13d5dc25427941296cb90607\"}"},{"reference_id":"reference","source_ref":"{\"bytes\":521608,\"identity\":\"original-user-reference\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\fresh-002\\\\authority\\\\ORIGINAL_REFERENCE.png\",\"sha256\":\"bb0f71f274fc1ed2e8bbef84382aea013da6c1f0c373d512e750f576548f2c29\"}"},{"reference_id":"clarification-001","source_ref":"{\"bytes\":184,\"identity\":\"actual-user-clarification-001\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\fresh-002\\\\authority\\\\USER_RESPONSE_001.txt\",\"sha256\":\"1a1215860356b33d6eaa3edba45e0c96a54100846eaad540e540c2701dd78cea\"}"}],"interpretation_envelope":["사진에는 보정된 절대 치수가 없다. 전체 폭 3.0 m를 작업용 가정으로 사용하되 실측값이나 정확도 보증으로 취급하지 않고 사진의 상대 비례를 우선한다.","보이지 않는 두께·후면·내부 연결은 입체 메쉬 구성에 필요한 범위에서 추론하며, 사진에서 확인된 사실로 주장하지 않는다.","전면 하단 두 파임의 보이는 입구 형태를 재현한다. 숨겨진 깊이와 관통 여부는 확정하지 않는다.","단일 원근 사진에 대한 픽셀 일치, 보정된 카메라 정확도, 숨겨진 토폴로지 또는 특정 메쉬 밀도를 수락 조건으로 요구하지 않는다.","작은 색점·얼룩·불명확한 부착물은 정밀 복제 기준으로 삼지 않는다. 관찰 가능한 주요 구조와 금속·콘크리트 재질 구별을 기준으로 판단한다.","원문·사진·실제 사용자 답변이 대상 권한이다. Skill과 이전 미동결 초안은 사용자 의도를 추가하거나 변경하지 않는다."],"request_type":"NEW_WORK","session_id":"fresh-spec-dialogue-artifact-002","specification_ready":true,"specification_version":"v1","unresolved_blocking_ambiguities":[]}

{"criterion_applicability":{"glb":["C01","C02","C03","C04","C05","C06","C07"]},"deliverable_type":"glb"}

{"deadline_seconds":5400,"resource_limits":{"attempts":7,"diagnostic_calls":20,"frontier_calls":16,"production_runs":3,"reviewer_calls":8,"worker_calls":10}}
