# SevaSetu Placement Desk — Option B

An independent, record-led placement prototype for discussion of Army Design Compendium 2025 PDS 6. A fictional candidate ID retrieves a sample register entry, separates confirmed facts from pending qualifications, compares explicit sample role requirements and prepares a CV with source references.

**[Open Option B](https://aievaluationlab.tech/sevasetu-desk/)** · **[Open the stable Option A](https://aievaluationlab.tech/sevasetu/)** · [Design and integration questions](docs/DESIGN.md)

Option A remains the candidate-led vacancy and CV demo. Option B is a separate folder and URL; it does not import or modify Option A's application code. Neither demo is an Army/AWPO service or a recruitment decision system.

## What the source supports

PDS 6 mentions CV preparation using the existing AWPO database. That supports exploring record retrieval. It does not establish the database schema, a universal ID, access to DOB/pay, existing verification quality, or an exclusively internal user. These remain questions for the responsible team. Source: [ADB/FICCI Compendium 2025, PDS 6, printed page 9](https://bharatshakti.in/wp-content/uploads/2025/02/ARMY-DESIGN-COMPENDIUM-2025-BSI.pdf).

This prototype covers one proposed ex-serviceman placement workflow. It does not claim that every AWPO service is restricted to ex-servicemen.

## Try the complete workflow

1. Retrieve `ESM-DEMO-1001` as **Placement counsellor**. DOB and pay are withheld; sources and age at the selected role cutoff are shown.
2. Open **Role checks & CV** and choose **Warehouse Supervisor**. The required certificate is not evidenced.
3. Open **Qualification review**, click **Fill sample certificate**, then **Submit for sample verification**. The new qualification stays pending and is excluded from the CV.
4. Choose **Records verifier**. Its purpose defaults to **Record verification**. Click **Check sample issuer** next to the new certificate.
5. The fictional issuer entry must match candidate ID, issuer, serial, metadata and document fingerprint. On a match, role checks and CV can use that fact. The evidence download includes claim references and the CV's SHA-256.
6. Switch back to counsellor to see the sensitive fields withheld again. Candidate mode can retrieve only `ESM-DEMO-1001`.

Other IDs: `1002` has a current post-service network certificate; `1003` has a stale snapshot, unconfirmed DOB and revoked driving licence; `1004` is still retiring; `1005` does not permit placement access. All IDs use the `ESM-DEMO-` prefix. All people, qualifications, employers, rules and issuer responses are fictional.

## Run and verify

Node 22 or later, no runtime packages:

```sh
npm start
# http://127.0.0.1:8092/
npm test
npm run evaluate
npm run check
```

The tests cover source provenance, dates, access projection, candidate ownership, qualification changes, issuer mismatches, CV exclusions, audit-chain integrity and actual HTTP requests. Seven replay cases cover supported requirements, gaps, review and closed roles. An integrity test records the seven unchanged Option A web assets from `5c1d860cf6bb3cab6c1367132b3f9c3c9f1f3e1f`.

Browser verification, with development-only tooling:

```sh
npm install --no-save --package-lock=false playwright@1.62.1
npx playwright install chromium
node tests/browser-check.mjs
```

The server must run during that command. Browser checks exercise the actual API or public static URL, the pending-to-confirmed workflow, CV/receipt downloads, denied lookups, role transitions and 1440×675 / 390×844 viewports. JSON reports and screenshots are retained as GitHub Actions artifacts by [the verification workflow](../../.github/workflows/sevasetu-desk.yml). A public run also verifies the deployed commit and every asset digest from its manifest.

## Two distinct demonstration modes

| Mode | What is demonstrated | Limit |
|---|---|---|
| Public static site | Clickable end-to-end workflow using a public fictional fixture | Role picker and field permissions are a simulation; the full fictional JSON is public. Never put real records into this build. |
| Local Node API | HTTP session, server-enforced record/purpose projection and ownership checks on the same fictional data | Role picker creates demonstration sessions. No production identity provider, issuer service or database is connected. Sessions and edits are in memory only. |

The loopback server does not serve the raw fixture. It accepts only loopback hosts and same-origin requests, uses HttpOnly/SameSite cookies, caps request bodies and limits requests. These are testable prototype controls, not a production security certification. Hash chaining makes accidental changes detectable against a retained trusted chain head; it does not stop a privileged actor rewriting the entire in-memory log.

Last pay is an optional reference field, withheld by default and never used for role suitability or CV generation. A certificate fingerprint identifies bytes; it cannot establish authenticity. Only the fictional issuer response is checked here. Real verification needs an authorised issuer/data-owner process.

Age cutoffs and qualification rules are illustrative. Results mean “documented checks met”, “evidence review needed”, “recorded requirement gap”, or “application window closed”. No person is selected/rejected and no application, credential verification request or email is sent.
