# Gap analysis: Dashboard Builder vs the Tableau inventory

Per-ID detail for [gap-analysis.md](gap-analysis.md). One row for each of the 229 requirements in [`tableau-features.md`](tableau-features.md). Evidence paths are relative to `src/DashboardBuilder/` in the app repo; **Layer** is where the missing work sits.

Status: **built** = the behaviour exists end to end · **partial** = some exists (the note says what is missing) · **open** = nothing implements it.

## 1. Workspace and workbooks

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T01-01 | Browser-based analytics workspace | P0 | built | Features/Dashboard/dashboards.js:fieldChip, toolButton | Drag/drop fields onto shelves builds the chart without code | - |
| T01-02 | Data pane | P0 | built | Features/Dashboard/dashboards.js:buildFields, fieldChip | Field pane per table with type icon, name, type tooltip, search | - |
| T01-03 | Dimension vs. measure roles | P0 | built | Features/Dashboard/show-me-rules.js:roleOf; dashboards.js:setRole | Dimensions/Measures grouped; pill convert button reassigns role | - |
| T01-04 | Discrete vs. continuous field semantics | P1 | partial | Features/Dashboard/dashboards.js:fieldPill; date-parts.js | Role convert and date part/exact only; no explicit discrete/continuous pill toggle or continuous axes | client |
| T01-05 | Rows shelf | P0 | built | Features/Dashboard/dashboards.js:fieldPill (rows shelf) |  | - |
| T01-06 | Columns shelf | P0 | built | Features/Dashboard/dashboards.js:fieldPill (columns shelf) |  | - |
| T01-07 | Marks card | P0 | built | Features/Dashboard/dashboards.js:1875-1900 (marks tools) | Colour, Size, Label, Shape, Detail, Tooltip, Path, Angle all wired to query/chart | - |
| T01-08 | Filters shelf | P0 | built | Features/Dashboard/dashboards.js:addFilter; ClickHouse/ClickHouseGateway.cs:QueryCoreAsync | Typed filters (13 ops), bound server-side | - |
| T01-09 | Pages shelf | P3 | built | Features/Dashboard/dashboards.js:addPages, pagesControl | Pages field steps/animates through members | - |
| T01-10 | Sheet canvas and title | P0 | built | Features/Dashboard/dashboards.js:titleBlock; Features/Tabs/tabs.js:beginRename | Editable sheet title/caption and tab rename | - |
| T01-11 | Multiple worksheets | P0 | partial | Features/Tabs/tabs.js:addButton, beginRename | Create/rename/switch/close exist; no duplicate-sheet action | client |
| T01-12 | New dashboard and story controls | P1 | partial | Features/Tabs/tabs.js:initTabs; Features/Core/store.js:createDashboard | A new dashboard tab can be created; no multi-sheet composition and no story view (P24 unbuilt) | client |
| T01-13 | Data source editor tab | P0 | built | Features/Tabs/tabs.js:modelTab; Features/Canvas/canvas.js | Pinned Data Model tab separate from worksheet tabs | - |
| T01-14 | Start screen and recent sources | P1 | partial | Features/Workbook/workbook.js:importFile, openWorkbook | Import workbook and autosave restore exist; no start screen or recent sources | client |
| T01-15 | Mouse field placement and double-click defaults | P1 | partial | Features/Dashboard/dashboards.js:fieldChip (drag, plus button) | Drag and plus-button auto-place exist; no double-click placement | client |
| T01-16 | Undo and redo | P0 | built | Features/Dashboard/dashboards.js:undoButtons, step, initUndoKeys; history.js | Undo/redo buttons and Ctrl+Z/Y per sheet | - |
| T01-17 | Swap rows and columns | P1 | built | Features/Dashboard/dashboards.js:swapShelves | Sheet actions menu swaps Rows/Columns | - |
| T01-18 | View data behind marks | P1 | open |  | Click selects/drills marks; no view-underlying-rows action or endpoint | both |
| T01-19 | Tooltip field editor | P0 | partial | Features/Dashboard/dashboards.js:1875 (tooltip shelf); chart.js tooltipExtra | Extra fields shown in hover; no tooltip text/format editor | client |
| T01-20 | Color palettes and discrete legend | P0 | partial | Features/Core/theme-model.js:PALETTES; dashboards.js:legendHandler; formatPanel legend | Workbook palette (3) + legend position/highlight; no per-member colour assignment | client |
| T01-21 | Continuous color scales | P1 | partial | Features/Dashboard/chart.js:continuousVisualMap; dashboards.js:2726 | Single-hue gradient on scatter only; no palette choice or range editing | client |
| T01-22 | Mark shape and size options | P1 | partial | Features/Dashboard/dashboards.js:renderScatterShapes; formatPanel Data labels | Shape/size by field, data labels; no fixed marker size or border setting | client |
| T01-23 | Worksheet-level formatting | P1 | partial | Features/Dashboard/dashboards.js:formatPanel; Features/Workbook/theme-dialog.js | Number/date/legend/fit and theme; no font, alignment, shading, cell sizes | client |
| T01-24 | Presentation mode | P1 | built | Features/Dashboard/dashboards.js:toggleFullScreen | Full-screen chart card, Esc to exit | - |
| T01-25 | Save, open, Save As | P0 | built | Features/Workbook/workbook.js:save, exportFile, importFile | Autosave in browser plus JSON export/import; no named multi-workbook Save As | - |
| T01-28 | Export to PDF and image | P1 | built | Features/Dashboard/dashboards.js:exportControl, exportImage, printView | PNG, SVG, print-to-PDF of the single worksheet | - |
| T01-29 | Export worksheet data or crosstab | P1 | built | Features/Dashboard/dashboards.js:exportCsvRows; Features/Dashboard/QueryController.cs:25 | CSV of worksheet result up to 100k rows, server-bounded | - |
| T01-30 | Workbook performance recording | P2 | open |  | No query/render timing capture or recording anywhere | both |

## 2. Data source, modeling, metadata

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T02-05 | Preview source rows | P0 | partial | Features/Canvas/canvas.js:renderColumns; SchemaController.cs:Distinct | Names/types and distinct values only; no raw-record preview endpoint | both |
| T02-06 | ClickHouse connection | P1 | built | Features/Connection/ConnectionController.cs:Connect; ClickHouse/ConnectionRegistry.cs | Session-only creds, Secure/TLS option, never returned | - |
| T02-07 | Database/schema/table browser | P1 | built | Features/Schema/schema.js:loadDatabases, loadTables; SchemaController.cs | Database select plus searchable table list | - |
| T02-08 | Multiple tables in a data model | P1 | built | Features/Canvas/canvas.js:createEntity | Entities carry db; tables from any database can be added | - |
| T02-09 | Visual table canvas | P1 | built | Features/Canvas/canvas.js:drop handler, enableDragMove | Drag tables to canvas; cards move; relationships drawn | - |
| T02-10 | Inner join | P1 | built | ClickHouse/ClickHouseGateway.cs:632 (INNER JOIN); relations.js:openCardinalityDialog | Default join type | - |
| T02-11 | Left join | P1 | built | ClickHouse/ClickHouseGateway.cs:632 (LEFT JOIN); relations.js:createRelationship | Left join with NULL-preserving setting | - |
| T02-12 | Right join | P1 | open | ClickHouse/RequestValidation.cs:118 | Join type validated to inner/left only; no right-join option | both |
| T02-13 | Full outer join | P1 | open | ClickHouse/RequestValidation.cs:118 | No full outer join in dialog, validation or SQL builder | both |
| T02-14 | Join key detection | P2 | open |  | Relationships drawn manually only; no suggestion of matching-name keys | client |
| T02-15 | Compound/non-equality join conditions | P2 | open | ClickHouse/QueryModels.cs:13 | JoinRef is one column pair, equality only | both |
| T02-16 | Manual table union | P1 | open |  | No union of tables anywhere | both |
| T02-18 | Live connection | P1 | built | ClickHouse/ClickHouseGateway.cs:QueryAsync | Every query hits ClickHouse live; no extract; 60s result cache | - |
| T02-19 | Manual refresh of live view | P1 | built | Features/Dashboard/dashboards.js:refreshButton; QueryRequest.Fresh | Refresh bypasses server cache | - |
| T02-25 | Source read-only safety | P0 | built | ClickHouse/ClickHouseGateway.cs:49-62 (set_readonly=2) | Server-enforced read-only plus no DDL/DML endpoint | - |
| T02-26 | Rename source field | P0 | built | Features/Dashboard/dashboards.js:renameField; Core/store.js:setFieldMeta | Alias saved in workbook, shown on pills/axes | - |
| T02-27 | Hide unused fields | P0 | built | Features/Dashboard/dashboards.js:fieldMenu, buildFields | Hide/show hidden fields in pane | - |
| T02-28 | Copy field or selected preview values | P2 | open |  | No copy action for fields or values | client |
| T02-29 | Alias dimension members | P1 | open |  | Field alias only; no member-value alias mapping | both |
| T02-30 | Dimension groups | P1 | open |  | No dimension groups | both |
| T02-31 | Automatic/custom string split | P1 | open |  | No string split | both |
| T02-32 | Unpivot wide columns to rows | P1 | open |  | No unpivot | both |
| T02-33 | Field details and metadata | P1 | partial | Features/Dashboard/dashboards.js:fieldChip; Canvas/canvas.js:renderColumns | Type and role shown; no field-properties panel (sort, semantic role, etc.) | client |
| T02-34 | Cast data types | P0 | open |  | Only role convert and date parts; no cast between string/number/date types | both |
| T02-36 | Query pushdown and source-aware optimization | P1 | built | Features/Dashboard/dashboards.js:buildJoins; ClickHouseGateway.cs:QueryCoreAsync | All filter/aggregate pushed to SQL; joins only for tables in use | - |
| T02-37 | Database indexing/partition guidance | Document only | open |  | Document-only row; no indexing/partition guidance found in app or KB | client |

## 3. Charts, encodings, filters

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T03-01 | Show Me chart recommender | P1 | built | Features/Dashboard/show-me-rules.js:showMeOptions; dashboards.js:773 | Greyed invalid types with reason, recommended tile. | - |
| T03-02 | Vertical and horizontal bar chart | P0 | built | Features/Dashboard/chart.js:buildCartesian; dashboards.js:swapShelves | Orientation follows Rows/Columns; Swap menu item. | - |
| T03-03 | Scatter plot | P0 | built | Features/Dashboard/chart.js:buildScatter | Two measures on axes; Detail gives mark per entity. | - |
| T03-04 | Time-series line chart | P0 | built | Features/Dashboard/chart.js:buildCartesian (line/area) | Category-axis line, not a true time axis. | - |
| T03-05 | Straight, step, and jump line styles | P1 | open |  | No step/jump/gap-aware line style; lines always straight series. | client |
| T03-06 | Temporal hierarchy navigation | P1 | built | Features/Dashboard/date-parts.js:stepPart; dashboards.js:1258-1270 | Pill +/- steps year to hour; drill tool also exists. | - |
| T03-07 | Continuous and discrete dates | P1 | partial | Features/Dashboard/date-parts.js:DATE_PART_CHOICES; ClickHouse/ClickHouseGateway.cs:DatePartExpression | Truncated vs discrete date parts exist; no continuous time axis or gap filling. | client |
| T03-08 | Text crosstab | P0 | built | Features/Dashboard/dashboards.js:crosstabTable (Table and Text types) | Rows x Columns text grid. | - |
| T03-09 | Highlight table | P1 | built | Features/Dashboard/conditional-model.js:scaleColors; dashboards.js:conditionalEditor | Per-measure colour scale on Table/Text cells. | - |
| T03-10 | Heatmap with circles | P1 | open |  | Heatmap is coloured squares only; no circle size+colour matrix. | client |
| T03-11 | Pie chart | P1 | built | Features/Dashboard/chart.js:buildPie | Pie and donut. | - |
| T03-12 | Bullet chart | P1 | built | Features/Dashboard/chart.js:buildBullet | Bar, target tick, three bands; target from Format, not a field. | - |
| T03-13 | Waterfall chart | P1 | built | Features/Dashboard/chart.js:buildWaterfall | Running total with Total bar. | - |
| T03-14 | Gantt-bar marks | P2 | open |  | No Gantt/interval marks; waterfall is a separate fixed chart type. | client |
| T03-15 | Side-by-side measure bars | P1 | built | Features/Dashboard/chart.js:buildCartesian | Bar groups side by side at 2+ measures. | - |
| T03-16 | Dual-axis layered view | P1 | built | Features/Dashboard/chart.js:buildCartesian (isCombo) | Combo only: first measure bar, second line on right axis. | - |
| T03-17 | Axis synchronization | P1 | open |  | Combo right axis independent; no synchronize-axis option. | client |
| T03-18 | Field-based categorical coloring | P0 | built | Features/Dashboard/dashboards.js:planDims (colorDiscrete); chart.js:colorByDim | Discrete Colour splits series; Colour by category. | - |
| T03-19 | Measure-based intensity coloring | P1 | partial | Features/Dashboard/chart.js:continuousVisualMap; buildHeatmap | Continuous colour on scatter, heatmap, table only; not bar/line/other marks. | client |
| T03-20 | Size encoding | P1 | built | Features/Dashboard/chart.js:buildScatter (sizes) | Size drives bubble radius on scatter family only. | - |
| T03-21 | Shape encoding | P1 | partial | Features/Dashboard/chart.js:buildScatterShapes; dashboards.js:111 | Shape dimension picks point symbols (scatter); no per-measure mark-type switch. | client |
| T03-22 | Detail encoding | P1 | built | Features/Dashboard/dashboards.js:planDims (Detail) | Detail dims become extra group-by keys. | - |
| T03-23 | Labels and text encoding | P1 | built | Features/Dashboard/chart.js:buildCartesian dataLabel; dashboards.js:planMeasures | Label tool and Data labels toggle. | - |
| T03-24 | Legend editing | P1 | partial | Features/Dashboard/dashboards.js:formatPanel Legend; Core/theme-model.js:PALETTES | Legend position/hide and workbook palette only; no per-member colour assignment or scale editing. | client |
| T03-25 | Dimension value filter | P0 | built | Features/Dashboard/filter-rules.js:opsFor; ClickHouse/RequestValidation.cs:Ops | in, =, != filters with bound values. | - |
| T03-26 | Show interactive filter control | P0 | built | Features/Dashboard/dashboards.js:filterCards | Filter cards and parameter controls on the sheet. | - |
| T03-27 | Numeric range and measure filter | P1 | partial | Features/Dashboard/filter-rules.js:opsFor; ClickHouse/ClickHouseGateway.cs:WHERE builders | Row-level between/compare on columns; no filter on aggregated measure (no HAVING); no slider. | both |
| T03-28 | Multiple selection and exclusion | P0 | partial | Features/Dashboard/dashboards.js:checklist; selectionChip | Multi-select in; Exclude only for single clicked value; no NOT IN. | both |
| T03-29 | Interactive dimension hierarchies | P1 | partial | Features/Dashboard/dashboards.js:addDrillLevel, drillChip | Per-sheet unnamed drill hierarchy; no named model hierarchies or expand/collapse headers. | client |
| T03-30 | Field- and value-based sorting | P0 | built | Features/Dashboard/dashboards.js:sortControl; ClickHouse/ClickHouseGateway.cs:IsValidSortAlias | Server ORDER BY by field, asc/desc. | - |
| T03-31 | Under-mark source inspection | P1 | open |  | No row-level endpoint; CSV export is the aggregated result only. | both |
| T03-32 | Fit view modes | P1 | built | Features/Dashboard/dashboards.js:891-897; chart-fit.js | Standard, fit width, fit height, entire view. | - |
| T03-33 | Categorical and diverging color palettes | P1 | partial | Features/Core/theme-model.js:PALETTES; Dashboard/conditional-model.js | Three categorical palettes, diverging only in table scale; no reverse; chart ramp single-hue. | client |
| T03-34 | Format mark borders | P2 | open |  | Heatmap border hardcoded to surface colour; no user border setting. | client |

## 4. Aggregations, calculations, parameters

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T04-01 | Aggregation SUM | P0 | built | ClickHouse/ClickHouseGateway.cs:Aggregations (258) | sum; numeric only. | - |
| T04-02 | Aggregation AVG | P0 | built | ClickHouse/ClickHouseGateway.cs:Aggregations (258) | avg; numeric only. | - |
| T04-03 | Aggregation MEDIAN | P1 | open |  | Whitelist is count,sum,avg,min,max,countDistinct; no median. | both |
| T04-04 | COUNT and COUNT DISTINCT | P0 | partial | ClickHouse/ClickHouseGateway.cs:675-683 | count() counts all rows; countDistinct uniqExact. No non-null column count. | both |
| T04-05 | MIN and MAX | P0 | built | Features/Dashboard/filter-rules.js:AGGS | min/max on numeric, text and date fields. | - |
| T04-06 | Percentiles | P1 | open |  | Quantiles only fixed 25/50/75 inside box plot; no percentile aggregation. | both |
| T04-07 | Standard deviations | P1 | open |  | No stddev aggregation in whitelist. | both |
| T04-08 | Variances | P1 | open |  | No variance aggregation in whitelist. | both |
| T04-09 | ATTR dimension aggregation | P2 | open |  | No ATTR aggregation. | both |
| T04-10 | Null semantics for aggregation | P0 | built | ClickHouse/ClickHouseGateway.cs:675-689 | Native SQL aggregates skip nulls; no deliberate replacement option. | - |
| T04-11 | Calculated field creator/editor | P0 | open |  | No calculated-field editor or expression engine anywhere in client or server. | both |
| T04-12 | Calculation help/glossary | P1 | open |  | No calculation help or function glossary. | client |
| T04-13 | Row-level vs aggregate expressions | P0 | open |  | No row-level vs aggregate expressions; only measure aggregation per pill. | both |
| T04-14 | Arithmetic calculations | P0 | partial | Features/Dashboard/table-calc.js:computeCalc | Quick table calcs (% total, diff, running, rank) only; no ratios or field arithmetic. | both |
| T04-15 | SPLIT text operator | P1 | open |  | No SPLIT or string functions. | both |
| T04-16 | LEFT and RIGHT string operators | P1 | open |  | No LEFT/RIGHT. | both |
| T04-17 | LOWER and UPPER | P1 | open |  | No LOWER/UPPER as a user calculation. | both |
| T04-18 | REPLACE text operator | P1 | open |  | No REPLACE. | both |
| T04-19 | CONTAINS text predicate | P1 | partial | ClickHouse/RequestValidation.cs:Ops; Features/Dashboard/filter-rules.js:TEXT_OPS | contains filter op exists, case-insensitive only; not a calculated predicate. | both |
| T04-20 | Date hierarchy and date parts | P1 | built | ClickHouse/ClickHouseGateway.cs:DatePartExpression; Dashboard/date-parts.js | Year, quarter, month, week, day, hour, month of year, day of week. | - |
| T04-21 | Gregorian and ISO 8601 date conventions | P2 | partial | ClickHouse/ClickHouseGateway.cs:308 | week = toMonday only; no ISO week number/year or fiscal calendar. | both |
| T04-22 | Date difference and calculation operators | P1 | open |  | No date difference or date arithmetic; period compare is range-based only. | both |
| T04-23 | Date parsing and formatting | P1 | partial | Features/Dashboard/dashboards.js:formatPanel Dates | Display format select and date-part extraction only; no string-to-date parsing. | both |
| T04-24 | CASE expression | P1 | open |  | No CASE expression. | both |
| T04-25 | IF / THEN / ELSE | P1 | open |  | No IF/THEN/ELSE. | both |
| T04-26 | IIF ternary conditional | P2 | open |  | No IIF. | both |
| T04-27 | IFNULL replacement | P1 | open |  | No IFNULL; nulls just render as dash. | both |
| T04-28 | Create a parameter | P1 | built | Features/Workbook/parameters-dialog.js; Core/parameters-model.js:cleanParameter | Typed number/text/date, max 20 per workbook. | - |
| T04-29 | Parameter constraints | P1 | partial | Features/Workbook/parameters-dialog.js:80; Core/parameters-model.js:checkValue | Any/list/range and value set; step size stored but dialog always saves null. | client |
| T04-30 | Parameter controls | P1 | built | Features/Dashboard/dashboards.js:paramControls | Select, slider+box, typed or date input above filters. | - |
| T04-31 | Parameter-dependent computed metrics | P1 | open |  | Parameters feed filter values and Top N only; no calculated measure to drive. | both |
| T04-32 | Parameter-fed reference thresholds | P2 | open |  | Analytics reference-line constant is typed number; not parameter-bindable. | client |
| T04-33 | Parameter-driven search box | P1 | built | Features/Dashboard/dashboards.js:PARAMABLE, paramBinding; ClickHouse/ClickHouseGateway.cs (contains) | Text parameter bound to contains/starts/ends filter; case-insensitive. | - |

## 5. Table calculations and LOD

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T05-01 | Calculation evaluation-order model | P0 | partial | Features/Dashboard/dashboards.js:2473-2480 | Pipeline implicit (server aggregate, then client calc); no evaluation-order explanation or LOD stage; notice only | client |
| T05-02 | Quick running total | P1 | built | Features/Dashboard/table-calc.js:computeCalc | Running sum along shelf in sort order; sum only | - |
| T05-03 | Quick difference | P1 | built | Features/Dashboard/table-calc.js:computeCalc | Difference vs previous mark; first is blank | - |
| T05-04 | Quick percent difference | P1 | built | Features/Dashboard/table-calc.js:computeCalc | pctDiff vs previous, abs denominator | - |
| T05-05 | Quick percent of total | P1 | built | Features/Dashboard/table-calc.js:computeCalc | Percent of partition total; no table/pane/cell total choice | - |
| T05-06 | Quick rank | P1 | built | Features/Dashboard/table-calc.js:computeCalc | Competition rank, descending only; no ascending/dense/unique options | - |
| T05-07 | Quick percentile ranking | P1 | open |  | No percentile-rank calculation in CALC_CHOICES | client |
| T05-08 | Quick moving average | P1 | built | Features/Dashboard/table-calc.js:computeCalc; dashboards.js:1477 | Trailing window 2-30 (preset choices); no centred/forward windows | - |
| T05-09 | YTD total | P2 | open |  | No year-restarting cumulative; running total partitions only by shelf dims | client |
| T05-10 | Compound growth rate | P2 | open |  | No compound growth rate calculation | client |
| T05-11 | Year-over-year growth | P1 | partial | Features/Dashboard/period-model.js:COMPARE_CHOICES | Same-period-last-year comparison series only; no growth percentage calculation | client |
| T05-12 | YTD growth | P2 | open |  | No YTD growth | client |
| T05-13 | Table-calculation edit dialog | P1 | partial | Features/Dashboard/dashboards.js:calcPanel | Type, Along (auto/columns/rows), window only; no per-dimension compute-using or restart control | client |
| T05-14 | Table across/down direction | P1 | partial | Features/Dashboard/table-calc.js:resolveAlong | Only across/down/auto per shelf; no pane, table-across-then-down or cell directions | client |
| T05-15 | Specific addressing vs partitioning | P1 | partial | Features/Dashboard/table-calc.js:computeCalc | Addresses a whole shelf, partitions by other shelf; cannot choose individual dimensions | client |
| T05-16 | Calculation-assistance overlay | P2 | open |  | No overlay showing direction or mark order | client |
| T05-17 | Duplicate as crosstab | P1 | partial | Features/Dashboard/dashboards.js:crosstabTable | Switching chart type to Table shows grouped data; no duplicate-as-crosstab action | client |
| T05-18 | Custom table functions | P2 | open |  | No expression syntax or window functions; only fixed quick-calc list | both |
| T05-19 | Bump chart | P2 | partial | Features/Dashboard/table-calc.js:computeCalc | Rank calc on a Line chart gives rank over time; no bump preset or reversed rank axis | client |
| T05-20 | Dual-axis chart with rank/measure | P1 | built | Features/Dashboard/chart.js:buildCartesian (combo); dashboards.js:2474 | Combo dual axis with per-measure table calcs; custom calcs absent | - |
| T05-21 | Parameter-adjustable moving average | P2 | partial | Features/Dashboard/dashboards.js:1477 | Window picked from preset list by author; not bindable to a viewer parameter | client |
| T05-22 | LOD FIXED | P2 | open |  | No FIXED LOD mechanism; no calculated fields at all | both |
| T05-23 | LOD INCLUDE | P2 | open |  | No INCLUDE LOD mechanism | both |
| T05-24 | LOD EXCLUDE | P2 | open |  | No EXCLUDE LOD mechanism | both |
| T05-25 | First-event cohort analysis | P2 | open |  | No per-entity first-date derivation (needs FIXED) | both |
| T05-26 | Per-entity aggregate then average | P2 | open |  | No two-level aggregation (aggregate per entity then average) | both |
| T05-27 | Higher-level benchmark in granular charts | P2 | open |  | No higher-level benchmark via EXCLUDE | both |

## 6. Maps

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T06-01 | Geographic field roles | P2 | open |  | No geographic data-type roles; categories are numeric/text/temporal only | both |
| T06-02 | Built-in place-name resolution | P2 | open |  | No gazetteer or place-name resolution | both |
| T06-03 | Generated geographic coordinates | P2 | open |  | No bundled reference; no lat/long generation | both |
| T06-04 | Symbol map | P2 | open |  | No map chart type; CHART_TYPE_IDS has none | both |
| T06-05 | Filled/choropleth map | P2 | open |  | No polygon/choropleth rendering or geometry source | both |
| T06-06 | Density map | P2 | open |  | No density/heat surface | both |
| T06-07 | Pan and zoom | P2 | open |  | No map; only chart dataZoom axes (chart.js:124) | client |
| T06-08 | Unrecognized-location resolution | P3 | open |  | No geographic roles, so nothing to disambiguate | both |
| T06-09 | Light/normal/dark map themes | P2 | open |  | No map themes; only app light/dark scheme | client |
| T06-10 | Configurable map layers | P2 | open |  | No map to hold layers | client |
| T06-11 | Background socioeconomic layer concept | P3 | open |  | No contextual statistics layer | both |
| T06-12 | Pie-on-map marks | P2 | open |  | No map; pie chart exists but not placed on coordinates | client |
| T06-13 | Map mark filters | P2 | open |  | No map marks to filter | client |
| T06-14 | Dual-axis map layers | P2 | open |  | No map layers; combo chart is not spatial | client |
| T06-15 | Viz in Tooltip | P2 | open |  | Tooltips show text fields only (P18 tooltipExtra); no embedded chart | client |
| T06-16 | Map mark detail control | P2 | open |  | No spatial geometry; Detail shelf exists for charts only | client |
| T06-17 | Spatial geometry ingestion | P3 | open |  | No geometry ingestion; ClickHouse geo types not handled | both |
| T06-18 | GeoJSON import | P2 | open |  | No file upload/import beyond workbook JSON | both |
| T06-19 | KML import | P3 | open |  | No KML parsing | client |
| T06-20 | ESRI Shapefile / MapInfo inputs | P3 | open |  | No shapefile/MapInfo parsers | client |
| T06-21 | Map layer ordering and symbol styling | P2 | open |  | No map layers or styling | client |

## 7. Statistics and forecasting

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T07-01 | Analytics pane | P1 | built | Features/Dashboard/dashboards.js:analyticsPanel | Toggled card of select controls, separate from field list; not drag-and-drop | - |
| T07-02 | Constant line | P1 | built | Features/Dashboard/analytics-model.js:refValue; chart.js:addAnalytics | Constant line on Bar/Line/Area, first measure only | - |
| T07-03 | Average line | P1 | partial | Features/Dashboard/analytics-model.js:refValue | Overall mean of first measure's shown rows only; no per-pane or per-cell scope | client |
| T07-04 | Reference line | P1 | partial | Features/Dashboard/analytics-model.js:REF_CHOICES | Constant or avg/median/min/max of shown values; not linked to field, calculation or parameter | client |
| T07-05 | Reference band | P2 | partial | Features/Dashboard/dashboards.js:analyticsPanel; chart.js:addAnalytics | Band between two typed constants; no measure or parameter bounds | client |
| T07-06 | Distribution band | P2 | open |  | No percentile, quantile or std-dev distribution band | both |
| T07-07 | Median with quartiles | P2 | partial | Features/Dashboard/analytics-model.js:refValue; ClickHouse/ClickHouseGateway.cs:BoxPlotAsync | Median reference line and box plot Q1/Q3 exist separately; no median-with-IQR overlay | client |
| T07-08 | Box plot | P2 | partial | ClickHouse/ClickHouseGateway.cs:BoxPlotAsync; chart.js:buildBoxplot | Quartiles via quantile(); whiskers are min/max, no outlier points; single table only | both |
| T07-09 | Average with 95% CI | P2 | open |  | No average with confidence interval | both |
| T07-10 | Median with 95% CI | P2 | open |  | No median with confidence interval | both |
| T07-11 | Row/column subtotals and grand totals | P1 | built | Features/Dashboard/dashboards.js:crosstabTable (totals) | Grand and first-level subtotals; avg/distinct show dash (not re-aggregated) | - |
| T07-12 | Trend line: linear | P2 | built | Features/Dashboard/analytics-model.js:trendFit | OLS linear over category index (not date axis); first measure only | - |
| T07-13 | Trend line: log / exponential | P2 | partial | Features/Dashboard/analytics-model.js:trendFit | Log (a+b ln(x+1)) only; no exponential model | client |
| T07-14 | Trend line: polynomial / power | P3 | partial | Features/Dashboard/analytics-model.js:trendFit | Fixed 2nd-order polynomial only; no configurable degree, no power model | client |
| T07-15 | Per-color-group trend line | P2 | open |  | Trend fitted on first series only; no per-colour-group models | client |
| T07-16 | Trend model diagnostics | P2 | partial | Features/Dashboard/dashboards.js:2578 | R-squared in trend label only; no equation, p-value or parameters | client |
| T07-17 | Trend confidence bands | P2 | open |  | No confidence bands or force-zero-intercept option | client |
| T07-18 | Forecasting with exponential smoothing | P2 | partial | Features/Dashboard/analytics-model.js:trendSeries | Forecast is extrapolation of the linear/log/poly trend, not exponential smoothing | client |
| T07-19 | Forecast horizon options | P2 | partial | Features/Dashboard/analytics-model.js:FORECAST_CHOICES | Only 3/6/12 steps on line/area; no history window, model family, or incomplete-period handling | client |
| T07-20 | Seasonality selection | P2 | open |  | No seasonality; single trend model | client |
| T07-21 | Forecast missing-data handling | P2 | open |  | No missing-data option; blanks skipped in fit | client |
| T07-22 | Forecast confidence / prediction interval | P2 | open |  | No prediction interval | client |
| T07-23 | Forecast model description | P2 | open |  | No forecast model description or quality metrics | client |
| T07-24 | K-means clustering | P2 | open |  | No k-means or any clustering | both |
| T07-25 | Automatic/manual cluster count | P2 | open |  | No cluster count suggestion or setting | both |
| T07-26 | Save cluster labels as dimension | P2 | open |  | No saving cluster labels as a dimension | both |

## 8. Dashboards and actions

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T08-01 | New dashboard workspace | P0 | partial | Features/Tabs/tabs.js:initTabs; Features/Core/store.js:createDashboard | A dashboard tab holds exactly one worksheet; no combining of several worksheets | client |
| T08-02 | Audience/goals planning guide | P2 | open |  | No audience/goal planning prompt | client |
| T08-03 | Dashboard pane and layout sidebar | P0 | open |  | Sidebar lists tables/tabs; no sheet list, object palette or dashboard layout controls | client |
| T08-04 | Dashboard device preview | P1 | open |  | No phone/tablet/desktop preview | client |
| T08-05 | Device-specific layouts | P2 | open |  | No alternate device layouts | client |
| T08-06 | Fixed dashboard size | P1 | open |  | No dashboard canvas size; Format Fit (chart-fit.js) only fits a chart in its pane | client |
| T08-07 | Automatic size | P1 | partial | Features/Dashboard/chart.js:101 (ResizeObserver); dashboard.css:423 | Worksheet fills window and has phone breakpoint; no dashboard-level size mode | client |
| T08-08 | Range-constrained size | P2 | open |  | No min/max size constraints | client |
| T08-09 | Tiled layout | P0 | open |  | Single chart card per tab; no tiled regions | client |
| T08-10 | Floating layout | P1 | open |  | No floating objects or overlay placement | client |
| T08-11 | Drag-drop worksheet composition | P0 | open |  | Cannot place saved worksheets into a dashboard; one worksheet per tab | client |
| T08-12 | Resize and reorder tiles | P0 | open |  | No chart tiles to resize or reorder; one chart per tab | client |
| T08-13 | Dashboard title and text formatting | P0 | partial | Features/Dashboard/dashboards.js:932 (editable title/caption); Core/store.js:141 | Per-worksheet title and caption editable; tab rename; no dashboard title or text boxes | client |
| T08-14 | Text widget | P1 | partial | Features/Dashboard/dashboards.js:932 | Only a ≤300-char caption on the worksheet; no free text widget placement | client |
| T08-15 | Image widget | P1 | open |  | No image widget or upload | client |
| T08-16 | Blank/spacer object | P1 | open |  | No spacer/blank object | client |
| T08-17 | Navigation button | P1 | open |  | No navigation buttons; bookmarks (bookmarks-dialog.js) are menu-only | client |
| T08-18 | Button labeling/tooltip | P1 | open |  | No navigation button to label | client |
| T08-19 | Use sheet as filter | P0 | partial | Features/Dashboard/dashboards.js:2777 toggleSelection; :2370 | Click selects a mark and Keep only filters the same worksheet; no other charts to constrain | client |
| T08-20 | Filter action setup | P1 | open |  | No configurable source/target/linking-dimension actions; shared filters (P40) are not actions | client |
| T08-21 | Highlight action | P1 | partial | Features/Dashboard/dashboards.js:2777; :2640 legendFocus | Selected mark/legend item highlighted within one chart; no linked charts | client |
| T08-22 | Action triggers | P1 | open |  | Click only, fixed; no hover or menu trigger options | client |
| T08-23 | Multi-mark selection | P1 | open |  | Single-mark selection only; no ctrl-click, rectangle or lasso (brushSelect false) | client |
| T08-24 | Clear-selection behavior | P1 | partial | Features/Dashboard/dashboards.js:587 | Clear button restores all; no preserve-current or filter-to-none option | client |
| T08-25 | Cross-dashboard interactions | P2 | open |  | Single worksheet per tab; no cross-dashboard linking | client |
| T08-26 | Go-to-sheet action | P2 | open |  | URL action (action-model.js) opens external https link only; no sheet navigation | client |
| T08-27 | Set action concept | P3 | open |  | No set actions; parameters are not driven by selection | client |
| T08-28 | Story sequencing | P2 | open |  | No story/sequence; bookmarks are not ordered steps | client |
| T08-29 | Conditional tooltips / embed chart in tooltip | P2 | open |  | Tooltip text fields only (chart.js:extraTooltip); no embedded chart or conditions | client |
| T08-30 | Design consistency checks | P2 | open |  | No design-consistency guidance or checks | client |

## 9. Consumption and ask-data

| ID | Feature | Phase | Status | Evidence | Missing / note | Layer |
|---|---|---|---|---|---|---|
| T09-12 | Source and data-use documentation | P1 | partial | Features/Dashboard/dashboards.js:autoCaption; :beginPrint | Caption/print header list fields and filters; no last-query time, calc definitions or data notes | client |
| T09-16 | Mobile browser viewing | P1 | built | Features/Dashboard/dashboard.css:423 (max-width 640px); :210 (pointer coarse) |  | - |
| T09-17 | Natural-language Ask Data concept | P3 | open |  | No natural-language query parser | client |
| T09-18 | Metadata preview in question interface | P3 | open |  | No question interface; distinct values only in filter pickers | client |
