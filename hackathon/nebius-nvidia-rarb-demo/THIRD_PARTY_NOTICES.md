# Browser runtime notices

ProofGate's application code is Apache 2.0, as specified by the repository LICENSE.

The deployed browser runtime is **Pyodide 0.27.7**, downloaded from the versioned distribution URL documented by the Pyodide project. Pyodide is distributed under the Mozilla Public License 2.0; see PYODIDE_LICENSE.txt. Its CPython 3.12.7 runtime carries the Python Software Foundation and incorporated notices in PYTHON_LICENSE.txt. The upstream distribution includes additional components under their respective terms.

The small browser-runtime.json manifest pins the URL, byte count and SHA-256 of each runtime file. prepare_browser_runtime.py verifies those hashes before installation. Runtime binaries are not checked into the main project repository; deployment includes the verified assets so judges need no third-party CDN request at execution time.

Upstream documentation: https://pyodide.org/en/0.27.7/usage/webworker.html

No proprietary model weights are distributed. NVIDIA Nemotron inference is provided through the user's Nebius Token Factory account; recorded model outputs are retained as evaluation evidence.
