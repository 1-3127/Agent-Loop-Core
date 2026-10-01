# Fresh Session — Stone Lantern Work Specification Candidate

작성일: 2026-10-01 (Asia/Seoul)

**CANDIDATE ONLY / NOT FROZEN / NOT EXECUTION READY**

현재 요청의 의미는 충분히 정리됐다. 그러나 canonical production entry가 새 Reference를 받지 못하므로, 이 문서를 execution-ready Frozen Specification이나 실제 새 Session binding으로 표시하지 않는다. 이전 penguin Specification을 복사하거나 재사용하지 않았다.

## Request / Reference / Goal

- Request type: NEW_WORK.
- 원문: “레퍼런스 이미지에 있는 석등을 제작하라. 석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.”
- 직접 Reference: `C:\Users\Worker\AppData\Local\Temp\codex-clipboard-db8b9907-3c93-42cd-ac7e-8d6906652f45.png`.
- Reference SHA-256: `9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5`.
- Authority: USER_CURRENT_REQUEST는 제작 대상 및 중앙 사각 개구부의 명확성에 대한 권위다. USER_CURRENT_REFERENCE는 보이는 주요 형태와 비율에 대한 권위다.
- Goal: 사진 속 석등 자체를 식별 가능한 3D 형태로 제작한다.
- [추론] 현재 Scenario A의 Single Image → Multiview → 3D capability에 맞춰 주 산출물은 GLB 1개로 해석한다. 사용 플랫폼·실측 크기·성능 예산은 미지정이며 이번 시각적 acceptance에 필요하지 않다.

## Deliverable / Must-Have

- Planned primary output: 석등 GLB 1개. Planned supporting evidence: front/right/left/back 이미지, GLB에서 렌더한 geometry diagnostic views, 실제 semantic Review records.
- 넓고 낮은 지붕, 위쪽의 낮은 돌 장식, 지붕 아래의 사각 등실, 받침판과 벌어진 다리/아치형 하부 받침을 주요 silhouette로 보존한다.
- 등실 중앙의 사각 개구부가 분명히 식별되어야 한다. 막힌 평면에 그린 어두운 사각형만으로 이 요구를 충족했다고 판단하지 않는다.
- 사람, 앞쪽 기둥, 주변 나무·길·뒤쪽 다른 구조물은 제작 대상이 아니다. 가려진 부분은 보이는 구조와 조화되는 범위에서 보완한다.
- 돌의 세부 얼룩·마모·미세 질감, 정확한 채색·실측 치수·보이지 않는 면의 장식은 별도 blocking requirement로 추가하지 않는다.

## Proposed Acceptance Criteria / Applicability

| ID | Blocking | Authority | Proposed supported stage | PASS / REVISE 의미 |
|---|---|---|---|---|
| AC-MULTIVIEW-LANTERN | YES | USER_CURRENT_REFERENCE | multiview | 이미지들이 같은 석등의 주요 parts와 비율을 유지한다. 사람·기둥·배경이 주 대상에 결합되거나 주요 parts가 크게 변형되면 UNMET. |
| AC-GEOMETRY-SILHOUETTE | YES | USER_CURRENT_REFERENCE | geometry | 현재 GLB의 진단 views에서 지붕·등실·받침의 실루엣이 reference의 석등으로 명확히 식별된다. 심한 parts 붕괴·유실은 UNMET. |
| AC-GEOMETRY-SQUARE-OPENING | YES | USER_CURRENT_REQUEST | geometry | 현재 GLB 진단 views 중 관측 가능한 각도에서 중앙의 사각 개구부와 둘레의 돌 frame이 분명히 보인다. 막힘·유실·형태 붕괴는 UNMET; evidence가 불충분하면 UNCERTAIN. |

이 배정은 새 Request에서 도출한 제안이며, C-01 production prepare/coverage 검사를 실제 통과한 기록이 아니다. Multiview Reviewer는 geometry-only 기준을 대신 충족 판정하지 않는다. 두 stage의 모든 applicable blocking 기준이 current evidence로 SATISFIED일 때만 최종 PASS/INTERNAL_ACCEPT가 가능하다. UNMET은 REVISE 근거가 되고, UNCERTAIN은 PASS를 차단한다. 이 image review를 watertight topology·정확한 치수·엔진 import 성능 증명으로 확대하지 않는다.

## Interpretation / Bounds / Readiness

- 결정적 intent ambiguity 없음. 사진과 요청이 대상 및 핵심 형태를 충분히 결정하므로 semantic clarification 질문은 하지 않았다.
- Technical sampling, occluded shape 보완, view/diagnostic 처리의 세부 선택은 고정 capability의 범위에서 Frontier가 담당한다.
- Existing declared capability: `fixed_four_view_glb_seed_only`; Worker6 / Reviewer4 / Renderer2 / revision1 / retry0. 이는 기존 계약의 budget 정보이며 이번 실제 호출 수가 아니다.
- Non-goals: source/test/contract 변경, 새 stage/validator, I-01/I-02 해결, manual artifact replacement, budget 확대, seed brute force, 기존 Session resume, Delivery.
- Stop condition: readiness blocker가 없을 때만 canonical actual Loop를 실행해 INTERNAL_ACCEPT를 검증한다. Source/contract 변경이 필요하면 effect 전에 중단한다.
- 현재 readiness: **FAIL_CURRENT_REFERENCE_ROUTING**. 기존 entry는 고정 manifest 및 `hunyuan-official-demo-padded.png`만 소비하며 새 Reference의 전달 경로가 없다.
- Session ID / Loop ID / binding / Frozen Specification / child namespaces: **미생성**. 후보 문서를 actual record로 승격하지 않았다.
