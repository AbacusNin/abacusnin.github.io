# Commons portrait provenance checklist

**Status: Proposed for general OSINT use.** This is a review process for public Wikimedia media. It does not turn a username into verified identity.

1. Record the biography title, URL, article revision ID, and collection time. The lead image can change. Name the exact file displayed in the recorded revision.
2. Open that file's Commons description page. Record its title and a permanent page link. If it is a crop, follow the cited `Derived from`, `Extracted from`, or other source link. Repeat until the recorded chain reaches a base file. Keep every link; do not infer a parent from similar file names alone.
3. On the base file, inspect **File history** or save the Commons `prop=imageinfo` response. The upload-history reviewer in this folder sorts the visible versions by timestamp and reports the oldest visible account. Check for API continuation and hidden users before accepting that result.
4. Ask whether the base file was transferred from another wiki, mirrored from another site, or uploaded by a bot. If so, the Commons account may only be an importer. Follow the earlier source before making a stronger claim.
5. Keep account provenance separate from identity. A talk-page statement or COI disclosure may support a claimed relationship, but preserve its exact page revision and wording. A generic COI guideline is context, not corroboration of a particular person.
6. Record the answer as narrowly as the evidence allows: "account on the oldest visible Commons upload of this base file." Add the stronger relationship only when a specific independent source supports it. Note any suppressed history, broken parent link, missing revision, or unresolved ambiguity.

**Required inputs:** an article revision, Commons file pages, visible upload history, and any case-specific disclosure. **Output:** a citation trail and a scoped account-attribution statement. **Failure surfaces:** later cropper mistaken for first uploader, mutable lead image, bot imports, incomplete API pagination, hidden revisions, and an account mistaken for a verified human identity. No IOC, detection rule, or production monitoring claim follows from this checklist.
