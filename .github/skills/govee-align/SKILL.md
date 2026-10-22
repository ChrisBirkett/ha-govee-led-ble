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

- **Full support across revisions by default:** Always audit and plan for complete in-scope support across all hardware and firmware revisions, while preserving confirmed working behaviour.  Never call `ask_user` to ask whether to narrow an investigation or plan to a single reported bug.
- **Select mode up front:** **Read-only mode** (investigations, issue diagnosis, PR reviews) never modifies tracked files or runs mutating tracked-file generators (`make build`, `make check`, `refresh_scene_catalogues.py`).  **Implementation mode** uses a dedicated git worktree and absolute paths when other work is active.
- **Reference material (worktree-safe):** Resolve the parent directory of the main repository clone via Git and read the reference material instructions before inspecting protocol files:
  ```sh
  common_git_dir="$(git rev-parse --git-common-dir)"
  ref_dir="$(cd "$common_git_dir/../.." && pwd)/.reference-material"
  ```
  Read `$ref_dir/README.md` first and follow its confidentiality rules, lookups, entry points, and **LSP activation** workflow.
- **Efficiency rules:**
  - **Local first:** Exhaust `$ref_dir`, repository `.ksy`/`const.py`/`scene_catalogues/<MODEL>.json`, and GitHub issue/PR history before any `web_search` or `web_fetch`.  Call `web_search` at most once and only when a physical specification remains unresolved locally.
  - **No duplicate reads:** Do not call `lsp` `documentSymbol` and full-file `view` on the same small file in one turn; use `documentSymbol` on large files to locate `view_range` targets or to link files before `goToDefinition`/`findReferences`.
  - **Fast JSON/ZIP reads:** Use `python3 -c` (not `uv run python -c`) for stdlib JSON/ZIP inspection so fresh worktrees do not trigger a full `.venv` sync.
  - **No guessed `docs/` paths:** Per-model `docs/*-support.md` files do not exist; rely on `grep`/`glob`, `.ksy` `doc` headers, and `const.py`.
- **Global non-goals (`CONTRIBUTING.md`):** Never expose runtime controls, queries, or active runtime roots for AI filters, Wi-Fi provisioning/cloud control, onboard timers/schedules, phone/host microphone streaming, continuous host-driven BLE streaming, OTA updates, animated previews, or cloud camera calibration.

## 1. Research hardware reality and lookup `<MODEL>`

1. **Reference and repository lookup:** Follow `$ref_dir/README.md` and inspect existing `.ksy`, `const.py`, `scene_catalogues/<MODEL>.json`, and GitHub issue/PR context for `<MODEL>`'s product/type ID, IC/segment geometry, dynamic type-ID remapping, hardware-version family parsers, BLE local-name prefixes, and encryption eligibility.
2. **Physical device and public evidence:** Cross-check hardware geometry, dedicated white emitters, power limits, owner diagnostics, and independent third-party captures (excluding self-referential repository hits).
3. **Hardware/revision matrix:** Map `(pact_type, pact_code, hardware, firmware, subordinate_20/21)` to each capability independently.  Separate baseline capabilities safe from Pact alone (so setup and writes work if version queries time out) from capabilities requiring confirmed HW/FW versions.  Treat reference code as candidate routing, not hardware proof; flag where physical firmware diverges (unanswered queries, masked-write side effects, out-of-range stored registers).

## 2. Trace feature surfaces end to end

For each reachable feature (`revision gate -> bounds/defaults -> byte producer -> framing/ACK -> reply parser -> retained state`), compare reference behaviour against the repository:

- **Power & brightness:** `33 01`/`AA 01`; percentage `1..100` vs register `brightness_wire_range` (`(6, 254)` or `(20, 254)`), clamping non-zero readback bytes (`1..255`) into `[low, high]`.
- **Static RGB & Kelvin:** Selector (`0x15` subop `0x01`/`0x02` vs legacy `0x0b`/`0x0d`/direct RGB), Kelvin bounds, `kelvin_direct_rgb` (`(0, 0, 0)` vs `(255, 255, 255)`), companion RGB (`table_kelvin_rgb` vs formula), and whole-device vs per-segment Kelvin.
- **Geometry & segments:** `segment_count`, `whole_device_mask` width (2-byte vs 4-byte), configurable strings (`33 0F`/`AA 0F` with fresh readback confirmation), and segment readback (`AA A5` `govee_segment_page` vs `AA A2` RGB-only `govee_rgb_segment_page`, `segment_group_size`, `segment_colour_mode_ambiguous`).
- **Scenes:** Exact-SKU `scene_catalogues/<MODEL>.json`, selector `33 05 04` (1-byte vs 2-byte LE, `selector_only_scene_bits`, `scene_codes`), type-0 selector vs type-1/type-2 (`A3 02` upload + `0x04`), speed metadata (`_SPEED_METADATA_SKUS`, `_METADATA_DEFAULT_SPEED_SKUS`), and `local_scenes`.
- **Music:** Selector (`0x0c`, `0x0f`, `0x11`, `0x12`, `0x13`, or `0x05`), mode IDs, sensitivity bounds, style/direction/group/key fields, fixed colour, and `A3 41` companion upload (`music_upload_before_selector`, `music_requires_upload_ack`, `music_retry_after_upload`, `music_params_require_activation`).
- **DIY & Workshop:** Transport/body (`A1 02` `DiyType04` with `a1_diy_selector=0xFE`, `A3 04` `DiyType04`/mixed, `A3 02` `SceneBody` layered templates, `DiyType03`, or `WorkshopBody`), family/variation allowlists, rate/palette bounds, `diy_requires_upload_ack`, `diy_slot_policy`, and `effect_readback`.
- **Settings, video & DreamView:** Boolean controls (`0x0e` `limit`, `0x14`/`0xa3` `gradual`, `0x41` `power_off_memory` V1 boolean vs V2 3-state), camera/video registers and subordinate `20`/`21` gates, and DreamView (`dreamview_max_sub_devices`, operations/reads).

## 3. Audit Kaitai ownership and neighbouring code

Kaitai Struct (`.ksy`) is the single source of wire truth.  Audit `<MODEL>` and neighbouring code across `tools/ble/kaitai/`, `const.py`, `generated_protocol_adapter.py`, `music_*.py`, `scenes.py`, `effect_*.py`, `coordinator*.py`, and `light*.py`:

- **Wire structure in Kaitai only:** Command frames, status replies (`aa_domain`), upload ACKs, music/scene/companion mode enums, segment page sizes, and register bounds belong in `.ksy` (`speculative/<sku>_*.ksy` starts `doc` with `SPECULATIVE` and preserves unknown bytes without invented `valid` constraints).
- **Minimal model-specific Python:** Flag and eliminate hardcoded byte offsets, command hex literals, Python mode/scene fallback tables, `if model == ...` branches in coordinator/entity/protocol modules, and static `get_profile(model)` calls that bypass effective `device_profile()`.
- **Complete semantic loop:** Verify `named fields -> observations -> sibling preservation -> persisted recovery -> generated writes -> fresh verification` (`applied`, `preserved`, `decode-only`, or `unknown`), plus `MODEL_EFFECT_CATALOGUES` (`effect_catalogue.py`) and `RELEASE_CAPABILITY_CONTRACT` (`effect_contracts.py`).

## 4. Check, review with a second agent, and report

1. **Run verification checks:**
   - Read-only: do not run `make protocol verify-protocol`, `test_profile_wire_invariants.py`, or `generate_frontend_contract_fixtures --check` on an unmodified checkout; run targeted `pytest` only when testing a specific frame/decode hypothesis.
   - Implementation: run `make protocol verify-protocol`, add every distinct `device_profile()` outcome to `_QUALIFIED_CONTEXTS` in `tests/test_profile_wire_invariants.py`, add direct-byte frames to `tests/test_kaitai_protocol.py`, regenerate fixtures if needed, and pass `make check`.
2. **Review with another agent:** Run a `code-review` or `rubber-duck` subagent (`gpt-6-astra`) to challenge the hardware/revision findings, Kaitai boundaries, and neighbouring refactoring opportunities.
3. **Respond clearly:**
   - **If aligned:** Return a short confirmation only (checked surfaces and passing checks).
   - **If misaligned or incomplete:** Return a concise numbered list of gaps in chat, and write the full AI-actionable specification (evidence ledger, exact wire frames, `.ksy` schema changes, `ModelProfile`/`device_profile()` updates, and neighbouring code improvements) to `<session_folder>/files/align-<model>.md`.

