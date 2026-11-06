---
components: []
---
# Backlog: analytics, AI assist and maps

Statistics, AI-assist and map work not yet built. Format: [index.md](index.md#how-to-read-an-entry).

- New numeric code is a pure JS module with `node --test` fixtures. There is no external statistical runtime and no scripting editor.
- The trend and forecast are fitted in the browser on the (possibly truncated) result. On truncated data the "Analytics use only the rows shown" notice is shown; no model refuses truncated data yet (listed under Trend models).

## Statistics and forecasting

- **Reference lines, bands and distribution** (IDs: T07-03, T07-04, T07-05; priority P1–P2) — Partial: lines and bands read any shown measure over the rows shown (average, median, min, max, constant; a constant may follow a number parameter); bands are typed numbers, mean ± 1σ / 2σ, P25–P75 / P10–P90 or typed percentiles. Open: a band's typed ends following a calculation (a number parameter works), a reference line over a field or calculation not on the shelf, per-pane / per-table scope, a distribution band over the whole table rather than the rows shown. Needs: parameters and aggregations in [calculations.md](calculations.md) for bound values.
- **Trend models** (IDs: T07-14, T07-15, T07-16; priority P2–P3) — Partial: linear, log, exponential, power and fixed quadratic; the label shows formula, R² and n, and exponential / power refuse non-positive values with a message. Missing: refusing a model on truncated data (today only the notice), a polynomial degree choice (1–4), the p-value, hiding a model the data cannot support beyond the exp / power domain rule, per-colour-group trend. Needs: none.
- **Intervals and confidence** (IDs: T07-09, T07-10, T07-17, T07-22; priority P2) — Open: average and median with 95% confidence interval, trend confidence bands, forecast prediction interval. Needs: trend models.
- **Forecast model** (IDs: T07-18, T07-19, T07-20, T07-21, T07-23; priority P2) — target: exponential smoothing with adjustable horizon, optional seasonality, incomplete-period and missing-value policy and a model description; a prediction interval is not a confidence interval. Partial: a 3/6/12-step extrapolation of the trend, not exponential smoothing; no history window, model family or incomplete-period handling. Open: seasonality, missing-data policy, model description and quality metrics. Needs: trend models.
- **Clustering** (IDs: T07-24, T07-25, T07-26; priority P2) — Open: k-means (chosen features, seeded for reproducibility, optional standardisation), cluster-count suggestion, saving labels as a dimension. Needs: a bounded server or client algorithm; saved labels need a derived dimension.

## P42 AI assist

- **Explain, decomposition and plain-language questions** (IDs: T09-17, T09-18; priority P3; effort L) — Open: rank which dimension members most change a selected mark (bounded per-dimension queries, client ranking); a decomposition tree; a question box (an explainable local grammar such as `sum of Sales by Region for 2025`, no external model) that shows its parse and returns a validated worksheet spec, never SQL, with a question-time metadata preview. Needs: a recorded decision on what data leaves the server.

## Maps (all open)

No map code exists; it would be a new `Features/Maps` module. Constraints:

- Geography is bundled and local, with no external map, tile or geocoding service (see the map licensing risk in [platform.md](platform.md)).
- Boundaries and a place-name reference are static, licensed, same-origin assets.
- An unknown location needs explicit latitude and longitude or GeoJSON, and is flagged, never guessed.
- GeoJSON is read in the browser with size and depth limits and no remote references. It is kept in the workbook only if small enough.
- No request leaves the app origin.

- **Geographic roles and place data** (IDs: T06-01, T06-02, T06-03, T06-08, T06-11; priority P2–P3) — no geographic roles, gazetteer, generated coordinates, unrecognised-location resolution or contextual statistics layer. Needs: licensed bundled data.
- **Map marks** (IDs: T06-04, T06-05, T06-06, T06-12, T06-13, T06-16; priority P2) — no symbol, filled, density or pie-on-map marks, mark filters or detail control. Needs: geographic roles.
- **Map interaction and layers** (IDs: T06-07, T06-09, T06-10, T06-14, T06-21; priority P2) — no pan and zoom, themes, configurable or dual-axis layers, layer ordering or symbol styling. Needs: map marks.
- **Spatial file import** (IDs: T06-17, T06-18, T06-19, T06-20; priority P2–P3) — no geometry ingestion (ClickHouse geo types unhandled), GeoJSON, KML, Shapefile or MapInfo import. Needs: a size cap and parsers.
