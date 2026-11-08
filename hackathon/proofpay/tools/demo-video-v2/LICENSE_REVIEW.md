# Neural narration source and licensing review

Checked 8 November 2026 against the publishers' own pages. This is a technical provenance record, not an independent legal opinion.

| Component | Publisher source | Stated license / role |
|---|---|---|
| Kokoro-82M v1.0 weights | https://huggingface.co/hexgrad/Kokoro-82M | Apache-2.0; model card explicitly discusses production deployment |
| Kokoro reference code | https://github.com/hexgrad/kokoro | Apache-2.0 |
| kokoro-onnx 0.6.1 | https://github.com/thewh1teagle/kokoro-onnx | MIT; repository separately identifies the Kokoro model as Apache-2.0 |
| Official English voice list | https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md | `af_heart` is an English preset; chosen without user voice cloning |
| ONNX download instructions | https://github.com/thewh1teagle/kokoro-onnx/blob/main/examples/save.py | Exact release asset URLs used below |

License texts and the publisher model/voice cards are retained in `licenses/`. The model card includes training-dataset acknowledgements for Koniwa and SIWIS; keep the publisher attribution when distributing a model package. No upstream binary, voice library or model weights should be committed to ProofPay merely to publish the narration pipeline. The generated sample is local inference output, not a paid hosted service result.

## Downloaded artifacts

Both assets were downloaded from the public release URLs linked by the publisher's example, with no account, credential, API call or payment. The hashes below are computed local integrity fingerprints, not a claim of publisher signing.

- `https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.onnx`
  - 325,505,369 bytes
  - SHA-256 `beb0d1848dee9a49da392cc3df26958d46cfa35d321edf434f52949153f0df3a`
- `https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin`
  - 28,214,398 bytes
  - SHA-256 `bca610b8308e8d99f32e6fe4197e7ec01679264efed0cac9140fe9c29f1fbf7d`

Dependencies live in the isolated local `.venv`, with versions recorded in `requirements-lock.txt`. Inference explicitly selects ONNX Runtime's CPU provider. The environment has 9 logical CPUs and no detected CUDA GPU. The 19.219-second `af_heart` audition took 7.019 seconds of local inference with four ONNX threads. It makes no hosted AI request and consumes no personal OpenAI credits.

The audio uses the pretrained `af_heart` preset. It does not claim to be Rama Chandra M, a PayPal employee or any other identified person. Pronunciation input spells ProofPay as “Proof Pay” and PayPal as “Pay Pal”; visible text keeps the product names.

## Avatar decision

The rejected Flite narration and illustrated presenter are not used in v2.

MuseTalk's publisher recommends a CUDA/PyTorch setup and reports its headline real-time performance on an NVIDIA Tesla V100: https://github.com/TMElyralab/MuseTalk. No such GPU is available here. A new photorealistic avatar would add unverified quality, runtime and source-portrait requirements. The selected direction is a narrated product demonstration with readable actual UI, purposeful detail views and clear transitions between simulation and saved sandbox evidence.

No external avatar service was called. No photorealistic lip-sync quality or performance is claimed. The 19.8-second MP4 is a voice/layout quality sample, not the final portal demonstration or a new live payment recording.

## Telemetry correction

The first full narration attempt was stopped by automatic approval review after ONNX Runtime attempted an unexpected Microsoft telemetry connection. That connection was outside the offline task. Both synthesis scripts now call `onnxruntime.disable_telemetry_events()` immediately after importing ONNX Runtime and before importing the Kokoro wrapper or creating an inference session. The function is documented by the publisher at https://onnxruntime.ai/docs/api/python/api_summary.html#onnxruntime.disable_telemetry_events. The stopped attempt is not treated as a completed offline run.


The documented telemetry switch did not prevent a second observed connection attempt, and that run was also rejected. No further inference was retried with that configuration alone. `offline_guard.py` now adds a stricter per-process kernel filter before importing ONNX or Kokoro: inherited non-stdio descriptors are closed; standard streams must not be sockets; no-new-privileges is set; socket, connection, send and io_uring syscalls return EPERM. Direct native AF_UNIX, IPv4, IPv6 and connect self-tests must pass before model loading. The guard cannot relax the host's security policy. It applies to the inference process and its descendants only.

Linux network namespaces and optional ptrace/strace auditing are unavailable under the host policy; neither was bypassed. The installed seccomp guard's native self-tests establish that new connections are denied. The outcome or payload of the earlier rejected connection attempts is not known, and this record does not claim that those attempts were network-free.
