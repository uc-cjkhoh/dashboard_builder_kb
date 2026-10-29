# Backlog: analytics, AI assist and maps

Format: [README.md](README.md#how-to-read-an-entry). New numeric code is a pure JS module with `node --test` fixtures; there is no external statistical runtime and no scripting editor. Today the trend and forecast are fitted in the browser on the (possibly truncated) result; a model must refuse truncated data and show the notice.

## Statistics and forecasting

- **Reference lines, bands and distribution** (IDs: T07-03, T07-04, T07-05, T07-06, T07-07; priority P1–P2) — Partial: the average line is the first measure's shown rows only; reference lines are not linked to a field, calculation or parameter; bands take typed constants only; median and quartiles exist separately. Open: percentile or standard-deviation distribution band. Needs: parameters and aggregations in [calculations.md](calculations.md) for bound values.
- **Box plot completeness** (IDs: T07-08; priority P2) — Partial: outlier points and Tukey whiskers are built; the box plot still reads one table only (no joined tables, no calculated fields). Needs: none.
- **Trend models** (IDs: T07-13, T07-14, T07-15, T07-16; priority P2–P3) — Partial: log and fixed quadratic only (no exponential, power or degree), R-squared only; target is the formula, R-squared, p-value and sample size, hiding a model the data cannot support. Open: per-colour-group trend. Needs: none.
- **Intervals and confidence** (IDs: T07-09, T07-10, T07-17, T07-22; priority P2) — Open: average and median with 95% confidence interval, trend confidence bands, forecast prediction interval. Needs: trend models.
- **Forecast model** (IDs: T07-18, T07-19, T07-20, T07-21, T07-23; priority P2) — target: exponential smoothing with adjustable horizon, optional seasonality, incomplete-period and missing-value policy and a model description; a prediction interval is not a confidence interval. Partial: a 3/6/12-step extrapolation of the trend, not exponential smoothing; no history window, model family or incomplete-period handling. Open: seasonality, missing-data policy, model description and quality metrics. Needs: trend models.
- **Clustering** (IDs: T07-24, T07-25, T07-26; priority P2) — Open: k-means (chosen features, seeded for reproducibility, optional standardisation), cluster-count suggestion, saving labels as a dimension. Needs: a bounded server or client algorithm; saved labels need a derived dimension.

## P42 AI assist

- **Explain, decomposition and plain-language questions** (IDs: T09-17, T09-18; priority P3; effort L) — Open: rank which dimension members most change a selected mark (bounded per-dimension queries, client ranking); a decomposition tree; a question box (an explainable local grammar such as `sum of Sales by Region for 2025`, no external model) that shows its parse and returns a validated worksheet spec, never SQL, with a question-time metadata preview. Needs: a recorded decision on what data leaves the server.

## Maps (all open)

Constraint: geography is bundled and local; no external map, tile or geocoding service (see the map licensing risk in [platform.md](platform.md)). No map code exists today; it would be a new `Features/Maps` module. Boundaries and a place-name reference are static, licensed, same-origin assets; an unknown location needs explicit latitude and longitude or GeoJSON, and is flagged, never guessed. GeoJSON is read in the browser with size and depth limits and no remote references, and is kept in the workbook only if small enough. No request leaves the app origin.

- **Geographic roles and place data** (IDs: T06-01, T06-02, T06-03, T06-08, T06-11; priority P2–P3) — no geographic roles, gazetteer, generated coordinates, unrecognised-location resolution or contextual statistics layer. Needs: licensed bundled data.
- **Map marks** (IDs: T06-04, T06-05, T06-06, T06-12, T06-13, T06-16; priority P2) — no symbol, filled, density or pie-on-map marks, mark filters or detail control. Needs: geographic roles.
- **Map interaction and layers** (IDs: T06-07, T06-09, T06-10, T06-14, T06-21; priority P2) — no pan and zoom, themes, configurable or dual-axis layers, layer ordering or symbol styling. Needs: map marks.
- **Spatial file import** (IDs: T06-17, T06-18, T06-19, T06-20; priority P2–P3) — no geometry ingestion (ClickHouse geo types unhandled), GeoJSON, KML, Shapefile or MapInfo import. Needs: a size cap and parsers.
