# Local responsive QA fixture

This isolated harness renders the actual ProofPay component and CSS. Every record is synthetic. All fetch calls stay in the fixture entry; mutations return an explicit read-only error. External anchor navigation and downloads are blocked by fixture-only guards, including the detached anchor used for evidence export. A visible outer QA status explains the blocked action. This does not test hosted authentication, PayPal, model calls, backend behavior, real evidence downloads or touch emulation. Production source and runtime data are unchanged.

## Build and run

Canonical location: `tests/responsive` inside the ProofPay app. From the app root, reuse its installed dependencies:

```sh
node tests/responsive/build.mjs
sites-preview start /absolute/path/to/proofpay/tests/responsive
```

Use your checkout's absolute path in the preview command if different. The build resolves the app root two directories above its own folder. An isolated copy can select another app explicitly:

```sh
PROOFPAY_APP_ROOT=/absolute/path/to/proofpay node /absolute/path/to/fixture/build.mjs
sites-preview start /absolute/path/to/fixture
```

Open only the exact CLI-returned URL in the cloud browser. The managed daemon owns one preview. Use `sites-preview status` for diagnostics and `sites-preview stop` before switching checkouts or when finished. Do not launch a separate server. Refresh the outer page after a static rebuild.

The outer controls set a real iframe CSS viewport at 360, 390, 768 or 1280 pixels. Scenarios cover mixed states, checkout, manual review, empty states, and PayPal return/cancel matching. Inspect navigation, no-match search, purchase drawers, cancellation confirmation, focus order, evidence details and long references. Sandbox-shaped records are also synthetic.

## Read-only width diagnostics

The panel below the frame reports actual iframe innerWidth, document/body clientWidth and scrollWidth, main-container widths, visible-dialog widths and the table scroll container. It lists right-edge candidates outside horizontal scrolling containers, including below-viewport and zero-height elements. Visible and offscreen positioned candidates are also separated. Pseudo-elements are reported by computed style only; their rectangles are not inferred.

A ResizeObserver updates dimensions; a MutationObserver registers newly rendered elements. Neither changes the product DOM. Document overflow uses 1px rounding tolerance. Wider content within a table's overflow-x:auto container differs from whole-document overflow. These measurements are not evidence of real payments or hosted integration.

## Inputs and portability

The build reuses the selected app's node_modules, installs nothing and writes only the harness's ignored dist folder. Required packages: esbuild, React, React DOM, lucide-react, PostCSS, @tailwindcss/postcss and Tailwind CSS. The production component uses the proofpay-component build alias. The next/link import uses the local anchor shim. Fixture source contains no absolute app import. static/ holds wrapper HTML, fixture HTML and diagnostic JavaScript.

dist/source-fingerprint.json records production source paths and SHA-256 hashes, harness-file paths and hashes, dependency input hashes and versions, Node version, timestamp and generated JS/CSS hashes. Use identical source/dependency inputs to reproduce assets; each fingerprint intentionally records a new build time. Compiled output and archives are gitignored.

## Standalone snapshot

After building:

```sh
node tests/responsive/package.mjs
```

This creates proofpay-responsive-qa-static.tar.gz beside package.mjs. Sorted archive entries, zero timestamps and normalized ownership produce repeatable archives from unchanged built files. It includes generated assets, source wrapper, diagnostics, fingerprint, static manifest and instructions. It excludes node_modules, runtime data, credentials and the production checkout.

Extract into an empty folder beneath /workspace and run sites-preview start with that absolute folder. Serving the built snapshot requires no package installation. Rebuilding an extracted copy requires PROOFPAY_APP_ROOT pointing to an installed app checkout.
