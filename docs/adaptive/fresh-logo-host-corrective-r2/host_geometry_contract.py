"""Fixed logo-host contour policy and Blender horizontal camera framing."""
import math
import re

def _positive(value, error):
    if type(value) not in (float, int) or not math.isfinite(value) or value <= 0:
        raise ValueError(error)
    return float(value)

def contour_epsilon_from_stage(stage):
    """Resolve the chosen immutable stage's limit; never substitute a default."""
    parameters = stage['parameters']
    declared = parameters.get('contour_tolerance_pixels')
    limits = []
    for instruction in parameters.get('construction_instructions', []):
        match = re.search(r'Simplify contours only within ([0-9]+(?:\.[0-9]+)?) source pixels', instruction)
        if match:
            limits.append(_positive(float(match.group(1)), 'CONTOUR_TOLERANCE_INVALID'))
    if declared is not None:
        declared = _positive(declared, 'CONTOUR_TOLERANCE_INVALID')
        if limits and any(value != declared for value in limits):
            raise ValueError('CONTOUR_TOLERANCE_CONFLICT')
        return declared
    if not limits:
        raise ValueError('WORKFLOW_CONTOUR_TOLERANCE_REQUIRED')
    if len(set(limits)) != 1:
        raise ValueError('CONTOUR_TOLERANCE_CONFLICT')
    return limits[0]

def verify_trace_tolerance(stage, observed_pixels):
    maximum = contour_epsilon_from_stage(stage)
    observed = _positive(observed_pixels, 'CONTOUR_TOLERANCE_INVALID')
    if observed > maximum:
        raise ValueError('TRACE_EXCEEDS_WORKFLOW_TOLERANCE')
    return maximum

def validate_fixed_trace_stage(stage):
    """Reject the observed unsupported recipe instead of silently overriding it."""
    epsilon = contour_epsilon_from_stage(stage)
    instructions = ' '.join(stage['parameters'].get('construction_instructions', []))
    if re.search(r'\bsubpixel\b|\bantialias midpoint\b|\bXY plane\b|\balong Z\b', instructions, re.I):
        raise ValueError('FIXED_TRACE_CAPABILITY_MISMATCH')
    return epsilon

def reference_orthographic_scale(image_width, pixel_scale):
    """Camera sensor_fit must be HORIZONTAL: ortho_scale is frame width."""
    return _positive(image_width, 'REFERENCE_WIDTH_INVALID') * _positive(pixel_scale, 'PIXEL_SCALE_INVALID')

def fitted_orthographic_scale(projected_points, render_width, render_height, margin=1.15):
    """Fit camera-space XY bounds in a HORIZONTAL Blender camera frame."""
    width = _positive(render_width, 'RENDER_SIZE_INVALID')
    height = _positive(render_height, 'RENDER_SIZE_INVALID')
    margin = _positive(margin, 'MARGIN_INVALID')
    if margin < 1 or not projected_points:
        raise ValueError('CAMERA_FIT_INVALID')
    if any(len(p) != 2 or any(not math.isfinite(v) for v in p) for p in projected_points):
        raise ValueError('CAMERA_FIT_INVALID')
    span_x = max(p[0] for p in projected_points) - min(p[0] for p in projected_points)
    span_y = max(p[1] for p in projected_points) - min(p[1] for p in projected_points)
    scale = max(span_x, span_y * width / height) * margin
    return _positive(scale, 'CAMERA_FIT_INVALID')
