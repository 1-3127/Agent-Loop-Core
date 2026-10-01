# Fresh Session Final-2 — Frozen Work Specification v1

레퍼런스 이미지에 있는 석등을 제작하라.
석등은 중앙의 사각형 구멍을 포함한 실루엣이 명확히 나와야 한다.

Target/deliverable: one current 3D stone-lantern GLB, multiview images and diagnostic evidence. Stop at INTERNAL_ACCEPT.

Goal: Create a 3D stone lantern faithful to the directly attached reference, with a clear silhouette and central square opening.

Must-have: Preserve the broad low roof with projecting eaves, central lantern chamber, and raised leg-like stone support shown in the reference.
Must-have: The central square aperture must be an actual open cavity in the 3D geometry, with readable boundaries; a dark surface patch is insufficient.
Must-have: Produce a current GLB through the fixed four-view pipeline and evaluate its current diagnostic renders before INTERNAL_ACCEPT.

Direct reference: {"bytes":362412,"identity":"CURRENT_DIRECT_USER_REFERENCE","path":"D:\\VSCODE-WorkSpace\\Others\\Agent-Loop-Core\\docs\\session\\fresh-session-refresh-proof-final-2\\CURRENT_REFERENCE.png","sha256":"9da5ed9e7f3490d058673122a7bd50b46635d4f0b5a36ca3199f0c1636cd17e5"}

Non-goals: foreground post, person, garden, exact unseen details, physical scale, texture production, source/test changes, historical resume, Delivery and closure.

Specification Dialogue: no blocking ambiguity; occluded backside completion follows observed structure. All criteria independently derived from current request/reference.

Criteria (all mandatory blocking):
LANTERN_FORM | authority=reference | stages=multiview,geometry | Recognizable stone-lantern silhouette: broad low eaved roof, central chamber, and raised leg-like support, consistent with the current reference. Exclude the foreground post, person, and garden scene.
APERTURE_VISUAL | authority=request | stages=multiview | The lantern chamber has a clearly bounded square aperture readable in the visible generated views; do not mistake the openings between base legs for the chamber aperture. Occluded views need coherent completion, not invented exact historical detail.
MULTIVIEW_IDENTITY | authority=reference | stages=multiview | Right, left, and back depict the same stone lantern with coherent proportions and structural arrangement; scene clutter must not become part of the target.
APERTURE_GEOMETRY | authority=request | stages=geometry | Current 3D diagnostic renders show the central square chamber aperture as a real recessed/open cavity with spatial depth and empty volume, not merely a flat dark square texture. If current renders cannot establish this, do not PASS.
GLB_READABILITY | authority=request | stages=geometry | The current GLB is a coherent readable lantern in diagnostic views, preserving the reference silhouette without gross merged clutter or broken essential components.

PASS means every selected criterion is SATISFIED with current evidence. REVISE requires an observed blocker and an action within the existing fixed capability. Unobservable mandatory evidence cannot be assumed SATISFIED. Fixed budgets: worker 6, reviewer 4, renderer 2, revision 1. No hidden retry or manual replacement.
