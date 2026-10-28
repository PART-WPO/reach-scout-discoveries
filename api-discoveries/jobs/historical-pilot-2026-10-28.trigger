Historical DataCite pilot authorization
Run date: 2026-10-28
Coverage: ALL SPARK unique award identifiers across every award shard, regardless division.
Mode: historical DataCite only; no Crossref historical backfill.
Output: append-only api-discoveries/historical/ research inbox, never Discovery Hub directly.
Stop publication if any API award request or shard fails; preserve workflow artifacts.

Rerun 2026-10-28: skip invalid SPARK placeholder quote; all legitimate IDs remain included. Prior failed shard is retained in GitHub Actions artifacts. No direct Hub publication.

Third run: 2026-10-28 full scan; commit retry/rebase enabled to handle concurrent repository updates.
