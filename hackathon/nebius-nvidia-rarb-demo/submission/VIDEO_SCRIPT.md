# Demo Video Script — target runtime 2:40–2:50

The public submission video must stay under three minutes. Record the actual judge interface and terminal/repository evidence; do not add copyrighted music.

## 0:00–0:18 — The problem

**On screen:** RARB landing page headline and the 51-attempt evidence snapshot.

**Voiceover:**

“Coding agents can write a patch, run public tests, and say they are done. But a green test is not always proof that the repository task is actually correct. RARB is a reliability layer that asks a second question: is the evaluation itself strong enough to trust?”

## 0:18–0:38 — How RARB works

**On screen:** Scroll through the three principles: qualify the verifier, evaluate the patch, replay the result.

**Voiceover:**

“First, RARB qualifies the verifier with a known-good reference, known-bad controls, and critical mutations. Then the coding agent generates a candidate. Public tests are evidence, not the final verdict. A qualified verifier produces VERIFIED_PASS, VERIFIED_FAIL, or HOLD, and the result is preserved for source-exact replay.”

## 0:38–1:05 — Nebius + NVIDIA execution

**On screen:** Select **Nebius / Nemotron pass** in Judge Mode. Show provider, model, gates, final verdict, and replay state.

**Voiceover:**

“For the hackathon, I integrated Nebius Token Factory through its chat-completions API and used NVIDIA Nemotron 3 Super 120B A12B to generate repository-task candidates. This is a real preserved Phase 12 Nemotron run: candidate admitted, public validation passed, the qualified verifier passed, the trusted boundary remained intact, and no-model replay reproduced the result.”

## 1:05–1:30 — Preserve the failure

**On screen:** Select **Preserved Phase 12 failure**. Let the failed steps appear.

**Voiceover:**

“RARB also preserves failures. In this Phase 12 llama3 attempt, the agent claimed success, but public validation failed and three AP-001 verifier gates failed. RARB kept the attempt as VERIFIED_FAIL. It did not replace the result with a better run and did not trigger repair because this was not a public-test false-green.”

## 1:30–1:58 — False-green and bounded repair

**On screen:** Select **False-green → repair**.

**Voiceover:**

“This AP-005 example shows the failure mode RARB is designed to catch. The initial patch passed public tests but failed all four qualified edge-case gates. RARB froze that false-green, exposed only bounded failed-gate evidence to a repair attempt, and applied the same qualified verifier. The repair converted to VERIFIED_PASS.”

## 1:58–2:23 — Replication evidence

**On screen:** Scroll to Phase 12 cards and the 29/30, 30/30, zero false-green, zero repair row.

**Voiceover:**

“Phase 12 was preregistered before execution: one frozen repository task, three fixed configurations, ten trials each. The batch produced 29 verified passes, one preserved failure, zero false-greens, zero repairs, and all 30 attempts passed source-exact no-model replay. The ten Nebius Nemotron attempts were all verified passes.”

## 2:23–2:42 — Reproducibility / terminal

**On screen:** Show the repository, the committed evidence paths, and run the one-command RARB demo or replay check locally. Capture the final GREEN output.

**Voiceover:**

“The repository contains the task contracts, verifier qualification, model responses, candidate artifacts, manifests, replay records, and CI gates. A stored verdict can be checked without spending another model call.”

## 2:42–2:52 — Close

**On screen:** Return to the headline and evidence boundary.

**Voiceover:**

“RARB does not claim that one benchmark proves general model reliability. It makes narrower claims that can be inspected and replayed. AI can propose the patch. RARB measures whether the patch deserves to ship.”

## Recording checklist

- Keep the final upload **under 3:00**.
- Use the deployed public demo URL in the browser.
- Show the actual interactive controls, not slides alone.
- Include the words **Nebius Token Factory** and **NVIDIA Nemotron 3 Super 120B A12B** in the audio.
- Show at least one canonical evidence path in GitHub.
- Show the terminal GREEN replay/check output.
- Do not show API keys, environment variables, browser autofill, email, or private tabs.
- Do not use copyrighted background music.
- Upload to YouTube as **Public** before entering the URL in Devpost.
