# Trade history and live join example

Subscribe to `trades` and buffer deliveries before requesting the immutable session snapshot. Load every history page using its cursor. Keep the snapshot's `(epoch, seq)` watermark and discard buffered/live transport entries at or below it; apply entries above it once in topic sequence order. This removes duplicate transport delivery without removing identical source trades: rows with the same millisecond, price, volume, and flags remain separate when their `occurrence` values differ.

For example, two eligible source rows at `2026-10-01T12:00:00.123Z` with identical values have occurrence `0` and `1`. Both are retained. If replay expires or the epoch changes, fetch a new snapshot. If `source_generation` changes, discard the old token and session pages and start from the replacement generation's snapshot. `trades.status` reports coverage and its own sequence; it is not a tape recovery source.
