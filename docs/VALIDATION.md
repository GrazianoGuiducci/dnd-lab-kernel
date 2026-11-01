# What has been exercised

Lab 0.1.0a3 is an alpha release. Its software support and its cognitive
exercise have different evidence scopes.

## Software contracts

Run `python -m unittest discover -s tests -v`. The 35 tests cover source and
event integrity, conditional memory contact, reopening changed contracts,
AGENTS/BOOT participation, monitoring and bridge transport limits. The test
bridge is deterministic; these tests do not establish cognitive behaviour.

The two release regressions reject a missing required wheel and a wheel
containing a stale receiving entry. CI builds the wheel and runs
`python tools/build_release.py --require-wheel` on Windows and Linux with
Python 3.11 and 3.13. The builder compares every packaged Python source and
semantic resource with the selected source before writing release artifacts.
Release verification also installs the wheel outside the checkout and reads
the corrected cognitive entry through the installed consumer.

A local upgrade fixture from the published 0.1.0a2 wheel to 0.1.0a3 preserves
the receiving Lab identity, sources, retained competence and original event
deposit. A pending contact prepared with the old entry is rejected; a fresh
contact under the corrected contract completes. This exercises installed
software and synthetic transport, without a cognitive provider.

## Historical cognitive exercise — 0.1.0a2

On 31 October 2026, six fresh native Codex CLI sessions were exercised through
the a2 stdio bridge, with the selected model gpt-6.1-sol. No prior conversation
or original Lab corpus was supplied. These are new contexts on the same
service, not independent model families; actual provider routing is not
observable in the CLI trace.

One contact reconstructed an exact affine calibration from synthetic samples
and retained its method, coefficients, reasons and applicability conditions.
A later contact, opened by a new process, received that competence on a
different question: determine whether new monitoring scores cross a threshold.

The initial transfer remained indeterminate because continuity of the
instrument and its calibration contract had not been explicitly established.
A declared follow-up added that applicability relation, without supplying
coefficients or expected results. The receiver then used the retained formula
`z = (3*u - 2*v + 11)/7` and correctly classified all five new rows:

| u | v | z | z >= 4 |
|---:|---:|---:|---|
| 2 | 3 | 11/7 | no |
| 5 | 1 | 24/7 | no |
| 8 | 0 | 5 | yes |
| 4 | -3 | 29/7 | yes |
| 9 | 6 | 26/7 | no |

A matched fresh session given the same updated source and question without
the competence left every score indeterminate. A different instrument mode
also remained indeterminate: the receiver used the competence's conditions
to withhold unsupported coefficient transfer.

This supports local reuse of retained, source-specific operational knowledge,
including its limits. It does not show that the model learned affine algebra
from scratch, discovered the competence without host selection, updated its
weights, or achieved general autonomy. The follow-up and matched control were
adaptive, not independent preregistered replications. There was no comparison
against a kernel-free receiver, and the two Lab identities/catalogues differ.

The exercise used the executable support and five semantic guides of
0.1.0a2. Its evidence remains attributed to that version; the corrected
receiving entry in 0.1.0a3 has its own software and installation checks above.
Original research sources and private operational records are not included.
Retained knowledge is reachable; its contribution must still be understood
in each later contact.
