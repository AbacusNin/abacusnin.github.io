# Commons upload-history review

These files help an analyst check which account uploaded the oldest visible version of a named Wikimedia Commons file. They do not identify the account holder as a person. The script works on a saved MediaWiki API response so the evidence can be reviewed without repeatedly querying a live page.

First follow the [provenance checklist](commons_provenance_checklist.md) from the article image through any crop or derivative links. Fetch the upload history for the **base file**. URL encoding is handled by `curl --data-urlencode`:

```sh
curl --fail --silent --show-error --get 'https://commons.wikimedia.org/w/api.php' \
  --data-urlencode 'action=query' \
  --data-urlencode 'format=json' \
  --data-urlencode 'prop=imageinfo' \
  --data-urlencode 'titles=File:EXACT BASE FILE NAME.jpg' \
  --data-urlencode 'iiprop=user|timestamp|comment' \
  --data-urlencode 'iilimit=max' > history.json
python artifacts/commons_history_audit.py history.json
```

The official [MediaWiki Imageinfo documentation](https://www.mediawiki.org/wiki/API:Imageinfo) says `imageinfo` returns upload history, `iiprop=user|timestamp|comment` selects the fields, and `iilimit=max` asks for the maximum page of versions. It can still return a continuation token. The script refuses a response with `continue` or `query-continue`; fetch and record all pages before deciding who appears earliest. Do not assume the first JSON array item is the oldest. The script sorts visible timestamps.

**Input:** one saved, default-format `action=query` JSON response for one `File:` title on Commons, at most 1 MB. **Output:** JSON with file title, visible version count, oldest visible upload time and account, a status, and a scope warning. It exits 0 for a visible account, 1 if the oldest account is hidden or ambiguous, and 2 for invalid or incomplete input. The tool does not fetch network content, follow crop links, verify a claimed family relationship, or inspect suppressed revisions. A transfer from another wiki can make the Commons upload account different from the first account that published the media elsewhere.

```sh
python -B artifacts/test_history_audit.py
python artifacts/commons_history_audit.py fixtures/sample_history.json
```

The [synthetic history](../fixtures/sample_history.json) has a newer replacement above an older upload. Five local tests cover the older-account selection, shuffled API order, a hidden oldest account, a continuation page, and missing or nonlocal files. These checks validate the parser against invented JSON. They do not replay the challenge's browser session, establish a real-world identity, or measure behavior across Commons as a whole.

For a real attribution record, preserve the article revision ID, exact image title at that revision, every derivative-to-parent link, base-file page revision, complete upload history, and any specific talk-page disclosure. The [checklist](commons_provenance_checklist.md) separates account provenance from a claim about the person behind that account.
