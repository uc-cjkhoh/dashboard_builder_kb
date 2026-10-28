# Tableau inventory — removed and excluded topics

Part of the [feature inventory](tableau-features.md). What the single-user, read-only product does not take from the guidebook, and why.

## Removed: server-side features

The product is a single-user tool with a read-only ClickHouse connection and browser-held state, so these requirements are dropped.

### Extracts and snapshots

| ID | Feature | Was |
|---|---|---|
| T01-26 | Packaged workbook concept | P2 |
| T02-20 | Data extract or materialized snapshot | P2 |
| T02-21 | Scheduled extract refresh | P2 |
| T02-22 | Incremental extract refresh | P2 |
| T02-23 | Extract-level row filters | P2 |
| T02-24 | Extract aggregation and sampling options | P2 |

### Publication, accounts and access control

| ID | Feature | Was |
|---|---|---|
| T01-27 | Read-only workbook consumption | P1 |
| T02-35 | Source/data governance considerations | P2 |
| T09-01 | Publish workbook inside the application | P1 |
| T09-02 | Project and subproject organization | P1 |
| T09-03 | Workbook title and description | P0 |
| T09-04 | Search/discovery tags | P2 |
| T09-05 | Select published sheets | P1 |
| T09-06 | Tabbed published views | P1 |
| T09-07 | Save default selection state | P2 |
| T09-08 | User sign-in | P1 |
| T09-09 | Project access management | P1 |
| T09-10 | Viewer vs editor roles | P1 |
| T09-11 | Row-level audience filters | P2 |
| T09-13 | Share link | P1 |
| T09-14 | Embed an interactive dashboard | P2 |
| T09-15 | Embed responsive view | P2 |
| T09-19 | Public publishing mode | P3 |
| T09-20 | Download/hide/delete published items | P2 |
| T09-21 | Saved profile/galleries concept | P3 |

### Uploads and file ingestion

| ID | Feature | Was |
|---|---|---|
| T02-01 | Upload CSV and delimited text | P0 |
| T02-02 | Upload Excel files | P1 |
| T02-03 | Import JSON files | P2 |
| T02-04 | Import data from clipboard | P1 |
| T02-17 | Wildcard union | P2 |

### Data preparation flows (saved, materialised output)

| ID | Feature | Was |
|---|---|---|
| T10-01 | Visual flow builder | P1 |
| T10-02 | Input node | P1 |
| T10-03 | Flow input sample and preview | P1 |
| T10-04 | Sample-size control | P2 |
| T10-05 | Additional input connections | P1 |
| T10-06 | Wildcard union node | P2 |
| T10-07 | Input field exclusion | P1 |
| T10-08 | Search and bulk-select input fields | P1 |
| T10-09 | Profile pane | P1 |
| T10-10 | Profile data table | P1 |
| T10-11 | Cleaning step node | P1 |
| T10-12 | Change log for cleaning steps | P2 |
| T10-13 | Flow calculated-field step | P1 |
| T10-14 | Construct date from year/month/day | P1 |
| T10-15 | Edit/recode values | P1 |
| T10-16 | Type conversion after recoding | P1 |
| T10-17 | Rename cleaning steps | P1 |
| T10-18 | Trim whitespace | P1 |
| T10-19 | Automatic/custom split in a flow | P1 |
| T10-20 | Group and replace similar strings | P2 |
| T10-21 | Manual categorical grouping | P1 |
| T10-22 | Union node | P1 |
| T10-23 | Union field alignment | P1 |
| T10-24 | Mismatched-fields only filter | P2 |
| T10-25 | Join node | P1 |
| T10-26 | Join profile/preview | P2 |
| T10-27 | Output node | P1 |
| T10-28 | Run flow | P1 |
| T10-29 | Export cleaned data to CSV | P1 |
| T10-30 | Save/reopen/re-run flow | P1 |

### Where the need remains

- **Uploads:** none. Data comes from ClickHouse tables; a one-off file has to be loaded into ClickHouse outside the app.
- **Extracts and snapshots:** the result cache and approximate mode (D25) speed up repeat queries; workbook Export/Import carries definitions, never data.
- **Publication and access:** the workbook file is the share unit (Export/Import); presentation mode and the phone-browser view cover consumption (T01-24, T09-16).
- **Preparation flows:** cleaning that needs no materialised output stays in the data source and calculation features (T02-26 to T02-34, T04-15 to T04-27).

## Excluded or substituted book topics

These entries are deliberately **not** functional requirements for the proposed standalone product. Where possible, an equivalent native interaction is already inventoried above.

| Guidebook topic | Source | Reason and scope decision |
|---|---|---|
| Python/R/MATLAB and TabPy or RServe calculations | Ch. 7, pp. 168–178 | Require third-party language runtimes, services, scripts or libraries; core statistics and k-means remain native. |
| IFTTT+Google Sheets automatic collection | Ch. 2, pp. 42–43 | Dependent on third-party accounts and a separate collection service. |
| Google Analytics traffic collection | Ch. 2, pp. 43–46 | Dependent on external analytics property/account and external tracking. |
| Dropbox, OneDrive, Salesforce, ServiceNow, BigQuery and similar SaaS connectors | Ch. 2, pp. 30–31 | Account/service-specific integrations; only local files and generic app-native standard SQL connections are proposed. |
| Web Data Connector and community connectors | Ch. 2, pp. 30–31 | Require custom third-party connector implementation and dependency maintenance. |
| Mapbox maps and third-party map services | Ch. 6, pp. 144–146 | Require an external mapping account, access token or mapping service. Use bundled/local base geometry instead. |
| Download datasets from external open-data portals | Ch. 6, pp. 148–154 | Sample data acquisition, not a core analytics application feature. |
| External web page/URL actions and mailto email workflows | Ch. 8, pp. 195–198 | Depend on external web content, email clients or browser plugins; internal chart filtering, highlighting and navigation stay. |
| Cloud Dashboard Starters for Marketo/Eloqua/Salesforce/ServiceNow | Ch. 8, pp. 199–201 | Require vendor cloud products and cloud credentials; generic in-app templates may be an optional enhancement. |
| Tableau Server/Online/Public/Reader/Mobile products as integrations | Ch. 1, pp. 4–5; Ch. 9, pp. 207–220 | Do not reproduce product dependencies; build equivalent native web publication, reader mode and mobile-responsive views. |
| External user-installed GIS editors (e.g. QGIS) | Ch. 6, p. 151 | Not needed; spatial format inputs must be accepted directly when implemented. |
| External dashboard extensions and arbitrary embedded web pages | Ch. 8, p. 185 | Require external extension code or web content; native text/image/widgets remain. |
| Tableau-proprietary workbook/extract format compatibility | Ch. 1, pp. 21–23; Ch. 10, p. 243 | Support native JSON/portable archive and CSV instead of claiming .twb/.twbx/.hyper/.tde compatibility. |
