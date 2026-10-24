---
name: govee-align
description: >-
  Align a Govee BLE device model (<MODEL>) across physical hardware research, local protocol
  reference, Kaitai Struct (.ksy) schemas, and ha-govee-led-ble profile/coordinator layers.
  Use for /govee-align <MODEL>, model investigations, user-reported device issues, new model
  candidates, and contributor compatibility PRs.
license: MIT
---

# govee-align

Take `<MODEL>` (an exact SKU such as `H6076`, `H6125`, `H7020`, `H7025`, `H60A1`, or `H66A0`, plus any reported BLE local name, `pact_type`/`pact_code`, hardware/firmware versions, diagnostics, or issue/PR context).  Reconcile physical hardware reality, public evidence, and local protocol reference against Kaitai schemas, `ModelProfile`, and shared runtime code.

## Boundaries and reference material

- **Full support across revisions by default:** Always audit, plan, and enable all defensible in-scope features across all hardware and firmware revisions, while preserving confirmed working behaviour and safety guards.  Never call `ask_user` to ask whether to narrow scope to a single reported bug or whether to keep structurally evidenced capabilities disabled until hardware qualification.
- **Select mode up front:** **Read-only mode** (investigations, issue diagnosis, PR reviews) never modifies tracked files or runs mutating tracked-file generators (`make build`, `make check`, `refresh_scene_catalogues.py`).  **Implementation mode** uses a dedicated git worktree and absolute paths when other work is active.
- **Reference material (worktree-safe):** Resolve the parent directory of the main repository clone via Git and read the reference material instructions before inspecting protocol files:
  ```sh
  common_git_dir="$(git rev-parse --git-common-dir)"
  ref_dir="$(cd "$common_git_dir/../.." && pwd)/.reference-material"
  ```
  Read `$ref_dir/README.md` first and follow its confidentiality rules, lookups, entry points, and **LSP activation** workflow.
- **Efficiency rules:**
  - **Decision-led, local-first research:** Start with local reference material, repository code and issue/PR evidence.
    Reuse cited findings after checking relevant checkout, source-version and owner-context changes.
    Stop deepening settled traces; record the specific missing evidence and next discriminating check for unresolved decisions.
    Use targeted authoritative public/upstream sources for remaining questions, including transport failures, under the reference confidentiality rules.
  - **Batch searches and file slices:** `grep` for target functions/constants first, then read all needed `view_range` slices across files in one parallel turn rather than paging one slice per turn.
  - **No duplicate reads:** Do not call `lsp` `documentSymbol` and full-file `view` on the same small file in one turn; use `documentSymbol` on large files to locate `view_range` targets or to link files before `goToDefinition`/`findReferences`.
  - **Fast JSON/ZIP reads:** Use `python3 -c` (not `uv run python -c`) for stdlib JSON/ZIP inspection so fresh worktrees do not trigger a full `.venv` sync.
  - **No guessed `docs/` paths:** Per-model `docs/*-support.md` files do not exist; rely on `grep`/`glob`, `.ksy` `doc` headers, and `const.py`.
- **Global non-goals (`CONTRIBUTING.md`):** Never expose runtime controls, queries, or active runtime roots for AI filters, Wi-Fi provisioning/cloud control, onboard timers/schedules, phone/host microphone streaming, continuous host-driven BLE streaming, OTA updates, animated previews, or cloud camera calibration.

## 1. Research hardware reality and lookup `<MODEL>`

Maintain a concise, revisable inventory of the full in-scope feature and revision surface, including paths not currently exposed.
Prioritise unresolved decisions and the reported failure's causal path without reducing coverage.
Add newly discovered routes and retain unresolved or deferred findings; locating the failing stage does not establish its cause.

1. **Reference and repository lookup:** Follow `$ref_dir/README.md` and inspect existing `.ksy`, `const.py`, `scene_catalogues/<MODEL>.json`, and GitHub issue/PR context for `<MODEL>`'s product/type ID, IC/segment geometry, dynamic type-ID remapping, hardware-version family parsers, BLE local-name prefixes, and encryption eligibility.
2. **Physical device and public evidence:** Cross-check hardware geometry, dedicated white emitters, power limits, owner diagnostics, and independent third-party captures (excluding self-referential repository hits).
3. **Hardware/revision matrix:** Map `(pact_type, pact_code, hardware, firmware, subordinate_20/21)` to each capability independently.  Separate baseline capabilities safe from Pact alone (so setup and writes work if version queries time out) from capabilities requiring confirmed HW/FW versions.  Treat reference code as candidate routing, not hardware proof; flag where physical firmware diverges (unanswered queries, masked-write side effects, out-of-range stored registers).

## 2. Trace feature surfaces end to end

For each in-scope feature, trace revision admission, bounds/defaults, producer/body, framing/transport, activation, acknowledgements, observations and recovery.
Catalogue type, body family and wire subtype are independent routing decisions.
Establish upload-ACK behaviour separately from status readback; status-query silence does not imply either ACK policy.
The headings and identifiers below are non-exhaustive lookup anchors, not the limits of the investigation.  Keep exact wire rules in Kaitai and attributable session evidence.

- **Power & brightness:** Input versus register bounds (`brightness_wire_range`), conversion, clamping and non-zero readback handling.
- **Static RGB & Kelvin:** Selector, Kelvin bounds, direct and companion RGB (`kelvin_direct_rgb`, `table_kelvin_rgb`), and whole-device versus per-segment behaviour.
- **Geometry & segments:** Physical, installed and logical counts; `segment_count`, mask width, grouping and readback ambiguity.
  Confirm configurable geometry through fresh readback before constructing masked writes.
- **Scenes:** Exact-SKU catalogue, selector width/eligibility (`scene_codes`, `selector_only_scene_bits`, `local_scenes`), body routing, upload versus selector-only activation,
  and exact-model speed metadata/defaults.
- **Music:** Exact selectors/mode IDs, sensitivity and style/direction/group/key bounds, fixed colour, companion bodies, upload ordering, ACKs, retries and parameter activation.
- **DIY & Workshop:** Body/transport, family/variation allowlists, rate/palette/layer bounds, upload ACKs, slot safety (`diy_slot_policy`) and restoration (`effect_readback`).
- **Settings, video & DreamView:** Exact control eligibility, boolean versus enum values, query/write semantics, subordinate-version gates and group capacity
  (`dreamview_max_sub_devices`).

## 3. Audit Kaitai ownership and neighbouring code

Kaitai Struct (`.ksy`) is the single source of wire truth.  Audit `<MODEL>` and neighbouring code across `tools/ble/kaitai/`, `const.py`, `generated_protocol_adapter.py`, `music_*.py`, `scenes.py`, `effect_*.py`, `coordinator*.py`, and `light*.py`:

- **Wire structure in Kaitai only:** Command frames, status replies (`aa_domain`), upload ACKs, music/scene/companion mode enums, segment page sizes, and register bounds belong in `.ksy` (`speculative/<sku>_*.ksy` starts `doc` with `SPECULATIVE` and preserves unknown bytes without invented `valid` constraints).
- **Minimal model-specific Python:** Flag and eliminate hardcoded byte offsets, command hex literals, Python mode/scene fallback tables, `if model == ...` branches in coordinator/entity/protocol modules, and static `get_profile(model)` calls that bypass effective `device_profile()`.
- **Complete semantic loop:** Verify `named fields -> observations -> sibling preservation -> persisted recovery -> generated writes -> fresh verification` (`applied`, `preserved`, `decode-only`, or `unknown`), plus `MODEL_EFFECT_CATALOGUES` (`effect_catalogue.py`) and `RELEASE_CAPABILITY_CONTRACT` (`effect_contracts.py`).

## 4. Check, review with a second agent, and report

1. **Run verification checks:**
   - Read-only: do not run `make protocol verify-protocol`, `test_profile_wire_invariants.py`, or `generate_frontend_contract_fixtures --check` on an unmodified checkout; run targeted `pytest` only when testing a specific frame/decode hypothesis.
   - Implementation: run `make protocol verify-protocol`, add every distinct `device_profile()` outcome to `_QUALIFIED_CONTEXTS` in `tests/test_profile_wire_invariants.py`, add direct-byte frames to `tests/test_kaitai_protocol.py`, regenerate fixtures if needed, and pass `make check`.
2. **Review with another agent:** Run a `code-review` or `rubber-duck` subagent (`gpt-6-astra`) to challenge the hardware/revision findings, Kaitai boundaries, and neighbouring refactoring opportunities.  Pass exact file/line citations and instruct the reviewer not to re-invoke `govee-align` or repeat full reference discovery.
3. **Respond and plan clearly:**
   - **If aligned:** Return a short confirmation of coverage and only checks actually performed.  Unfinished coverage is not aligned.
   - **If gaps or uncertainty remain:** Report confirmed gaps alongside unresolved conclusions and unexamined scope.
     Distinguish unexamined, investigated-but-unresolved and not-hardware-qualified; absent owner qualification alone does not withhold defensible candidates.
     Keep evidence, attributable frames, affected schema/profile/runtime paths and intended checks in `<session_folder>/files/align-<model>.md`.
     Identify the next discriminating evidence for unresolved conclusions instead of prescribing unsupported fixes.
   - **Consistent handoff:** Keep one current decision per capability/revision context, or mark it unresolved.
     Reconcile changed decisions across the specification, any plan and intended tests before implementing the affected path.
     Retain contrary evidence, reasons for supersession and deferred findings without leaving competing current instructions.
   - **When planning an implementation:** Include the four-section `CONTRIBUTING.md` plan and the complete delivery handoff: independent code review, `make check`, draft PR/comment approval, opening a PR linked to the issue (`Fixes #<issue>`, exact SKU label), passing CI, and rebase-merging to `master`.
