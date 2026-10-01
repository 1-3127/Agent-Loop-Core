"""Deterministic execution derivative for the fixed Scenario A 768-square seam."""
import hashlib
from io import BytesIO
import zlib

from PIL import Image, __version__ as pillow_version

TARGET = (768, 768)
CONTRACT = {
    "kind": "contain_pad", "version": "scenario-a-reference.1",
    "target_dimensions": list(TARGET), "upscale": False, "crop": False,
    "alignment": "center_floor", "padding_rgb": [255, 255, 255],
    "padding_alpha": 0, "resampling": "LANCZOS",
    "encoding": "PNG", "compress_level": 9, "optimize": False,
    "metadata": "strip_on_transform_preserve_on_identity",
    "pillow_version": pillow_version, "zlib_version": zlib.ZLIB_RUNTIME_VERSION,
}


def normalize_reference(payload):
    """No writes or effects; preserve all pixels for smaller/equal inputs.

    White RGB (transparent white for alpha inputs) matches the existing padded
    fixture and LoadImage's RGB conversion. Larger inputs alone are downsampled.
    """
    with Image.open(BytesIO(payload)) as image:
        if image.format != "PNG":
            raise ValueError("current normalization requires PNG")
        image.load()
        width, height = image.size
        mode = image.mode
        if image.size == TARGET:
            resized = image.size
            output_mode = mode
            encoded = payload  # No semantic or encoding change on identity.
            operation = "identity"
        else:
            largest = max(width, height)
            resized = ((max(1, (width * 768 + largest // 2) // largest),
                        max(1, (height * 768 + largest // 2) // largest))
                       if largest > 768 else image.size)
            output_mode = "RGBA" if "A" in image.getbands() or "transparency" in image.info else "RGB"
            content = image.convert(output_mode)
            if resized != image.size:
                content = content.resize(resized, Image.Resampling.LANCZOS)
            fill = (255, 255, 255, 0) if output_mode == "RGBA" else (255, 255, 255)
            canvas = Image.new(output_mode, TARGET, fill)
            canvas.paste(content, ((768-resized[0])//2, (768-resized[1])//2))
            stream = BytesIO()
            canvas.save(stream, format="PNG", compress_level=9, optimize=False)
            encoded = stream.getvalue()
            operation = "fit_pad" if largest > 768 else "pad"
    left, top = (768-resized[0])//2, (768-resized[1])//2
    record = {
        "contract": CONTRACT.copy(), "operation": operation,
        "original_dimensions": [width, height], "resized_dimensions": list(resized),
        "padding_offsets": {"left": left, "top": top,
                            "right": 768-resized[0]-left, "bottom": 768-resized[1]-top},
        "original_mode": mode, "output_mode": output_mode,
        "normalized_sha256": hashlib.sha256(encoded).hexdigest(),
        "normalized_bytes": len(encoded),
    }
    return encoded, record
