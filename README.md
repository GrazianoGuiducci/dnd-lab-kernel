# Lab

**A reusable research and monitoring kernel that can change how it continues.**

Lab brings together a receiving cognitive entity, its context and sources,
temporary attention, open resultants and continuing competences. It can
investigate varied questions, observe a system over time, and let the work
change its methods and ways of recognising the next situation.

Version **0.1.0a2 — alpha release**, distributed under the MIT license. The name remains Lab.
[Italiano](README.it.md).

[Download 0.1.0a2](https://github.com/GrazianoGuiducci/dnd-lab-kernel/releases/tag/v0.1.0a2) · [Research Lab on MAIOS](https://maios.it/research-lab.html).

## What you receive

* **A semantic kernel:** AGENTS.md, BOOT.md, KERNEL.md, CONCEPTS.md and COMPETENCES.md
  explain the operating logic, concept formation, autological correction and
  generation/evolution of capabilities. A compatible AI host can use this
  knowledge through its own tools and continuing project context.
* **Runnable local support:** Python 3.11+, with no runtime dependencies.
  It preserves sources and exact events, brings selected knowledge into the
  next contact, supports observation of changing JSON snapshots and can drive
  bounded autonomous occurrences through a receiver-configured stdio bridge.

The cognitive host understands and forms the research. The Python program
maintains its contact, state and provenance. The host can develop additional
methods, tools or kernel forms as the work makes them useful. This package
does not depend on the original Lab, a central service or a selected vendor.

## Start with an AI host

Open this directory in your AI workspace and enter through **AGENTS.md** and
**BOOT.md**. Give the Lab the context or system you want to observe. It forms
the useful movement with the means available in that environment.

For a host that receives one instruction document, `python lab.py kernel`
prints the semantic core without creating state. A local Python environment
can also install this directory with `pip install .`; the `dnd-lab` command
exposes the same support and includes the semantic resources. When editing
the semantic source, run `python tools/sync_kernel.py` before building and
verify the source/resource correspondence.

In the source tree these five readable documents are the live authority for
instructions and contact identity. Installed wheels use the corresponding
bundled resources. The same complete entry, including Boot, reaches a stdio
receiver and `kernel` output. A material edit invalidates a pending contact
and makes an already completed contact available under the changed contract.

To use the local support, choose a new directory for this receiving instance:

```sh
python lab.py --state ./my-lab status
python lab.py --state ./my-lab observe --id system --file examples/system.json
python lab.py --state ./my-lab prepare --focus system > contact.json
```

The contact contains the selected sources, contacted competences, reachable
index, requested event identity and current contract. The host returns one
JSON occurrence using that exact `event_id`:

```json
{"schema":"dnd.lab.occurrence.v1","event_id":"copy-the-event-id-from-contact","resultant":"What occurred"}
```

Save it as `occurrence.json`, then receive it:

```sh
python lab.py --state ./my-lab record --packet-file contact.json --event-file occurrence.json
python lab.py --state ./my-lab available
python lab.py --state ./my-lab verify
```

Only identity, JSON integrity and a non-empty resultant are required by the
occurrence contract. Optional unfamiliar fields remain in the exact deposit.
The machine checks that the contacted state has not changed before committing.
This is transport coherence, not a judgment of scientific truth.

## Memory and generative continuation

COMPETENCES.md explains optional `memory_effect`, `field_effect` and
`next_relation`. Retained knowledge is content-addressed: two distinct methods
do not overwrite one another because they share a label. Records include
source contact and provenance. Cooling removes a form from automatic
attention while its deposit remains recoverable.

Use `available` and `competence --id ID` to discover and inspect retained
knowledge. `prepare --competence ID` selects a relevant method for another
question or source; activation IDs also support automatic contact. A receiver
understands applicability and can transform the method rather than repeating
an earlier conclusion. A new capability can itself change how later
capabilities are formed.

## Observe a system

A producer can supply a JSON snapshot of its system. Observation reads that
file; no command from the snapshot is executed:

```sh
python lab.py --state ./monitor watch --id service --file examples/system.json --ticks 3 --interval 1
```

Without a bridge this records observations only. Key ordering and JSON
whitespace do not manufacture a content change. A changed value is a content
difference for the receiver to interpret; the hash does not infer meaning.
Sources can declare `--related ID` relations; missing related objects remain
expressly unresolved. Exact versions are recoverable with `source --revision`.

## Connect autonomous cognition

Supply your own trusted bridge program, whose **stdin** receives
`{"instructions": "...", "contact": {...}}` and whose **stdout** returns
one JSON occurrence. A provider config is a local JSON file:

```json
{"command":["python","/absolute/path/to/your_bridge.py"],"allow_env":[],"timeout_seconds":120}
```

The command is an argument list, executed without a shell. Ambient credentials
are removed; explicitly selected `allow_env` names can supply the bridge's
own credentials. Put no credential values in the config. The bridge receives
the selected contact data and runs with the receiver's OS permissions; it is
not an OS sandbox. It owns any provider/network use it performs.

Output is drained incrementally. The default stdout collection is bounded to
4 MiB; stderr is counted and discarded, with a default 64 KiB ceiling. Override
these byte ceilings with positive `max_stdout_bytes` / `max_stderr_bytes` in
the receiver-owned config. Exceeding either ceiling interrupts the direct
bridge process and records a transport incident without a research event.
No arbitrary stderr is exposed in controller errors. Input, JSON decoding and
Python overhead are additional memory; this is not a total process-RAM cap.
The controller does not sandbox or guarantee termination of a descendant
process tree. Use a trusted bridge and host-owned OS isolation where needed.

```sh
python lab.py --state ./my-lab run --provider-file provider.json --occurrences 3
python lab.py --state ./monitor watch --id service --file snapshot.json --provider-file provider.json --ticks 3
```

The receiver chooses the bridge, budgets and automation. No provider or
scheduler is configured by installation. Transport incidents are recorded
without producing research events or silently repairing the answer. A later
explicit invocation can try again. Already observed unchanged contact returns
to potential without calling the bridge. Changing an unrelated source does
not reopen a fixed focus; changed relevant knowledge or profile can do so.

`--occurrences` and `--seconds` bound each run's opportunities to open another
occurrence. In watch mode each tick can offer such a run. `--interval` is the
gap between observation ticks; the bridge's `timeout_seconds` bounds one
transport attempt. Those clocks do not certify novelty or scientific value.

## Boundaries and development

State lives in your selected directory, in a local SQLite database. Events and
source versions are append-only through this implementation; verification
recomputes their digests. The file owner still controls the database. There
is no automatic upload, public export, deployment or administration of the
observed system. Keep receiver data separate from a distributable package.

[ARCHITECTURE.md](ARCHITECTURE.md) describes the causal path and implemented
scope. Run `python -m unittest discover -s tests -v` for local contract checks.
The fixture bridge in tests verifies the machine, not a reasoning model's
autopoietic capacity. [Validation notes](docs/VALIDATION.md) keep those evidence levels distinct.

## Origin and rights

Formed from the current D-ND regenerative Lab's functional relations, with
Graziano Guiducci's direction on research, monitoring and Entity evolution.
The original Lab retains its own private sources and operational continuity.
[Its public history and companion](https://github.com/GrazianoGuiducci/dnd-lab-physics)
and [the separate D-ND_LAB engine](https://github.com/GrazianoGuiducci/D-ND_LAB)
keep their respective identities. This receiving package contains new neutral
texts and implementation, with no original prompts, deposits or credentials.

This receiving package is distributed under the [MIT License](LICENSE).
The license covers the files in this repository; it does not change rights on
original sources, corpora or historical repositories.
