"""Read-only, local metadata triage for images approved for publication.

The tool reports the presence of metadata, not raw coordinates or image content.
Human review is still required for landmarks, screens, badges, and captions.
"""

import argparse
import json
from pathlib import Path

from PIL import Image, IptcImagePlugin, UnidentifiedImageError

Image.MAX_IMAGE_PIXELS = 40_000_000
MAX_BYTES = 20_000_000


def inspect_image(path):
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("image missing or exceeds 20 MB")
    try:
        with Image.open(path) as image:
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise ValueError("only JPEG, PNG, and WebP are supported")
            if image.width * image.height > 40_000_000:
                raise ValueError("decoded dimensions exceed limit")
            exif = image.getexif()
            gps = exif.get_ifd(34853) if 34853 in exif else {}
            return {"format": image.format, "width": image.width, "height": image.height,
                    "exif_present": bool(exif), "gps_exif_present": bool(gps),
                    "iptc_present": bool(IptcImagePlugin.getiptcinfo(image)),
                    "xmp_present": any("xmp" in str(k).lower() for k in image.info),
                    "comment_present": any("comment" in str(k).lower() for k in image.info),
                    "visual_review_required": True}
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("unsupported or malformed image") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    args = parser.parse_args()
    if len(args.images) > 100:
        parser.error("at most 100 images per run")
    for path in args.images:
        try:
            result = inspect_image(path)
            result["image"] = path.name
        except ValueError as exc:
            result = {"image": path.name, "error": str(exc)}
        print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
