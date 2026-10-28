# Backlog: analytics, AI assist and maps

Format: [README.md](README.md#how-to-read-an-entry). Today the trend and forecast are fitted in the browser on the (possibly truncated) result; a model must refuse truncated data and show the notice.

## Statistics and forecasting

- **Reference lines, bands and distribution** (IDs: T07-03, T07-04, T07-05, T07-06, T07-07; priority P1–P2) — Partial: the average line is the first measure's shown rows only; reference lines are not linked to a field, calculation or parameter; bands take typed constants only; median and quartiles exist separately. Open: percentile or standard-deviation distribution band. Needs: parameters and aggregations in [calculations.md](calculations.md) for bound values. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Box plot completeness** (IDs: T07-08; priority P2) — partial: quartiles with min/max whiskers, one table only; no outlier points. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Trend models** (IDs: T07-13, T07-14, T07-15, T07-16; priority P2–P3) — Partial: log and fixed quadratic only (no exponential, power or degree), R-squared only. Open: per-colour-group trend. Needs: none. Source: [gap-analysis-detail.md](../proposals/gap-analysis-detail.md).
- **Intervals and confidence** (IDs: T07-09, T07-10, T07-17, T07-22; priority P2) — Open: average and median with 95% confidence interval, trend confidence bands, forecast prediction interval. Needs: trend models. Source: [gap-analysis.md](../proposals/gap-analysis.md).
- **Forecast model** (IDs: T07-18, T07-19, T07-20, T07-21, T07-23; priority P2) — Partial: a 3/6/12-step extrapolation of the trend, not exponential smoothing; no history window, model family or incomplete-period handling. Open: seasonality, missing-data policy, model description and quality metrics. Needs: trend models. Source: [gap-analysis.md](../proposals/gap-analysis.md).
- **Clustering** (IDs: T07-24, T07-25, T07-26; priority P2) — Open: k-means, cluster-count suggestion, saving labels as a dimension. Needs: a bounded server or client algorithm; saved labels need a derived dimension. Source: [gap-analysis.md](../proposals/gap-analysis.md).

## P42 AI assist

- **Explain, decomposition and plain-language questions** (IDs: T09-17, T09-18; priority P3; effort L) — Open: rank which dimension members most change a selected mark (bounded per-dimension queries, client ranking); a decomposition tree; a question box that returns a validated worksheet spec, never SQL, with a question-time metadata preview. Needs: a recorded decision on what data leaves the server. Source: the former BI-parity roadmap.

## Maps (all open)

Constraint: geography is bundled and local; no external map, tile or geocoding service ([delivery-and-risks.md](../proposals/delivery-and-risks.md) map licensing risk). No map code exists today.

- **Geographic roles and place data** (IDs: T06-01, T06-02, T06-03, T06-08, T06-11; priority P2–P3) — no geographic roles, gazetteer, generated coordinates, unrecognised-location resolution or contextual statistics layer. Needs: licensed bundled data. Source: [tableau-features-geo-stats.md](../proposals/tableau-features-geo-stats.md).
- **Map marks** (IDs: T06-04, T06-05, T06-06, T06-12, T06-13, T06-16; priority P2) — no symbol, filled, density or pie-on-map marks, mark filters or detail control. Needs: geographic roles. Source: [tableau-features-geo-stats.md](../proposals/tableau-features-geo-stats.md).
- **Map interaction and layers** (IDs: T06-07, T06-09, T06-10, T06-14, T06-21; priority P2) — no pan and zoom, themes, configurable or dual-axis layers, layer ordering or symbol styling. Needs: map marks. Source: [tableau-features-geo-stats.md](../proposals/tableau-features-geo-stats.md).
- **Spatial file import** (IDs: T06-17, T06-18, T06-19, T06-20; priority P2–P3) — no geometry ingestion (ClickHouse geo types unhandled), GeoJSON, KML, Shapefile or MapInfo import. Needs: a size cap and parsers. Source: [tableau-features-geo-stats.md](../proposals/tableau-features-geo-stats.md).
