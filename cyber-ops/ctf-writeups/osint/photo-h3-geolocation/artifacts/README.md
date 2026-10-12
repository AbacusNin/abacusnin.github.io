# Photo geolocation exposure review

These are defensive proofs of concept for an authorized image-publication review or an analyst's offline reconstruction. All coordinates in `geo_sample.json` are invented. No challenge photo, exact camera cell, or person-level location is included.

## Camera-path geometry

`geo_path_review.py` reads one local JSON configuration. It requires Python 3.10+ and `h3` Python 4.x for the command-line H3 conversion. Install dependencies in an isolated environment using your organization's normal package review process. The module's geometry functions can be tested without `h3`.

```sh
python geo_path_review.py geo_sample.json
python -m unittest test_geo_review.py
```

Input fields are `path_start`, `path_end`, `subject` as latitude/longitude pairs, `heading_deg`, `subject_offset_window_deg`, `aux_path_fraction_window`, `step_m`, and `h3_resolution`. The output gives sampled-point count, matching-point count, and unique candidate H3 cells. Negative angular offsets mean the subject is to the left of the heading. The auxiliary interval must come from separately verified sight-line evidence; the tool does not infer visibility from pixels or map features.

This is a short-path approximation: it linearly interpolates latitude and longitude, assumes a fixed heading and analyst-supplied angle window, and does not model camera lens distortion, occlusion, elevation, or survey uncertainty. Do not use it to claim an exact person location from one ambiguous photo. A sample step can miss a thin cell crossing; inspect neighbors and the path on a map before a high-stakes decision. Paths crossing the antimeridian are outside scope.

## Image publication check

`image_exposure_review.py` requires Pillow. It reads local JPEG, PNG, and WebP files and reports metadata presence without printing coordinates. It limits input files to 20 MB and images to 40 million pixels. It does not write sanitized images, contact the network, or inspect visible landmarks. A clean GPS result never means the photo is safe to publish. An authorized reviewer must still inspect the image, caption, background, and posting time.

```sh
python image_exposure_review.py approved_photo.jpg
```

The tests cover a GPS-bearing synthetic JPEG, a metadata-free benign JPEG, a malformed file, a geometric positive, a bearing-window near miss, and a zero-length path. The H3 conversion branch was not exercised in the packaged tests. Neither script has been validated on production imagery or telemetry.
