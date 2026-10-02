# Work Specification v1

Session: `fresh-spec-dialogue-artifact-001` · Request: `NEW_WORK` · Ready: `true`

## Goal
제공 사진 중앙의 흰색 금속 난간과 바로 아래 직사각형 콘크리트 받침을 검사 가능한 3D 메시로 제작한다. 실제 사용자 답변에 따라 연석은 제외한다. 주변 인물과 거리 환경도 자산 범위에 포함하지 않는다.

## Deliverable
설치된 Blender 5.2.0 LTS로 제작·내보낸 단일 `.glb` 자산을 제공한다. 난간과 받침은 식별 가능한 메시 및 재질 이름을 사용한다. 재현 가능한 제작 소스, 진단 이미지와 검토 기록은 실행 증거로 함께 보존한다.

## Authority
`request`, `reference`, `clarification-001`을 supplied authority_references의 내용과 순서 그대로 바인딩한다. 원요청은 3D 메시 제작을, 이미지는 보이는 형태를, 실제 답변은 난간·받침 포함 및 연석 제외를 결정한다. Skill은 제작 방법에 관한 지식이며 대상 범위나 성공 조건을 변경하지 않는다.

## Mandatory acceptance
`ACC_SCOPE`, `ACC_RAIL_FRAME`, `ACC_CENTER_CURVES`, `ACC_BASE`, `ACC_MATERIALS`, `ACC_3D`를 모두 GLB에 적용한다. 각각의 상세 조건과 권위 참조는 finalized_fields_json에 정의한다. 주요 판정 대상은 포함 범위, 난간의 비례와 관재 구조, 중앙 곡선 장식 및 빈 공간, 받침의 두 하단 개구부, 금속·콘크리트 재질 구분, 새로 가져온 메시의 입체성이다.

## Observable evidence
최종 GLB를 독립적인 새 Blender 장면에 가져와 메시·재질·bounds 지표를 기록한다. 해당 자산에서 1024×768 PNG 정면, 후면, 측면, 상부 사선 및 재질 원근 뷰를 생성한다. 정면 비교는 사진과 유사한 시점을 사용하고 카메라 차이와 형상 차이를 구분한다. 중립 재질 뷰는 구조와 빈 공간을, 내보낸 재질 뷰는 재질 구분을 확인한다. 각 필수 criterion에 증거 경로, 판정과 불확실성을 연결한다. 독립 검토가 불명확하다고 판단한 부분은 남은 예산 안에서 조정 가능한 뷰로 확인한다. 마스크나 유사도 점수는 요구하지 않는다.

## Resource Envelope
총 작업 기한은 5400초이다. 전체 상한은 production_runs 3, attempts 6, worker_calls 6, reviewer_calls 6, frontier_calls 10, diagnostic_calls 24이다. Run당 최대 2개 Attempt를 사용한다. 최초 계획, 제작과 독립 검토 후 필요할 때만 Frontier 진단과 국소 수정을 수행한다. 기존 Workflow로 해결하기 어려운 증거가 있으면 예산 안에서 Workflow를 개정하고 명시적인 새 Run을 시작할 수 있다. 첫 결과가 모든 필수 조건을 충족하면 추가 적응이나 Run 없이 종료한다. 종료된 Attempt의 증거는 보존하며 수정 결과는 새 Attempt에 기록한다. 예산 또는 기한 소진 시 미충족 조건과 함께 종료하고 자동 재개하지 않는다.

## Uncertainty and interpretation limits
사진에는 보정된 절대 크기가 없다. 명목 크기는 기술 선택으로 기록하며 실측값으로 주장하지 않는다. 보이지 않는 깊이, 후면, 관재 두께와 연결부는 사진에 보이는 구조와 일관되게 추정한다. 주요 구조와 상대 비례를 재현하되 정확한 숨은 토폴로지, 픽셀 일치, 개별 얼룩 복제나 임의의 표면 결함 수치 기준은 부과하지 않는다. 이 응답은 명세 작성이며 제작 또는 검증 실행의 증거가 아니다.

Fresh finalized authority fields:
{"acceptance_criteria":[{"authority_ref":"clarification-001","blocking_when_unmet":true,"criterion_id":"ACC_SCOPE","description":"흰색 금속 난간과 바로 아래 직사각형 콘크리트 받침을 모두 포함하고 연석을 제외한다. 배경 인물, 보도, 도로, 주변 기둥과 체인은 제작 대상에 포함하지 않는다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"ACC_RAIL_FRAME","description":"사진의 길고 낮은 난간 비례, 양끝 수직 기둥, 상단·중간·하단 수평 관재와 그 사이 열린 공간을 재현한다. 난간은 콘크리트 받침 위에 연결된 구조로 보여야 한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"ACC_CENTER_CURVES","description":"난간 중앙의 좌우로 펼쳐지는 곡선 관재와 중앙의 위로 솟는 장식 연결 형태를 재현하고, 이 관재들이 만드는 주요 빈 공간과 하부 중앙으로 모이는 배치를 사진과 대조해 확인한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"ACC_BASE","description":"난간 폭에 대응하는 길고 낮은 직사각형 콘크리트 받침, 드러난 상면과 전면, 전면 하단의 서로 떨어진 두 직사각형 개구부를 재현한다. 개구부는 단순한 검은 표면 표시가 아니라 기하학적 빈 공간으로 읽혀야 한다."},{"authority_ref":"reference","blocking_when_unmet":true,"criterion_id":"ACC_MATERIALS","description":"내보낸 자산에서 흰색 도장 금속 관재와 회백색 콘크리트 받침이 서로 다른 재질로 식별되어야 한다. 사진의 전반적인 색과 표면 인상을 반영하되 개별 얼룩의 정확한 복제는 요구하지 않는다."},{"authority_ref":"request","blocking_when_unmet":true,"criterion_id":"ACC_3D","description":"GLB를 새 장면에 가져오면 난간과 받침의 실제 메시, 입체 두께, 재질이 유지되어야 한다. 정면·측면·후면·상부 사선에서 검사 가능한 입체 자산이어야 하며 사진 평면이나 정면 전용 형상으로 대체하지 않는다."}],"authority_references":[{"reference_id":"request","source_ref":"{\"bytes\":85,\"identity\":\"original-user-request\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\authority\\\\ORIGINAL_REQUEST.txt\",\"sha256\":\"ef97302e3f172840d624f59247213d3e51d4245a13d5dc25427941296cb90607\"}"},{"reference_id":"reference","source_ref":"{\"bytes\":521608,\"identity\":\"original-user-reference\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\authority\\\\ORIGINAL_REFERENCE.png\",\"sha256\":\"bb0f71f274fc1ed2e8bbef84382aea013da6c1f0c373d512e750f576548f2c29\"}"},{"reference_id":"clarification-001","source_ref":"{\"bytes\":84,\"identity\":\"actual-user-clarification-001\",\"path\":\"D:\\\\VSCODE-WorkSpace\\\\Others\\\\Agent-Loop-Core\\\\docs\\\\adaptive\\\\fresh-spec-dialogue-artifact-proof\\\\authority\\\\USER_RESPONSE_001.txt\",\"sha256\":\"f612d3eae664aa520116d29c1ba0696f8310ef28832901b6e94771ec753b531c\"}"}],"interpretation_envelope":["절대 실측 치수는 사진에서 보정할 수 없다. 기술적으로 선택한 작업 단위와 명목 크기를 기록하고 사진의 상대 비례를 따른다.","단일 사진에서 확정할 수 없는 관재 두께, 받침 깊이, 후면과 숨은 연결부는 보이는 구조와 일관되게 추정하고 추정임을 명시한다.","참조 사진의 원근과 가림을 고려해 주요 윤곽과 빈 공간을 시각적으로 비교한다. 픽셀 일치나 보정된 재구성 정확도는 주장하지 않는다.","사진의 주요 구조와 재질 구분은 필수이다. 보이지 않는 내부 구조, 특정 토폴로지, 임의의 표면 결함 허용치나 얼룩 복제율은 요구하지 않는다.","제작 범위는 흰색 금속 난간과 콘크리트 받침이다. 연석 및 주변 환경은 제외한다."],"request_type":"NEW_WORK","session_id":"fresh-spec-dialogue-artifact-001","specification_ready":true,"specification_version":"v1","unresolved_blocking_ambiguities":[]}

{"criterion_applicability":{"glb":["ACC_SCOPE","ACC_RAIL_FRAME","ACC_CENTER_CURVES","ACC_BASE","ACC_MATERIALS","ACC_3D"]},"deliverable_type":"glb"}

{"deadline_seconds":5400,"resource_limits":{"attempts":6,"diagnostic_calls":24,"frontier_calls":10,"production_runs":3,"reviewer_calls":6,"worker_calls":6}}
