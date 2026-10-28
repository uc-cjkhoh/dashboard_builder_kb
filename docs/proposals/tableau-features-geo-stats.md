# Tableau inventory — geospatial, statistics and forecasting

Chapters 6 and 7 of the [feature inventory](tableau-features.md). IDs are unchanged.

### 6. Geospatial visual analytics

*Coverage: Ch. 6, pp. 131–154; 21 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T06-01 | Geographic field roles | Mark country/state/city/geocoordinates as geographic data types. | 132–134 | P2 |
| T06-02 | Built-in place-name resolution | Resolve supported geographic names with country/region context, using bundled gazetteer. | 132–134 | P2 |
| T06-03 | Generated geographic coordinates | Provide latitude/longitude from known place names where present in bundled reference. | 132–134, 140 | P2 |
| T06-04 | Symbol map | Map circles/points whose size and color can encode measures. | 132–134 | P2 |
| T06-05 | Filled/choropleth map | Shade polygons by categorical or numeric attributes. | 134–135 | P2 |
| T06-06 | Density map | Show spatial concentration with smoothed density/heat surface. | 134–136 | P2 |
| T06-07 | Pan and zoom | Navigate map extent using controls, mousewheel and drag gestures. | 133 | P2 |
| T06-08 | Unrecognized-location resolution | Allow manual geographic disambiguation of ambiguous names. | 134 | P3 |
| T06-09 | Light/normal/dark map themes | Select among locally bundled cartographic background styles. | 136–137 | P2 |
| T06-10 | Configurable map layers | Toggle administrative borders, coastlines, text labels and geographic context. | 136–137 | P2 |
| T06-11 | Background socioeconomic layer concept | Overlay pre-provided contextual statistics when legally bundled; book references US-specific layers. | 137 | P3 |
| T06-12 | Pie-on-map marks | Visualize categorical proportions at geographic points. | 137–139 | P2 |
| T06-13 | Map mark filters | Reduce clutter by category or aggregate threshold. | 138–139 | P2 |
| T06-14 | Dual-axis map layers | Overlay symbol or pie marks on a filled map. | 139–140 | P2 |
| T06-15 | Viz in Tooltip | Render a second filtered chart inside tooltip for chart/map marks. | 140–143 | P2 |
| T06-16 | Map mark detail control | Break one spatial geometry collection into separate marks by a dimension. | 150–151 | P2 |
| T06-17 | Spatial geometry ingestion | Import supplied polygon/line/point geometry to a spatial field. | 147–152 | P3 |
| T06-18 | GeoJSON import | Read an uploaded open-standard GeoJSON geometry file directly. | 148 | P2 |
| T06-19 | KML import | Read user-supplied KML without use of Google Earth. | 147 | P3 |
| T06-20 | ESRI Shapefile / MapInfo inputs | Accept supplied multiparts with bundled parsers; no QGIS required. | 148 | P3 |
| T06-21 | Map layer ordering and symbol styling | Set line width, geometry mark order and colors to reduce overlap. | 146, 151–152 | P2 |

### 7. Statistics, reference analytics, forecasting and clustering

*Coverage: Ch. 7, pp. 155–167; 26 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T07-01 | Analytics pane | Separate drag-and-drop statistics tools from raw data fields. | 156–157 | P1 |
| T07-02 | Constant line | Add a fixed threshold on a numeric axis. | 156–157 | P1 |
| T07-03 | Average line | Show an overall, pane- or cell-level mean. | 156–157 | P1 |
| T07-04 | Reference line | Link a threshold to measure, calculated field, or parameter. | 157 | P1 |
| T07-05 | Reference band | Show ranges specified by two metrics/parameters. | 157 | P2 |
| T07-06 | Distribution band | Shaded distribution using percentiles, quantiles, percentage or standard deviation. | 157 | P2 |
| T07-07 | Median with quartiles | Show central tendency and interquartile range. | 156 | P2 |
| T07-08 | Box plot | Display quartiles, spread and outliers as box-and-whisker plot. | 156–157 | P2 |
| T07-09 | Average with 95% CI | Show average plus confidence bounds. | 156 | P2 |
| T07-10 | Median with 95% CI | Show median with estimated confidence bounds. | 156 | P2 |
| T07-11 | Row/column subtotals and grand totals | Display aggregations across rows/columns and grouped partitions. | 156 | P1 |
| T07-12 | Trend line: linear | Fit a straight regression line to view data. | 158–161 | P2 |
| T07-13 | Trend line: log / exponential | Fit logarithmic or exponential trend models where compatible. | 158–161 | P2 |
| T07-14 | Trend line: polynomial / power | Fit configurable polynomial or power regression models. | 158–161 | P3 |
| T07-15 | Per-color-group trend line | Fit separate regression models for dimension groups. | 160 | P2 |
| T07-16 | Trend model diagnostics | Show equation, R², p-value, parameters and fit description. | 160–161 | P2 |
| T07-17 | Trend confidence bands | Show confidence bounds (95% in book) and optional forced zero intercept. | 160 | P2 |
| T07-18 | Forecasting with exponential smoothing | Extrapolate future time-series values with native smoothing model. | 162–165 | P2 |
| T07-19 | Forecast horizon options | Choose forecast length, history window, model family, last incomplete period handling. | 162–164 | P2 |
| T07-20 | Seasonality selection | Compare automatic seasonal, nonseasonal and custom forecast options. | 164 | P2 |
| T07-21 | Forecast missing-data handling | Decide whether to omit or replace missing observations with zero. | 163 | P2 |
| T07-22 | Forecast confidence / prediction interval | Display probabilistic range around a forecast. | 162–165 | P2 |
| T07-23 | Forecast model description | Expose model assumptions, smoothing coefficients and quality metrics. | 164–166 | P2 |
| T07-24 | K-means clustering | Segment marks into clusters using selected measures. | 166–167 | P2 |
| T07-25 | Automatic/manual cluster count | Suggest or configure number of clusters. | 166–167 | P2 |
| T07-26 | Save cluster labels as dimension | Reuse computed clusters across subsequent views. | 167 | P2 |
