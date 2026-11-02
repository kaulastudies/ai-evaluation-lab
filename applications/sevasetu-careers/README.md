# SevaSetu Careers

**Search civilian roles for ex-servicemen, check requirements, and prepare a CV from candidate-supplied facts.**

[Open the working demonstration](https://kaulastudies.github.io/ai-evaluation-lab/sevasetu/) · [Design and requirement mapping](docs/DESIGN.md) · [Pilot proposal](docs/PILOT.md) · [Reproducible fixture evidence](evidence/offline-evaluation.json)

SevaSetu Careers is an independent AI Evaluation Lab prototype addressing **PDS 6, printed page 9, Army Design Compendium 2025**. The published problem asks for an ex-servicemen job aggregator and CV-generation application. This project is not commissioned, approved or deployed by the Indian Army, DIO, iDEX or AWPO. It makes no claim about a current application window.

## Try it

The demonstration contains **synthetic people, employers and vacancies**, frozen at **2 November 2026**. It does not advertise real jobs. Candidate edits remain in memory in the current tab; reload resets them. Explicit downloads are the only profile persistence.

1. Open the [demonstration](https://kaulastudies.github.io/ai-evaluation-lab/sevasetu/).
2. Review Warehouse Coordinator and its requirement checks. Turn on the deadline review queue to inspect an unknown deadline.
3. Open Candidate profile, switch to the IT or healthcare sample, then save.
4. Build a CV for a role. Download the plain-text CV and claim-evidence receipt, or print to PDF.
5. Under How it works, run the five fixture checks.

## Run locally

Requires **Node.js 22 or later**. The application has no npm runtime dependencies, API key, account, external font or model download.

```sh
git clone https://github.com/kaulastudies/ai-evaluation-lab.git
cd ai-evaluation-lab/applications/sevasetu-careers
npm start
```

Open `http://127.0.0.1:8090`. The development server binds to loopback only and serves the `web/` directory. Stop with Ctrl+C. These commands also work in PowerShell. To choose a port in PowerShell, use `$env:PORT=8091` before `npm start`.

```sh
npm test
npm run check
npm run evaluate
```

Optional browser automation is in `tests/browser-check.mjs`. In a separate test environment, install Playwright (`npm install --no-save playwright` and `npx playwright install chromium`), start the application, then run `node tests/browser-check.mjs`. `SEVASETU_BASE_URL` selects another deployment. `SEVASETU_SCREENSHOTS` selects an output directory. These are development checks; Playwright is not an application dependency.

The test suite covers source lifecycle, conflicting duplicates, qualification gaps, CV traceability, unsupported model output and network-source restrictions. Evaluation uses three author-labelled synthetic candidates. It does **not** establish real-world ranking quality, fairness, placement outcomes or live-model performance.

## What works

| Function | Implementation |
| --- | --- |
| Vacancy aggregation | CLI adapters for explicitly configured public HTTPS JSON feeds and Schema.org JobPosting JSON-LD pages. Browser import of a local JSON export. |
| Source discipline | Canonical URLs; source observations; tracking-URL and role deduplication; rejected-record and source-failure reports. No fake fallback jobs on failures. |
| Deadline checks | Expired/withdrawn listings and source snapshots older than seven days are withheld. Unknown, future-dated or conflicting records require review. Date-only deadlines use end of day in India. |
| Candidate matching | Transparent skill aliases, corpus-derived TF-IDF text relevance, location and explicit structured requirements. Search-query terms filter the result set. Missing qualifications remain visible. |
| CV preparation | Candidate fact selection, ordering and verbatim rendering. Plain-text export, browser print/PDF and SHA-256 receipt with a fact ID for every claim. |
| Optional local AI | Ollama structured-output adapter selects fact IDs; deterministic validation rejects extra prose, unknown IDs and duplicate claims. Education and licences are preserved by the application outside model selection. |

The browser path is an explainable retrieval and template baseline, not a trained semantic model. The optional local-model path has been exercised with a real Qwen2.5 0.5B model on CPU: three synthetic fact-selection cases passed after the follow-up described in the [live validation report](evidence/LIVE_VALIDATION.md). Public-URL desktop/mobile and real HTTPS ingestion checks also passed. These are scoped integration checks, not real-candidate ranking or placement results. It cannot rewrite candidate claims: this deliberately limits fluency to preserve fact boundaries. The receipt proves correspondence and detects changes; it does not prove that a candidate's claims are true.

## Import a vacancy source

Only configure endpoints you are allowed to use. No login bypass, AWPO account scraping or candidate-database access is implemented. AWPO/DGR live integration requires an agreed feed or export and has not been established.

The included `sources.example.json` fetches this repository's **synthetic fixture**, not an official vacancy feed:

```sh
node scripts/ingest.mjs sources.example.json imported-jobs.json
```

That fixture deliberately contains one invalid record, so the command writes the qualified records and report **and exits 1** to draw attention to the rejection. Import `imported-jobs.json` through the browser's Import vacancies button. The importer preserves existing snapshot dates; re-importing an old export does not make it fresh.

A source configuration needs `name`, `url`, `format` (`json` or `jsonld`) and an explicit `allowed_hosts` list. Sources are limited to 20, responses to 2 MB and 10 seconds. The fetcher rejects redirects, local/private/reserved destinations, credentials and unapproved ports, and pins the checked DNS address. It does not automatically crawl search results or follow links. Complete source loss produces `status: failed`; partial loss is explicit and never advertised as complete coverage.

The normalised JSON interchange format is:

```json
{
  "jobs": [{
    "id": "source-vacancy-1",
    "title": "Stores Assistant",
    "employer": "Example employer",
    "url": "https://employer.example.org/jobs/1",
    "location": "Varanasi",
    "skills": ["inventory", "excel"],
    "esm": true,
    "posted_at": "2026-11-01",
    "valid_until": "2026-11-20",
    "observed_at": "2026-11-02T08:00:00Z",
    "requirements": {
      "education": "10+2",
      "min_years": 2,
      "skills": [],
      "certificates": [],
      "review_required": true
    }
  }]
}
```

`esm: true` means the source explicitly lists an ESM opportunity, not that every ESM candidate is eligible. Unknown ESM eligibility is `null`; it is excluded by the default ESM-only filter. JSON-LD imports deliberately keep full eligibility in manual review. Requirements such as age, disability accommodation, medical fitness, rank, trade, citizenship, application mode and equivalence are not automatically resolved. They need source-specific structured fields and user validation in a pilot.

## Generate a CV from the CLI

```sh
node scripts/cv.mjs web/data/profile.example.json web/data/jobs.json sample-warehouse candidate-cv.txt
```

This creates a CV and `candidate-cv.txt.receipt.json`. For the optional AI selector, start Ollama separately, install a model suitable for your hardware, and append its exact installed model name:

```sh
node scripts/cv.mjs web/data/profile.example.json web/data/jobs.json sample-warehouse candidate-cv.txt your-installed-model
```

Only `http://127.0.0.1:11434` is used by the CLI. Candidate name and contact are excluded from the model prompt; the supplied fact text is still personal information and remains visible to your local model service. If the model fails or returns an invalid selection, the command exits without writing a new CV; there is no silent fallback or claim of successful inference.

## Boundaries and next validation

This is a functional prototype for a capability discussion and supervised pilot. It has no authorised AWPO integration, actual candidate trial, verified credential service, production authentication, hosted profile database, trained multilingual ranker or recruitment integration. English UI and a small explicit English/Hindi skill-alias dictionary are implemented; this is not general Hindi language support. It never applies for a job or sends an email.

See the [live verification workflow](https://github.com/kaulastudies/ai-evaluation-lab/actions/workflows/sevasetu-live.yml) and [recorded live results](evidence/LIVE_VALIDATION.md). It uses actual network requests and real CPU inference with synthetic records. The original offline report remains available separately.

The next partner contribution is access to a consented, minimal candidate export and approved vacancy data; confirmation of the problem's current ownership and availability; and a counsellor who can review requirement interpretations. The [pilot plan](docs/PILOT.md) gives proposed acceptance criteria, not achieved results or a funding commitment.

Code is licensed under the repository's [Apache-2.0 licence](../../LICENSE). All fixture people, employers and vacancies are fictional.
