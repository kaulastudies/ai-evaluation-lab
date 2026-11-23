# EO-001 / Evercraft alignment and independent input review

**17 November 2026 | Lab PR #51 | review support only; NOT FROZEN**

This note updates the engineering review snapshot without changing the exact
bytes of `EXPERIMENT_CONTRACT_v0.2.md`, `run_plan.proposed.json` or
`freeze_packet.proposed.json`. Historical reviews remain historical. The existing
contract is still the one joint experiment proposal; this is not a competing
run plan, a method approval or a physical/model execution authorization.

## Current review target

[Forge PR #2149](https://github.com/jgaethle10/forge-operator/pull/2149), inspected
at `70510dbc18a326c8846e5a7005aa7198a9744987`, consolidates the held-FD observer,
subtree observations, stable boot/starttime identity, negative evidence handling
and method review. It remains an open draft, not an approved executable Gate 1
runner. The previously reported broad CI issue should not be repeated as an
unresolved current-head failure: both [dedicated review CI](https://github.com/jgaethle10/forge-operator/actions/runs/43868142972)
and [full Forge CI](https://github.com/jgaethle10/forge-operator/actions/runs/43868142841)
were checked as SUCCESS at this head. Jesse's [head-specific report](https://github.com/jgaethle10/forge-operator/pull/2149#issuecomment-6916627252)
records 252 focused tests; the Lab did **not** independently rerun that full suite.

The [manager-target review](https://github.com/jgaethle10/forge-operator/blob/70510dbc18a326c8846e5a7005aa7198a9744987/integrations/ai-evaluation-lab/EO001_MANAGER_STOP_IDENTITY_REVIEW.md)
disables the native name-based systemctl stop route. The held-original-cgroup
`cgroup.kill` route is a proposed alternative with read-only survey/metadata
work, not an approved kernel write. An old StopUnit permit must not authorize
the changed method. Linux documents `cgroup.kill` as a SIGKILL-subtree control;
that is not the same operation as a graceful systemd stop. Sources:
[Linux cgroup v2](https://www.kernel.org/doc/html/latest/admin-guide/cgroup-v2.html#cgroup-kill)
and [systemd Manager interface](https://www.freedesktop.org/software/systemd/man/262/org.freedesktop.systemd1.html).
Actual installed versions, permissions and lifecycle behavior still need review.

## Small independent contribution: reproducible join-boundary probe

Rather than adding another supervisor, the Lab independently exercised the pure
`joinHeldScopeKillSurveyForReview` function with JSON-round-tripped synthetic
inputs. The source was retrieved at the immutable Forge revision and its Git
blob verified locally before import. Only this pure module is imported; it has
no dependency beyond `node:crypto`. No Forge product tree is vendored here.

| Source identifier | Value |
|---|---|
| Forge revision | `70510dbc18a326c8846e5a7005aa7198a9744987` |
| Git blob | `612f993ff555cccbe52088ed5abcbed407141bc2` |
| SHA-256 of tested upstream bytes | `5141a6cc02505c63d98d2fad9c4d1b77aeeff51022f3b5900f5ecb585df99361` |
| Local runtime | Node.js `v22.16.0`, Linux |

### Observed results, not a model score

- **12/12 existing-boundary expectations matched**, including rejection of
  mismatched source/boot/inode, reused stop permits, fabricated approval,
  name-based targeting, kernel-write/host-attestation/effective-permission claims,
  an altered write value and an unbounded resource policy.
- **Three additional proposed strict-input expectations did not match.** The
  join accepted numeric device/inode values, an agreed relative path and an
  agreed path with `..` as review-only matching metadata.
- **All returned results retained false authority/actuation flags.** No kernel
  action, host-control bypass, physical containment result or exploit was shown.

The path cases call the join directly with fabricated serialized records and
matching path digests. The upstream `reviewHeldCgroupKillAlternative` helper
already rejects these paths. These probes therefore **do not show the normal
factory/survey pipeline produces malformed paths**. They identify defense-in-depth
opportunities at an exported function that describes its input as untrusted
supplied records. Numeric regex coercion likewise affects metadata typing; it
is not evidence of a wrong-process signal or authenticated-host compromise.

### Proposed repair for Jesse's review

[Small source patch](interop/held_scope_join_input_hardening.patch): apply the
existing candidate helper's path rule at the join boundary and require the
candidate device/inode fields to be strings before regex validation. Reject
invalid values rather than normalizing evidence into an apparently valid record.
The patch does not change method semantics or authority flags.

**Local proposed-patch check: 15/15 stated expectations matched.** This result
applies only to the in-memory Lab proposal, not to upstream Forge, the complete
Forge suite or physical behavior. Jesse has not reviewed or adopted it. The
upstream result is preserved separately and is not overwritten by the patched
result. The probe additionally refused a missing argument, a changed source
file and a symlinked source (three setup checks).

Artifacts:
- [Pinned probe](interop/held_scope_join_probe.mjs)
- [Unmodified upstream result](interop/held_scope_join_probe.result.json)
- [Proposed-patch result](interop/held_scope_join_proposed.result.json)
- [Proposed source diff](interop/held_scope_join_input_hardening.patch)

Run locally from the Lab repository, supplying the exact reviewed Forge file:

```bash
node research/eo001_coordination/interop/held_scope_join_probe.mjs \
  /path/to/pinned-forge/integrations/ai-evaluation-lab/eo001-held-cgroup-kill-survey-join.mjs

node research/eo001_coordination/interop/held_scope_join_probe.mjs --proposed-guards \
  /path/to/pinned-forge/integrations/ai-evaluation-lab/eo001-held-cgroup-kill-survey-join.mjs
```

First command: exit **2**, recording the three proposed hardening gaps. Second:
exit **0**, applying the adjacent exact patch in memory only. Source/setup
mismatch: exit **3**, with a bounded error and no path dump. Both modes require
the original pinned source; the second verifies a separately pinned patched
SHA-256. Neither edits Forge files, reads procfs/cgroups, starts a child, calls a
provider, installs packages, uses private receipts or grants run permission.
These probes are deliberately separate from the existing Python contract suite;
no test totals have been combined into a larger safety claim.

## Next useful handoff, without duplicate work

| Decision | Evercraft contribution | Lab review | Still held |
|---|---|---|---|
| Choose one containment method | State the method, target identity binding, source pin, residual races and difference from the old permit | Review a method-specific contract amendment before any adoption | Neither method is approved by this note |
| Read-only capability evidence | Privacy-minimized observation at the exact intended host/kernel/source, with real limitations | Check provenance and correspondence; distinguish mode bits from effective permission | Read-only agreement is not permission or cleanup proof |
| One bounded synthetic physical test | Separately proposed worker, resource limits, observer, stop/cleanup deadlines, failure capture and genuine owner approval | Independent review of the same method/configuration and later evidence | No command to execute or implied permission is supplied here |
| Four Qwen cases | Effective parameters, model/runtime pins, prompt/context bytes and the final integrated runner | Existing v0.2 gates, 15-second whole warmed decision and six-decision budget | Only after containment evidence and joint freeze |

Do not repeat Gate 0 or the already operator-reported synthetic preflight/canary
merely to fill a new document. Keep unavailable or vanished post-stop observations
UNKNOWN, retain negative attempts, and keep genuine operator/reviewer approvals
separate from synthetic signatures or metadata completeness. No signing key is
created, provisioned or requested by this review.

## Black Box and collaboration boundary

[Forge PR #2098](https://github.com/jgaethle10/forge-operator/pull/2098) is a separate
negative-evidence projection. Its unsigned/UNKNOWN read-only output must not be
promoted to a worker-exit event, verified impact, Lab certification or recovery
permission. No Black Box runtime code or proprietary product implementation is
added here. Commercial scope, attribution and compensation remain a separate
conversation; this small review does not commit either party to broader work.
