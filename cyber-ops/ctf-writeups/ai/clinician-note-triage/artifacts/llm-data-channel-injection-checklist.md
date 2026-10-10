# LLM data-channel injection test checklist

Use fictional records and a lab canary in an authorized environment. Record the exact input, transport, session identity, output, and request ID for every attempt.

- [ ] Draw the data path: who authors each field, who assigns its origin label, what tools and secrets the model can reach, and where output goes.
- [ ] Capture the application's claimed rules as hypotheses. Check whether an authorization service enforces them outside the model.
- [ ] Establish a direct-request baseline. Keep the refusal or disclosure as an observed result, not as proof of every future path.
- [ ] Test the instruction inside lower-trust data fields, including a note, uploaded document, retrieved record, or tool output if those carriers exist.
- [ ] Change one factor at a time: paste versus upload, ordinary versus high-stakes context, direct versus embedded wording, and authenticated versus unauthenticated session.
- [ ] Try a document that claims a trusted origin. Confirm that content alone cannot change the application's origin or authorization metadata.
- [ ] Test filename and asserted human authority separately from the data-field mechanism.
- [ ] Include negative controls: benign imperatives, a note without a secret request, a secret request that the assistant refuses, and a response containing only a lookalike canary.
- [ ] Treat system-prompt requests and encoded-output attempts as separate avenues. Record rejections; do not turn failed attempts into findings.
- [ ] Distinguish model refusal, application denial, and service malfunction. Repeat only when authorized and necessary to resolve ambiguity.
- [ ] Check whether an unverified requester receives the synthetic canary. Record expected and observed outcomes for each case.
- [ ] Review input/output logging, redaction, access control, and retention before adapting the test to production. Real patient data and protected values do not belong in public fixtures.

The test succeeds defensively when the application enforces the channel and role decision using trusted metadata and keeps the protected value outside untrusted summarization. Prompt wording or a keyword alert alone does not establish that boundary.
