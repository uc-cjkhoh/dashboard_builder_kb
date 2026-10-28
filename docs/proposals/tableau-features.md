# Tableau Guidebook Feature Inventory

**Source:** Alexander Loth, *Visual Analytics with Tableau* (Wiley, 2019), uploaded 287-page PDF. The book generally illustrates **Tableau Desktop 2019.1**; this is a guidebook-derived inventory, **not an audit of all Tableau features or the current Tableau product**. Source references use the **printed book page** (PDF page = printed page + 32 for the numbered book chapters).

**Scope rule:** Extract capabilities demonstrated or explicitly described in the book, then target the existing Dashboard Builder: a **single-user** web tool whose only data source is a read-only ClickHouse connection and whose only persistence is the browser (workbook auto-save and Export/Import). Anything that needs server-side storage — uploaded data, extracts, accounts, publication, saved prep flows with materialised output — is **out of scope** and listed under [Removed](tableau-features-excluded.md#removed-server-side-features). Do not require end users to install Python, R, MATLAB, GIS editors, Tableau products, third-party dashboard extensions or separate SaaS services.

## Inventory summary

- **229 scoped feature requirements** in 9 functional domains; priorities: P0 **44**, P1 **107**, P2 **67**, P3 **10**, document-only **1**.
- **60 server-side requirements removed** (single-user scope), listed in [Removed](tableau-features-excluded.md#removed-server-side-features). IDs are stable and **not renumbered**, so gaps are expected (Ch. 10 is gone entirely).
- **13 exclusions and substitutions** explicitly trace features excluded for third-party dependence or proprietary interoperability.
- **P0** foundation and minimum viable product; **P1** practical analytics release; **P2** advanced/native analytics; **P3** optional deferred or sparsely described; **Document only** guidance, not a product control.
- Some capability entries appear in more than one chapter (for example, string split in both the data source and calculated fields). They are kept separately when the **user workflow differs**; counts represent actionable requirements, not unique Tableau menu commands.

## In-scope feature inventory (traceable to the source)

### 1. Application, workbooks, and visual analysis workspace

*Coverage: Ch. 1, pp. 1–23; 28 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T01-01 | Browser-based analytics workspace | Interactive point-and-click authoring without coding; drag fields into a visual specification. | 13–15 | P0 |
| T01-02 | Data pane | List current connection fields and their metadata next to authoring canvas. | 13–17 | P0 |
| T01-03 | Dimension vs. measure roles | Classify descriptive group-by fields separately from quantitative metrics; manually reassign. | 16–17 | P0 |
| T01-04 | Discrete vs. continuous field semantics | Display groups/categories versus quantitative axes and allow switching where valid. | 16–17, 61–63 | P1 |
| T01-05 | Rows shelf | Drag field pills to define breakdown rows or the vertical quantitative axis. | 13–14, 78–79 | P0 |
| T01-06 | Columns shelf | Drag field pills to define breakdown columns or horizontal quantitative axis. | 13–14, 78–79 | P0 |
| T01-07 | Marks card | Encode color, size, label/text, shape, detail, and hover tooltip via fields. | 14, 19–21, 78–79 | P0 |
| T01-08 | Filters shelf | Specify field-level filters affecting worksheet queries and results. | 14, 55–56 | P0 |
| T01-09 | Pages shelf | Bind a field to page-by-page view progression; introduced in the workspace but not demonstrated. | 14 | P3 |
| T01-10 | Sheet canvas and title | Display and rename each worksheet visualization. | 13–14, 19 | P0 |
| T01-11 | Multiple worksheets | Create, duplicate, rename, and switch between sheet tabs. | 14–15, 110 | P0 |
| T01-12 | New dashboard and story controls | Create a dashboard or sequenced story from workbook sheets. | 14–15 | P1 |
| T01-13 | Data source editor tab | Switch between schema modeling and visualization authoring. | 12–14 | P0 |
| T01-14 | Start screen and recent sources | Open existing workbooks and select new or recent data sources. | 11, 15, 26 | P1 |
| T01-15 | Mouse field placement and double-click defaults | Use drag-and-drop or auto-placement after double-clicking selected fields. | 17–18 | P1 |
| T01-16 | Undo and redo | Revert and restore analytical and layout edits. | 15 | P0 |
| T01-17 | Swap rows and columns | Swap worksheet orientation and corresponding chart axes. | 54, 65, 110 | P1 |
| T01-18 | View data behind marks | Inspect the detailed rows contributing to an aggregate mark. | 79 | P1 |
| T01-19 | Tooltip field editor | Customize formatted hover information and include additional measures/dimensions. | 21–22 | P0 |
| T01-20 | Color palettes and discrete legend | Assign categorical colors and edit legends. | 20–21, 54–55 | P0 |
| T01-21 | Continuous color scales | Apply gradient palettes for numeric measures and edit range. | 21, 68–69 | P1 |
| T01-22 | Mark shape and size options | Set mark shape, marker size, border, and labels. | 19–21, 67–69 | P1 |
| T01-23 | Worksheet-level formatting | Configure font, alignment, shading, cell sizes, and workbook appearance. | 16 | P1 |
| T01-24 | Presentation mode | Expand dashboard display to use available screen space. | 16 | P1 |
| T01-25 | Save, open, Save As | Persist visualization definitions and metadata in a workbook. | 15, 21–23 | P0 |
| T01-28 | Export to PDF and image | Export views and dashboards into PDFs and graphic files. | 15–16 | P1 |
| T01-29 | Export worksheet data or crosstab | Export underlying rows or aggregate cross-tabular results. | 15, 110 | P1 |
| T01-30 | Workbook performance recording | Measure dashboard query and rendering time for diagnosis. | 16 | P2 |

### 2. Data source, modeling, live queries, metadata

*Coverage: Ch. 2, pp. 25–48; 26 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T02-05 | Preview source rows | Inspect field names, types, sample values and raw records. | 12, 31, 38–40 | P0 |
| T02-06 | ClickHouse connection | Create a session-scoped connection to the user's ClickHouse server using credentials and secure transport; credentials are never persisted. | 25–30 | P1 |
| T02-07 | Database/schema/table browser | Discover schemas and choose one or more tables. | 31 | P1 |
| T02-08 | Multiple tables in a data model | Add tables from one or more databases on the connected server. | 31–34 | P1 |
| T02-09 | Visual table canvas | Drag logical tables into a visual data model. | 31–32 | P1 |
| T02-10 | Inner join | Keep only rows matching join criteria. | 32 | P1 |
| T02-11 | Left join | Preserve all left rows and unmatched nulls on the right. | 33 | P1 |
| T02-12 | Right join | Preserve right-side rows on a join. | 33 | P1 |
| T02-13 | Full outer join | Preserve unmatched rows from both inputs. | 33 | P1 |
| T02-14 | Join key detection | Suggest join keys using matching field names. | 32 | P2 |
| T02-15 | Compound/non-equality join conditions | Build multiple join predicates including equality and comparison operators. | 32 | P2 |
| T02-16 | Manual table union | Append compatible tables/worksheets. | 34 | P1 |
| T02-18 | Live connection | Query upstream source as data changes, without holding a full copied dataset. | 36 | P1 |
| T02-19 | Manual refresh of live view | Request latest data explicitly when needed. | 36 | P1 |
| T02-25 | Source read-only safety | Prevent transformation or visual analysis from rewriting original source data. | 27 | P0 |
| T02-26 | Rename source field | Replace technical column names with readable names in metadata. | 39 | P0 |
| T02-27 | Hide unused fields | Exclude irrelevant columns from authoring pane and preview. | 39 | P0 |
| T02-28 | Copy field or selected preview values | Reuse preview metadata or data via copy action. | 39 | P2 |
| T02-29 | Alias dimension members | Map coded category values to audience-friendly labels. | 39 | P1 |
| T02-30 | Dimension groups | Combine logically related dimension members into named groups. | 39, 96 | P1 |
| T02-31 | Automatic/custom string split | Split a column on inferred or user-specified separators. | 40 | P1 |
| T02-32 | Unpivot wide columns to rows | Reshape crosstab columns into key-value rows. | 8, 40 | P1 |
| T02-33 | Field details and metadata | Inspect data type, semantic role, sorting and other properties. | 40 | P1 |
| T02-34 | Cast data types | Convert field among string, number, boolean, date, datetime and geographic where valid. | 40–41 | P0 |
| T02-36 | Query pushdown and source-aware optimization | Push supported filter/aggregate work to SQL database, avoid unnecessary joins/unions. | 46–48 | P1 |
| T02-37 | Database indexing/partition guidance | Explain that indexing and partitioning source tables can improve performance; not a database admin UI. | 48 | Document only |

### 3. Charts, visual encodings, filters, and drill-down

*Coverage: Ch. 3, pp. 49–79; 34 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T03-01 | Show Me chart recommender | Recommend compatible charts from selected dimension/measure types and grey out invalid options. | 50–53 | P1 |
| T03-02 | Vertical and horizontal bar chart | Display aggregated measures by category; swap orientation. | 50, 54 | P0 |
| T03-03 | Scatter plot | Place two numeric measures on axes with optionally one mark per entity. | 50, 52–53 | P0 |
| T03-04 | Time-series line chart | Connect measures over a date axis. | 50, 57–58 | P0 |
| T03-05 | Straight, step, and jump line styles | Switch between ordinary, stepped, and gap-aware jump paths. | 57, 59–62 | P1 |
| T03-06 | Temporal hierarchy navigation | Drill year, quarter, month and finer grains; remove unwanted levels. | 58–60 | P1 |
| T03-07 | Continuous and discrete dates | Plot dates on a continuous time axis or discrete category header. | 61–63 | P1 |
| T03-08 | Text crosstab | Arrange categories in rows/columns with numbers as text. | 64–65 | P0 |
| T03-09 | Highlight table | Color full table cells according to a measure. | 64–67 | P1 |
| T03-10 | Heatmap with circles | Encode a matrix measure using circle size and color. | 67–69 | P1 |
| T03-11 | Pie chart | Show contribution of categories to a total using angles. | 51, 137–138 | P1 |
| T03-12 | Bullet chart | Overlay actual performance bars with a target reference marker and optional qualitative bands. | 69–73 | P1 |
| T03-13 | Waterfall chart | Show cumulative positive and negative contributions through steps. | 73–77 | P1 |
| T03-14 | Gantt-bar marks | Represent intervals/steps, including the waterfall construction technique. | 74–76 | P2 |
| T03-15 | Side-by-side measure bars | Compare multiple measures adjacent to each other. | 71–72 | P1 |
| T03-16 | Dual-axis layered view | Overlay two related measures on separate axes. | 116–118, 139–140 | P1 |
| T03-17 | Axis synchronization | Apply a common scale when layering axis measures. | 117–118 | P1 |
| T03-18 | Field-based categorical coloring | Color bars or points by another dimension. | 20, 54–55 | P0 |
| T03-19 | Measure-based intensity coloring | Color marks by continuous aggregate value. | 21, 54, 65–69 | P1 |
| T03-20 | Size encoding | Set mark area or radius based on numeric field. | 19–20, 67–69 | P1 |
| T03-21 | Shape encoding | Switch mark types such as circle, square, pie, bar, and line. | 19–20, 66–69 | P1 |
| T03-22 | Detail encoding | Create distinct marks at a finer granularity without changing color/size. | 78–79 | P1 |
| T03-23 | Labels and text encoding | Place aggregated field values directly on marks. | 19–20, 64–65 | P1 |
| T03-24 | Legend editing | Edit legends, palettes, categorical assignments, and continuous scale. | 20–21, 54–55, 68 | P1 |
| T03-25 | Dimension value filter | Include or exclude chosen category values. | 55–56 | P0 |
| T03-26 | Show interactive filter control | Expose filtering controls directly to dashboard viewers. | 55–56 | P0 |
| T03-27 | Numeric range and measure filter | Constrain aggregated numeric values with visual controls. | 55–56, 139 | P1 |
| T03-28 | Multiple selection and exclusion | Select many filter members or invert the current filter. | 55–56 | P0 |
| T03-29 | Interactive dimension hierarchies | Create named category/subcategory hierarchies with expand/collapse. | 54–56 | P1 |
| T03-30 | Field- and value-based sorting | Sort marks/categories and swap ascending/descending ordering. | 74, 151 | P0 |
| T03-31 | Under-mark source inspection | Reveal detailed rows supporting a visualization mark. | 79 | P1 |
| T03-32 | Fit view modes | Choose standard fit, entire view, width, or height. | 68 | P1 |
| T03-33 | Categorical and diverging color palettes | Provide accessible categorical, sequential and diverging schemes, including reversed palettes. | 68–69 | P1 |
| T03-34 | Format mark borders | Set border and separation to distinguish heatmap/highlight cells. | 66 | P2 |

### 4. Aggregations, calculated fields, date/text logic, parameters

*Coverage: Ch. 4, pp. 81–103; 33 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T04-01 | Aggregation SUM | Aggregate additive measures across the current grouping. | 82 | P0 |
| T04-02 | Aggregation AVG | Compute arithmetic mean per mark. | 82 | P0 |
| T04-03 | Aggregation MEDIAN | Compute median per mark. | 82 | P1 |
| T04-04 | COUNT and COUNT DISTINCT | Count all/non-null records or unique non-null values as appropriate. | 83 | P0 |
| T04-05 | MIN and MAX | Return extremal measure or dimension values. | 83 | P0 |
| T04-06 | Percentiles | Compute chosen percentiles, including 5/10/25/50/75/90/95. | 83 | P1 |
| T04-07 | Standard deviations | Offer sample and population variants. | 83–84 | P1 |
| T04-08 | Variances | Offer sample and population variants. | 84 | P1 |
| T04-09 | ATTR dimension aggregation | Treat single-value descriptive attributes without re-granularizing the visual. | 84 | P2 |
| T04-10 | Null semantics for aggregation | Exclude nulls from aggregate calculation unless deliberately replaced. | 84 | P0 |
| T04-11 | Calculated field creator/editor | Name fields, author expressions, validate and save them in model. | 84–86 | P0 |
| T04-12 | Calculation help/glossary | Show function syntax, validation errors and built-in function descriptions. | 85–86 | P1 |
| T04-13 | Row-level vs aggregate expressions | Evaluate arithmetic on rows or grouped aggregated values as explicitly specified. | 86–87 | P0 |
| T04-14 | Arithmetic calculations | Build ratios and transformations of existing fields. | 84–87 | P0 |
| T04-15 | SPLIT text operator | Extract components of a delimited string. | 88–89 | P1 |
| T04-16 | LEFT and RIGHT string operators | Extract leading or trailing substrings. | 89 | P1 |
| T04-17 | LOWER and UPPER | Normalize case for display or matching. | 89–90 | P1 |
| T04-18 | REPLACE text operator | Substitute substring in a text field. | 90 | P1 |
| T04-19 | CONTAINS text predicate | Detect case-sensitive/case-folded matches for text-search calculated filters. | 100–103 | P1 |
| T04-20 | Date hierarchy and date parts | Derive year, quarter, month, week, day and other date components. | 90–93 | P1 |
| T04-21 | Gregorian and ISO 8601 date conventions | Support ISO week/calendar and traditional Gregorian breakdowns. | 91–92 | P2 |
| T04-22 | Date difference and calculation operators | Compute date arithmetic and date comparisons. | 92 | P1 |
| T04-23 | Date parsing and formatting | Convert date strings, extract date parts, or format date values. | 92–93 | P1 |
| T04-24 | CASE expression | Map mutually exclusive categorical values into outputs. | 94–95 | P1 |
| T04-25 | IF / THEN / ELSE | Build conditional logic with nested Boolean expressions. | 95–96 | P1 |
| T04-26 | IIF ternary conditional | Use compact conditional evaluation with documented null behavior. | 96–97 | P2 |
| T04-27 | IFNULL replacement | Replace null values or supply human-friendly null labels. | 97 | P1 |
| T04-28 | Create a parameter | Define typed input independent of underlying source fields. | 97–98 | P1 |
| T04-29 | Parameter constraints | Support fixed list, numeric range and step size, current/default values. | 97–99 | P1 |
| T04-30 | Parameter controls | Expose sliders, dropdowns or typed text input to viewers. | 97–100 | P1 |
| T04-31 | Parameter-dependent computed metrics | Drive what-if forecasts/scenarios by applying a control value to a calculated measure. | 98–100 | P1 |
| T04-32 | Parameter-fed reference thresholds | Place a user-selected value on a reference line. | 97 | P2 |
| T04-33 | Parameter-driven search box | Use a string parameter with CONTAINS/LOWER and Boolean filter. | 100–103 | P1 |

### 5. Table calculations and level-of-detail expressions

*Coverage: Ch. 5, pp. 105–129; 27 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T05-01 | Calculation evaluation-order model | Explain row-level, aggregated, LOD, post-filter table-calculation stages to avoid wrong results. | 106–107 | P0 |
| T05-02 | Quick running total | Accumulate aggregated values in a chosen order. | 108–109 | P1 |
| T05-03 | Quick difference | Compute delta from previous mark. | 108 | P1 |
| T05-04 | Quick percent difference | Compute relative delta from preceding mark. | 108 | P1 |
| T05-05 | Quick percent of total | Compute fraction of the chosen partition total. | 108 | P1 |
| T05-06 | Quick rank | Rank members by a measure. | 108 | P1 |
| T05-07 | Quick percentile ranking | Place measure within distribution by percentile. | 108 | P1 |
| T05-08 | Quick moving average | Smooth a series over a configurable window. | 108–109 | P1 |
| T05-09 | YTD total | Compute cumulative total within each calendar year. | 109 | P2 |
| T05-10 | Compound growth rate | Calculate growth across measurement periods. | 109 | P2 |
| T05-11 | Year-over-year growth | Compare current value to equivalent period prior year. | 109 | P1 |
| T05-12 | YTD growth | Compare year-to-date growth across periods. | 109 | P2 |
| T05-13 | Table-calculation edit dialog | Change calculation, compute-using dimension and partition behavior. | 110–112 | P1 |
| T05-14 | Table across/down direction | Compute left-to-right, top-to-bottom and other directions. | 111–112 | P1 |
| T05-15 | Specific addressing vs partitioning | Choose compute dimensions and reset by other dimensions. | 111–112 | P1 |
| T05-16 | Calculation-assistance overlay | Show computation direction and mark order while editing. | 111–112 | P2 |
| T05-17 | Duplicate as crosstab | Expose the view's intermediate grouped data in cross-tab form. | 110 | P1 |
| T05-18 | Custom table functions | Support rank and window-based calculations via explicit expression syntax. | 113–122 | P2 |
| T05-19 | Bump chart | Use ranking calculations to plot rank changes over time. | 113–116 | P2 |
| T05-20 | Dual-axis chart with rank/measure | Overlay different series/axes including custom table calculations. | 116–118 | P1 |
| T05-21 | Parameter-adjustable moving average | Compute WINDOW_AVG based on a viewer-set rolling period. | 118–122 | P2 |
| T05-22 | LOD FIXED | Evaluate an expression at explicitly selected grouping dimensions. | 123–124 | P2 |
| T05-23 | LOD INCLUDE | Evaluate at a finer level than the view and then re-aggregate. | 123–126 | P2 |
| T05-24 | LOD EXCLUDE | Evaluate at a coarser level independently of named view dimensions. | 123–129 | P2 |
| T05-25 | First-event cohort analysis | Derive first purchase date per customer from a FIXED LOD expression. | 124–125 | P2 |
| T05-26 | Per-entity aggregate then average | E.g. average per customer region using INCLUDE. | 125–127 | P2 |
| T05-27 | Higher-level benchmark in granular charts | E.g. compare regional data against countrywide total using EXCLUDE. | 127–129 | P2 |

### 6–7. Geospatial analytics; statistics, reference analytics, forecasting and clustering

Chapters 6 (`T06-*`) and 7 (`T07-*`) are in [tableau-features-geo-stats.md](tableau-features-geo-stats.md).

### 8. Dashboard and story composition, navigation and actions

*Coverage: Ch. 8, pp. 181–204; 30 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T08-01 | New dashboard workspace | Combine reusable worksheet charts into interactive dashboard pages. | 181–185 | P0 |
| T08-02 | Audience/goals planning guide | Prompt author for audience, decision objective and key data questions. | 182 | P2 |
| T08-03 | Dashboard pane and layout sidebar | Access sheets, size, object palette, layout and formatting controls. | 183–185 | P0 |
| T08-04 | Dashboard device preview | Preview phone, tablet and desktop layouts. | 184 | P1 |
| T08-05 | Device-specific layouts | Author alternate configurations for smaller screens. | 184 | P2 |
| T08-06 | Fixed dashboard size | Explicit width/height canvas dimensions. | 184 | P1 |
| T08-07 | Automatic size | Adapt layout to available screen width and height. | 184 | P1 |
| T08-08 | Range-constrained size | Limit automatic width/height with min and max dimensions. | 184 | P2 |
| T08-09 | Tiled layout | Snap charts and elements into controlled responsive regions. | 185–187 | P0 |
| T08-10 | Floating layout | Place and resize elements independently, including overlay placement. | 185–191 | P1 |
| T08-11 | Drag-drop worksheet composition | Select saved worksheets and place them into a dashboard. | 185–187 | P0 |
| T08-12 | Resize and reorder tiles | Change placement and available space of chart cards. | 186–187 | P0 |
| T08-13 | Dashboard title and text formatting | Set dashboard title and edit labels and text boxes. | 187–188 | P0 |
| T08-14 | Text widget | Place explanatory instructions and annotations on dashboards. | 185, 201–202 | P1 |
| T08-15 | Image widget | Place uploaded static images in dashboards. | 185 | P1 |
| T08-16 | Blank/spacer object | Reserve whitespace and layout separation. | 185 | P1 |
| T08-17 | Navigation button | Link to another worksheet, dashboard, or story within workbook. | 188–190 | P1 |
| T08-18 | Button labeling/tooltip | Edit navigation target, icon/image, and tooltip. | 189 | P1 |
| T08-19 | Use sheet as filter | Make selected marks constrain other dashboard charts. | 191–192 | P0 |
| T08-20 | Filter action setup | Explicitly choose source views, targets and linking dimensions. | 191–194 | P1 |
| T08-21 | Highlight action | Emphasize corresponding marks across linked charts without discarding others. | 191, 193–194 | P1 |
| T08-22 | Action triggers | Configure hover, selection or menu-driven interactions. | 194 | P1 |
| T08-23 | Multi-mark selection | Select multiple marks with click/rectangle/lasso, with clear-to-reset. | 191–192 | P1 |
| T08-24 | Clear-selection behavior | Restore all, preserve current, or filter to none after clearing selection. | 194 | P1 |
| T08-25 | Cross-dashboard interactions | Link a source chart to a different dashboard within workbook. | 194 | P2 |
| T08-26 | Go-to-sheet action | Navigate between sheets and dashboards based on mark selections. | 191 | P2 |
| T08-27 | Set action concept | Change a named subset of values from interactive selection; mentioned, not taught. | 191 | P3 |
| T08-28 | Story sequencing | Arrange charts and dashboards into presentation steps with annotations. | 15, 189 | P2 |
| T08-29 | Conditional tooltips / embed chart in tooltip | Show detailed secondary visualizations in hover content. | 140–143 | P2 |
| T08-30 | Design consistency checks | Guide limited filters/legends, consistent colors and 2–4-chart visual hierarchy. | 201–202 | P2 |

### 9. Consumption, source documentation and natural-language query

*Coverage: Ch. 9, pp. 205–220; 4 distinct functional requirements.*

| ID | Feature | Behavior documented in the guidebook / app requirement | Book pp. | Phase |
|---|---|---|---|---|
| T09-12 | Source and data-use documentation | Show on a dashboard the source table, time of the last query, calculation definitions and notes about the data. | 206 | P1 |
| T09-16 | Mobile browser viewing | View and filter a dashboard in a phone or tablet browser without installing a dedicated mobile app. | 206, 212–213 | P1 |
| T09-17 | Natural-language Ask Data concept | Parse scoped queries such as 'sum of Sales by Sub-Category' to generate views; no external AI API assumed. | 211–212 | P3 |
| T09-18 | Metadata preview in question interface | Show top field values and calculation definitions during query discovery. | 212 | P3 |

## Removed and excluded

The 60 removed server-side requirements and the 13 excluded or substituted book topics, with reasons, are in [tableau-features-excluded.md](tableau-features-excluded.md).

## Features mentioned briefly vs. fully demonstrated

- The **Pages shelf**, **set actions**, **story authoring**, **some advanced map/service settings**, and **Ask Data** are mentioned or summarized but are **not taught to an implementation specification**. Their P2/P3 status reflects the additional product-design assumptions that would be required.
- **Ask Data** appears in the book as a natural-language query interface (pp. 211–212). It is not equivalent to a conversational AI assistant, and the application should implement a limited, explainable local grammar before attempting unrestricted NLP.
- The guidebook only introduces several advanced analytical tools; their exact numerical equivalence to Tableau depends on implementation choices, including null handling, partitioning, confidence-interval method, exponential-smoothing parameter selection, and k-means seeding.
- **Visualization types** such as bump, waterfall and dual-axis maps are **compositions** built from marks, measures and table calculations, not necessarily separate one-click menu actions.

## Traceability and validation conventions

1. The `TNN-NN` IDs in this inventory are stable requirement identifiers referenced by the product proposal. A validation test should verify the specified user-observable behavior, not visual similarity alone.
2. Book page references refer to the printed pagination (not the PDF viewer page index); for example, Tableau Prep p. 231 is PDF p. 263.
3. **Scope note on dates:** Only capabilities documented in this **2019 source** are extracted. Newly released Tableau capabilities, licensing and edition changes are intentionally not inferred.
4. **Implementation note:** Technology choices, API changes and performance targets in the companion proposal are **new design recommendations** and not claims made by the guidebook.

