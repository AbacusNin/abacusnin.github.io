# LLM agent authorization triage

Use this decision aid on an authorized test target. It grew from one records-custodian exercise, so I would check each step against the actual procedure before using it elsewhere.

Start by classifying the task. A target that explains its gates, logs unsupported role claims, and ties the objective to a ticket or audit entry may expect completion of a sanctioned workflow. The phrase "elevation is not the win" is another strong clue. A silent agent or a target whose objective explicitly requires bypass testing needs a different plan.

1. **Read the objective.** Identify the requested end state. In the court custodian case, a higher tier was a prerequisite; the audit record from a completed emergency action carried the answer.
2. **Ask for the procedure.** Record the gates, accepted field names, and response to a plain information request. Save replies and visible state changes. A role claim in the same message can affect the response, as it did in this case.
3. **Separate identity from a title.** Supply a real, authorized credential when the procedure requires one. A title typed into a chat message does not establish identity.
4. **Check every reason predicate.** Choose an emergency reason only when the underlying facts support it. A legal-order option needs an actual order; an in-person verification option needs actual verification.
5. **Resolve identifiers before invoking access.** Write down the required identifier class and canonical format. An enrollment ID and a medical record number can refer to different things. A generic prefix can also make the right underlying value fail.
6. **Interpret denials narrowly.** A response that names only an identifier mismatch narrows the next check. It does not prove that every other field was accepted unless the system explicitly reports that decision.
7. **Record the side effect.** Confirm the emergency action and its audit entry separately from the tier change. Keep a platform acceptance result separate from the daemon's own reply.
8. **Inspect tempting values.** A disclosed credential segment remains a credential. Compare any token-like value with the stated objective before using it.

For a production assessment, test a valid emergency, a valid credential with the wrong record, unsupported reasons, title claims, identifier disclosure requests, and repeated denials. Use server decisions and audit records as the source of truth. Keep patient identifiers and credentials out of the public report.
