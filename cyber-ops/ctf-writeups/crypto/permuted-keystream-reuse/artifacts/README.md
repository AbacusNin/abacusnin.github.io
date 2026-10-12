# Permuted-keystream review lab

These are defensive proofs of concept based on the cipher design in the case. The data are synthetic. No challenge ciphertext, key, generator, or submission receipt is bundled here.

## Run

Python 3.10 or later, standard library only:

```bash
python test_pocs.py
python keystream_lab.py
python crypto_review.py your_python_file.py
```

`keystream_lab.py` prints the raw and alphabet-filtered candidate count for three deterministic, invented 25-byte examples. Each trial checks that the synthetic secret survives every position. The generator's `random.Random` is used only to recreate the weak construction for a reproducible lab. The input is a seed and length; the output is candidate counts. It does not recover an unknown real-world secret or validate the challenge's reported counts.

`crypto_review.py` accepts Python source files and emits `file:line:rule (key)` review leads. Its sensor is repository source code, not runtime logs. It requires direct `key = random.randbytes(...)` assignment and, for the second finding, direct `encrypt(key, ...)` plus `encrypt(transform(key), ...)` calls in one module or function. The `transform` may be a nested expression containing the key. This is deliberately narrow. It cannot prove the two calls run on the same key value, follow aliases across functions, assess nonce handling, or find all custom ciphers. Review each lead manually. A direct `random.randbytes` assignment is a weak-key lead even without visible reuse.

The test fixture covers a positive transformed-reuse example, benign sampling with a `secrets` key, a near miss that uses a weak key only once, three synthetic recovery trials, and a case where the alphabet range removes one of four possibilities. Expected and observed on this local run: two findings, zero findings, one finding, all secret bytes retained, and three remaining byte candidates respectively. These checks establish local logic only. They are not Semgrep validation, production accuracy, or a deployed CI gate.

The source record also included proposed Semgrep patterns and a reported Bandit `B311` result. Scanner output and the exact control fixture were unavailable for independent verification. The report on the page keeps those statements attributed to the record. The AST script here supplies a locally tested alternative, with the limitations above.

The [proposed Semgrep rule](proposed_semgrep.yml) retains that detection idea for review. Semgrep did not start in this local environment because its certificate-store initialization failed before rule loading. The YAML parses as data, but Semgrep syntax and match behavior have not been validated. The low-bit rule will need data-flow context to avoid benign matches. Keep it out of a blocking pipeline until it passes real positive, benign, and near-miss fixtures under the target Semgrep version.
