# Metadata review checklist

**Status: Proposed.** Use this after a file-review pipeline flags a long hex value in an image comment. A match is a lead, not a finding of credential theft.

1. Preserve the received file, its SHA-256, path, owner, source system, collection time, and access controls. Work from a copy.
2. Confirm the PNG container and parse the exact metadata field. The local scanner examines Adobe XMP in `iTXt` and `exif:UserComment`; it does not inspect pixels or every metadata format.
3. Keep any embedded candidate value in restricted evidence storage. The default scanner output gives counts without exposing candidate digests. Decide separately whether `--show-digests` is authorized.
4. Compare the image with known output from the same producer. A content hash, software identifier, or test fixture can look similar. Record that explanation if it closes the lead.
5. If the value could represent a credential verifier, identify the owning application and password-storage design. Check whether per-record salts and a costed password KDF are used. Do not infer storage practice from digest length alone.
6. If access was unauthorized or the material was shared outside its expected boundary, follow the organization's incident process for access review, credential reset, file removal, and retention. Preserve the evidence trail before taking action.
7. Tune on a labeled set from the actual intake path: positive samples, benign long-hex comments, compressed XMP, malformed files, and near misses. Measure review volume and misses before promoting the rule to an alert.

**Inputs:** PNG bytes and contextual file events from an authorized upload, attachment, or file-storage sensor. **Outputs:** a documented triage decision and, where warranted, an incident record. **Limits:** no identity attribution, intent inference, algorithm identification, or automatic credential compromise determination. No production deployment or corpus measurement is claimed.
