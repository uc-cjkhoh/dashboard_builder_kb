# Out of scope

Deliberately excluded, so not backlog. The product is a single-user tool with a read-only ClickHouse connection and browser-held state. IDs are stable and not renumbered, so gaps in the T-numbering are expected.

## Removed: server-side requirements (60)

| Topic (requirement IDs) | Why excluded, and where the need remains |
|---|---|
| **Extracts and snapshots** (6): T01-26 Packaged workbook concept; T02-20 Data extract or materialized snapshot; T02-21 Scheduled extract refresh; T02-22 Incremental extract refresh; T02-23 Extract-level row filters; T02-24 Extract aggregation and sampling options | Need server-side storage; the app has no application database. The result cache and approximate mode (D25) speed up repeat queries; workbook Export/Import carries definitions, never data. |
| **Publication, accounts and access control** (19): T01-27 Read-only workbook consumption; T02-35 Source/data governance considerations; T09-01 Publish workbook inside the application; T09-02 Project and subproject organization; T09-03 Workbook title and description; T09-04 Search/discovery tags; T09-05 Select published sheets; T09-06 Tabbed published views; T09-07 Save default selection state; T09-08 User sign-in; T09-09 Project access management; T09-10 Viewer vs editor roles; T09-11 Row-level audience filters; T09-13 Share link; T09-14 Embed an interactive dashboard; T09-15 Embed responsive view; T09-19 Public publishing mode; T09-20 Download/hide/delete published items; T09-21 Saved profile/galleries concept | Single-user tool with no sign-in or sharing service. The workbook file is the share unit (Export/Import); presentation mode and the phone-browser view cover consumption (T01-24, T09-16). |
| **Uploads and file ingestion** (5): T02-01 Upload CSV and delimited text; T02-02 Upload Excel files; T02-03 Import JSON files; T02-04 Import data from clipboard; T02-17 Wildcard union | The only data source is a read-only ClickHouse connection; a one-off file has to be loaded into ClickHouse outside the app. |
| **Data preparation flows (saved, materialised output)** (30): T10-01 Visual flow builder; T10-02 Input node; T10-03 Flow input sample and preview; T10-04 Sample-size control; T10-05 Additional input connections; T10-06 Wildcard union node; T10-07 Input field exclusion; T10-08 Search and bulk-select input fields; T10-09 Profile pane; T10-10 Profile data table; T10-11 Cleaning step node; T10-12 Change log for cleaning steps; T10-13 Flow calculated-field step; T10-14 Construct date from year/month/day; T10-15 Edit/recode values; T10-16 Type conversion after recoding; T10-17 Rename cleaning steps; T10-18 Trim whitespace; T10-19 Automatic/custom split in a flow; T10-20 Group and replace similar strings; T10-21 Manual categorical grouping; T10-22 Union node; T10-23 Union field alignment; T10-24 Mismatched-fields only filter; T10-25 Join node; T10-26 Join profile/preview; T10-27 Output node; T10-28 Run flow; T10-29 Export cleaned data to CSV; T10-30 Save/reopen/re-run flow | Need saved flows and materialised output. Cleaning that needs none stays in the data source and calculation features (T02-26 to T02-34, T04-15 to T04-27). |

## Excluded or substituted book topics (13)

| Topic | Why excluded |
|---|---|
| Python/R/MATLAB and TabPy or RServe calculations | Require third-party language runtimes, services, scripts or libraries; core statistics and k-means remain native. |
| IFTTT+Google Sheets automatic collection | Dependent on third-party accounts and a separate collection service. |
| Google Analytics traffic collection | Dependent on external analytics property/account and external tracking. |
| Dropbox, OneDrive, Salesforce, ServiceNow, BigQuery and similar SaaS connectors | Account/service-specific integrations; only local files and generic app-native standard SQL connections are proposed. |
| Web Data Connector and community connectors | Require custom third-party connector implementation and dependency maintenance. |
| Mapbox maps and third-party map services | Require an external mapping account, access token or mapping service. Use bundled/local base geometry instead. |
| Download datasets from external open-data portals | Sample data acquisition, not a core analytics application feature. |
| External web page/URL actions and mailto email workflows | Depend on external web content, email clients or browser plugins; internal chart filtering, highlighting and navigation stay. |
| Cloud Dashboard Starters for Marketo/Eloqua/Salesforce/ServiceNow | Require vendor cloud products and cloud credentials; generic in-app templates may be an optional enhancement. |
| Tableau Server/Online/Public/Reader/Mobile products as integrations | Do not reproduce product dependencies; build equivalent native web publication, reader mode and mobile-responsive views. |
| External user-installed GIS editors (e.g. QGIS) | Not needed; spatial format inputs must be accepted directly when implemented. |
| External dashboard extensions and arbitrary embedded web pages | Require external extension code or web content; native text/image/widgets remain. |
| Tableau-proprietary workbook/extract format compatibility | Support native JSON/portable archive and CSV instead of claiming .twb/.twbx/.hyper/.tde compatibility. |
