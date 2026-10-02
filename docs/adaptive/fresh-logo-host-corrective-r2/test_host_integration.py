"""Synthetic imagery only; no actual Session/reference/artifact input."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw
from host_integration import trace_before_worker, compare_silhouette

class TraceIntegrationTests(unittest.TestCase):
    def test_selected_workflow_drives_real_tracer_and_preserves_hole_and_strokes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary); output=root/'trace'; output.mkdir()
            image=Image.new('RGB',(120,60),(40,40,40)); draw=ImageDraw.Draw(image)
            draw.rectangle((10,10,40,50),fill=(190,175,140))
            draw.rectangle((20,20,30,40),fill=(40,40,40))
            for y in (10,28,46):draw.rectangle((60,y,105,y+4),fill=(190,175,140))
            image.save(root/'synthetic.png')
            stage={'parameters':{'contour_tolerance_pixels':.25}}
            result,process=trace_before_worker(sys.executable,root/'synthetic.png',output,stage)
            self.assertEqual(process.returncode,0)
            self.assertEqual(result['simplification_pixels'],.25)
            self.assertEqual(result['shape_count'],4)
            self.assertEqual(result['hole_count'],1)
            self.assertEqual(json.loads((output/'selected-trace-stage.json').read_text()),stage)
    def test_missing_policy_has_no_output_effect(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            with self.assertRaisesRegex(ValueError,'REQUIRED'):
                trace_before_worker(sys.executable,root/'missing.png',root,{'parameters':{}})
            self.assertEqual(list(root.iterdir()),[])
    def test_observed_unsupported_recipe_is_rejected_without_effects(self):
        for instruction in ('Extract oriented subpixel contour loops.', 'Use an antialias midpoint boundary.', 'Map into the XY plane.', 'Extrude along Z.'):
            with self.subTest(instruction=instruction), tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary)
                stage={'parameters':{'contour_tolerance_pixels':.25,'construction_instructions':[instruction]}}
                with self.assertRaisesRegex(ValueError,'CAPABILITY_MISMATCH'):
                    trace_before_worker(sys.executable,root/'missing.png',root,stage)
                self.assertEqual(list(root.iterdir()),[])
    def test_comparison_preserves_fixed_canvas_and_does_not_resize(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            image=Image.new('RGB',(20,10)); ImageDraw.Draw(image).rectangle((2,2,17,7),fill='white')
            image.save(root/'mask.png'); image.save(root/'render.png')
            self.assertEqual(compare_silhouette(root/'mask.png',root/'render.png',root)['iou'],1)
            Image.new('RGB',(10,20)).save(root/'wrong.png')
            with self.assertRaisesRegex(ValueError,'CANVAS_MISMATCH'):
                compare_silhouette(root/'mask.png',root/'wrong.png',root)

if __name__=='__main__': unittest.main()
