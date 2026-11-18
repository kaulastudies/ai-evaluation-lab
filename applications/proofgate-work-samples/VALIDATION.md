# Validation — 4 November 2026

Local validation, not independent certification or an employer pilot.

- Nine unit tests passed: evidence roundtrip, forged verdict with recomputed hash,
  failed-parent retention, consent, AI disclosure, HTML escaping, path restriction,
  false identity claim and rejection of unnecessary private fields.
- CLI export created HTML and JSON; CLI verification matched pinned Git evidence.
- Fresh source-exact replay reproduced AP-005 initial VERIFIED_FAIL.
- Fresh source-exact repair replay reproduced AP-005 repair VERIFIED_PASS.
- Both replay results use the mock provider and frozen recorded responses; no new
  model inference or paid API call was used.

The two fresh replay reports are in evidence/. The packet in demo/ uses an
explicitly fictional demonstration declaration. It contains no real beneficiary.
No job outcome, independent worker ability, customer adoption or revenue was tested.
