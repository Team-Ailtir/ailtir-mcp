# Tender discovery tools (system path)

These tools back the Phase 0 tender-discovery pipeline (Paperclip
`discovery-controller` / `scoring-controller` skills). Unlike the
user-facing tools in [Usage](usage.md), they call `god` directly with the
shared `GOD_SERVICE_TOKEN` rather than going through `api-mcp` with a
per-user `AILTIR_MCP_API_TOKEN` — there is no logged-in user driving these
calls, only a scheduled discovery/scoring run. See `CLAUDE.md` for the two
call-path rationale.

Configuration adds two required env vars: `GOD_URL` (the `god` service base
URL) and `GOD_SERVICE_TOKEN` (the shared token gating `god`'s system-path
write endpoints).

## Tender notices

### `tender_notice_upsert(tenant_id, source, resource_id, portal_url, listing, detail?, authority_name?, cpv_codes?, procurement_type?, deadline?, published_at?)` → `TenderNotice`

Creates or updates a canonical tender notice. Idempotent on `(source,
resource_id)` — calling this again for the same notice updates it in place.

### `tender_notice_classify(notice_id, classification)` → `TenderNotice`

Stores the LLM classification result (sector, region, engagement, CPV
codes) and advances the notice to `classified` status. Pass
`{"failed": true}` on a classification failure so scoring can degrade
gracefully instead of blocking the run.

### `tender_notice_list(tenant_id, status?, deadline_after?, skip?, take?)` → `list[TenderNotice]`

Lists notices for a tenant, for a scoring or review pass.

### `tender_notice_get(notice_id)` → `TenderNotice`

Fetches a single notice by id.

## Fit scores

### `fit_score_upsert(tenant_id, notice_id, profile_id, total, dimensions, disqualified?, disqualifier?)` → `FitScore`

Creates or updates a deterministic fit score. Idempotent on `(notice_id,
profile_id)` — calling this again for the same pair replaces the score in
place.

### `fit_score_list(tenant_id, profile_id, min_total?, skip?, take?)` → `list[FitScore]`

Lists scored notices for a tenant profile, for a digest or review pass.

### `fit_score_set_narrative(score_id, narrative)` → `FitScore`

Fills in the LLM-authored rationale for an already-scored notice.

## Poll logs

### `poll_log_create(source, mode, ok, records_returned, started_at, finished_at, errors?)` → `PollLog`

Records fleet telemetry for one ingestion run. `errors` defaults to an
empty list, not an omitted field — a partially failed run is still
auditable via `poll_log_list`.

### `poll_log_list(source?, take?)` → `list[PollLog]`

Lists recent poll logs, most recent first, for fleet health monitoring.

## Settings (cursors and gates)

### `setting_get(key)` → `Setting`

Reads a cursor or gate value by key, e.g. `etenders.last_seeded_at`.

### `setting_set(key, value)` → `Setting`

Writes a cursor or gate value by key.

## Tenant fit-scoring configuration

### `profile_get_fit_config(tenant_id)` → `FitConfig`

Reads the tenant's fit-scoring configuration (sector weights, geo tiers,
route preferences, engagement gates, score/fit thresholds, contact
emails).

### `profile_set_fit_config(tenant_id, sector_weights?, geo_tiers?, route_prefs?, engagement?, score_threshold?, max_concurrent_bids?, fit_threshold?, contact_emails?)` → `FitConfig`

Writes the tenant's fit-scoring configuration. Omitted fields leave the
corresponding stored value unchanged.
