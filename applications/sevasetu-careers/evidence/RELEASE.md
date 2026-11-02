# Release validation — 0.1.0

Validated on 2 November 2026. This is author-run engineering evidence, not independent certification or Army acceptance.

- `npm test`: **45 tests passed** on Node.js 24.22.1. Contract, source-policy, server and CLI byte/hash checks included. GitHub CI also runs the suite on Node.js 22.
- `npm run check`: browser module syntax checks passed.
- `npm run evaluate`: all 3 author-labelled synthetic candidate cases passed; the complete inputs and hashes are in `offline-evaluation.json`.
- Existing Lab Python suite: **22 tests passed** after obtaining the repository history required by its evidence replays.
- `tests/browser-check.mjs`: desktop (1440 × 1100) and mobile (390 × 844), profile switching, filters, review queue, local vacancy import, CV/receipt downloads, hash comparison and 5 interactive fixture checks passed. No browser page errors or mobile horizontal overflow were observed. See `browser-checks.json`.
- Browser print-to-PDF output was rendered and visually reviewed after formatting the CV into experience, education and training sections. The observed sample fit on one page without clipping.
- The combined Pages build completed with both the existing ProofGate app and the new SevaSetu folder present. Deployment adds a source-commit/hash manifest.

The browser check used Chromium 153.0.8010.0 with Playwright in a headless test environment. The optional Ollama adapter was tested against simulated responses only. No live-model inference, actual candidate trial, official vacancy feed, authorised AWPO database integration, recruitment outcome or current funding intake was verified.
