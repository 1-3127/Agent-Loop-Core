"""Prospective fixed host calls. No Session start, grant, or inference authority."""
import json
from pathlib import Path
import subprocess
from host_geometry_contract import validate_fixed_trace_stage, verify_trace_tolerance

HERE = Path(__file__).resolve().parent

def trace_before_worker(python, source, output, selected_stage):
    # Resolve the immutable ExecutionAdapter work_order['stage'] before effects.
    epsilon = validate_fixed_trace_stage(selected_stage)
    output = Path(output)
    with (output/'selected-trace-stage.json').open('x', encoding='utf-8') as stream:
        json.dump(selected_stage, stream)
    process = subprocess.run([str(python), str(HERE/'reference_trace.py'), str(source), str(output), str(output/'selected-trace-stage.json')], capture_output=True, check=True)
    data = json.loads((output/'logo-contours.json').read_text(encoding='utf-8'))
    verify_trace_tolerance(selected_stage, data['simplification_pixels'])
    if data['simplification_pixels'] != epsilon:
        raise ValueError('TRACE_POLICY_WAS_NOT_APPLIED')
    return data, process

def full_diagnostic_request(source, source_hash, traced, output, manifest, parameters=None):
    return dict(source_glb=str(source), source_sha256=source_hash, output=str(output), manifest=str(manifest),
                pixel_scale=traced['scale'], image_width=traced['image_width'], image_height=traced['image_height'],
                parameters=parameters or {})

def compare_silhouette(mask_path, rendered_path, output):
    """Identical canvases only; no resizing or alignment optimization."""
    import numpy as np
    from PIL import Image
    mask = np.asarray(Image.open(mask_path).convert('L')) > 127
    rendered = np.asarray(Image.open(rendered_path).convert('RGB'))
    if rendered.shape[:2] != mask.shape:
        raise ValueError('SILHOUETTE_CANVAS_MISMATCH')
    actual = rendered.max(axis=2) > 127
    union = int((mask | actual).sum())
    intersection = int((mask & actual).sum())
    if not union:
        raise ValueError('SILHOUETTE_COMPARISON_EMPTY')
    output = Path(output)
    overlay = np.zeros((*mask.shape, 3), dtype=np.uint8)
    overlay[mask & actual] = (255, 255, 255)
    overlay[mask & ~actual] = (255, 0, 0)
    overlay[actual & ~mask] = (0, 255, 255)
    with (output/'silhouette-overlay.png').open('xb') as stream:
        Image.fromarray(overlay).save(stream, format='PNG')
    result = dict(iou=intersection/union, intersection_pixels=intersection, union_pixels=union,
                  reference_pixels=int(mask.sum()), rendered_pixels=int(actual.sum()),
                  canvas_width=mask.shape[1], canvas_height=mask.shape[0],
                  alignment='unchanged fixed reference canvas',
                  interpretation='Diagnostic measurement; semantic acceptance remains independent Review and Frontier')
    with (output/'silhouette-metrics.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    return result

if __name__ == '__main__':
    import sys
    compare_silhouette(*sys.argv[1:])
