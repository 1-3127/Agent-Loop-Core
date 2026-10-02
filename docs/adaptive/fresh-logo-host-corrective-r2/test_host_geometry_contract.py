"""Synthetic-only regression; no actual User inputs, Session, or production."""
import math
import unittest
from host_geometry_contract import contour_epsilon_from_stage, verify_trace_tolerance, reference_orthographic_scale, fitted_orthographic_scale

class ContourPolicyTests(unittest.TestCase):
    def stage(self, **extra):
        return {'parameters': dict(construction_instructions=['Simplify contours only within 0.25 source pixels while preserving sharp corners and narrow gaps.'], **extra)}
    def test_observed_old_policy_is_rejected_against_selected_workflow(self):
        with self.assertRaisesRegex(ValueError, 'TRACE_EXCEEDS_WORKFLOW_TOLERANCE'):
            verify_trace_tolerance(self.stage(), .55)
    def test_exact_or_stricter_measured_policy_is_admitted(self):
        self.assertEqual(contour_epsilon_from_stage(self.stage()), .25)
        self.assertEqual(verify_trace_tolerance(self.stage(), .25), .25)
        self.assertEqual(verify_trace_tolerance(self.stage(), .1), .25)
    def test_missing_conflicting_and_invalid_policy_fail_before_effects(self):
        with self.assertRaisesRegex(ValueError, 'REQUIRED'):
            contour_epsilon_from_stage({'parameters': {}})
        with self.assertRaisesRegex(ValueError, 'CONFLICT'):
            contour_epsilon_from_stage(self.stage(contour_tolerance_pixels=.55))
        for value in (True, 0, -1, float('nan'), float('inf'), '0.25'):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'INVALID'):
                contour_epsilon_from_stage({'parameters': {'contour_tolerance_pixels': value}})

class CameraFramingTests(unittest.TestCase):
    def test_wide_reference_requires_width_based_scale(self):
        pixel_scale = 10 / 626
        corrected = reference_orthographic_scale(800, pixel_scale)
        self.assertGreater(corrected, 10)
        self.assertLess(reference_orthographic_scale(400, pixel_scale), 10)
        self.assertAlmostEqual(10 / corrected * 800, 626)
    def test_horizontal_vertical_and_perspective_extents_fit(self):
        for points, w, h in [([(-5,-.6),(5,.6)],800,400),([(-.04,-.6),(.04,.6)],800,400),([(-4,-2),(4,2)],800,400),([(-2,-5),(2,5)],400,800)]:
            scale = fitted_orthographic_scale(points,w,h)
            span_x=max(p[0] for p in points)-min(p[0] for p in points)
            span_y=max(p[1] for p in points)-min(p[1] for p in points)
            self.assertLess(span_x,scale)
            self.assertLess(span_y,scale*h/w)
    def test_invalid_frames_do_not_produce_plausible_defaults(self):
        for args in [([],800,400), ([(0,0),(0,0)],800,400), ([(0,0),(1,1)],0,400), ([(0,0),(1,1)],800,400,.5)]:
            with self.subTest(args=args), self.assertRaises(ValueError):
                fitted_orthographic_scale(*args)

if __name__ == '__main__':
    unittest.main()
