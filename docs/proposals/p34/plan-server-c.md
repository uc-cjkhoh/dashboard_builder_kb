# P34 plan — Server C: Task 3 implementation, endpoint removal (Task 4)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/` unless they start
with `tests/`.

## Task 3 implementation

**`ClickHouse/RequestValidation.cs` — add** (`using System.Globalization;`):

```csharp
/// <summary>Converts a filter value to its column's category before it is bound — a value that doesn't fit is a 400, not a ClickHouse 502.</summary>
public static class FilterValues
{
    private static readonly string[] DateFormats = ["yyyy-MM-dd", "yyyy-MM-dd HH:mm", "yyyy-MM-dd HH:mm:ss", "yyyy-MM-ddTHH:mm", "yyyy-MM-ddTHH:mm:ss"];
    // Digits, optional sign, one '.', optional exponent — rejects "1,000", "1 000", "0x10", "NaN", "Infinity".
    private static readonly Regex PlainNumber = new(@"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$", RegexOptions.CultureInvariant);

    public static (string Type, object Value) Coerce(string category, string column, string raw, string field)
    {
        var v = raw.Trim();
        switch (category)
        {
            case ClickHouseType.Numeric:
                if (PlainNumber.IsMatch(v) && double.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out var d) && double.IsFinite(d))
                    return ("Float64", d);
                throw new RequestValidationException($"'{raw}' is not a number for column {column}.", field);
            case ClickHouseType.Temporal:
                if (DateTime.TryParseExact(v, DateFormats, CultureInfo.InvariantCulture, DateTimeStyles.None, out var t))
                    return ("String", t.ToString(v.Length == 10 ? "yyyy-MM-dd" : "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture));
                throw new RequestValidationException($"'{raw}' is not a date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS) for column {column}.", field);
            case ClickHouseType.Boolean:
                return v.ToLowerInvariant() switch
                {
                    "true" or "1" => ("UInt8", (byte)1),
                    "false" or "0" => ("UInt8", (byte)0),
                    _ => throw new RequestValidationException($"'{raw}' is not true or false for column {column}.", field),
                };
            case ClickHouseType.Text:
                return ("String", raw);
            default:
                throw new RequestValidationException($"Column {column} can't be filtered — its type can't be compared.", field);
        }
    }
    /// <summary>Order two coerced values; 0 for categories where order isn't checked (text).</summary>
    public static int Compare(string category, object a, object b) => category switch
    {
        ClickHouseType.Numeric => ((double)a).CompareTo((double)b),
        ClickHouseType.Temporal => string.CompareOrdinal((string)a, (string)b),
        _ => 0,
    };
}
```

**`ClickHouseGateway.cs` — replace `BuildCondition`:**

```csharp
internal static string BuildCondition(
    string? op, string paramBase, string expr, string category, string column, string field,
    string? value, IReadOnlyList<string>? values, List<(string Name, string Type, object Value)> parameters)
{
    switch ((op ?? string.Empty).ToLowerInvariant())
    {
        case "in":
        {
            var typed = (values ?? []).Select(v => FilterValues.Coerce(category, column, v ?? "", field)).ToList();
            if (typed.Count == 0) throw new RequestValidationException("Pick at least one value.", field);
            var type = typed[0].Type;
            object arr = type switch
            {
                "Float64" => typed.Select(t => (double)t.Value).ToArray(),
                "UInt8" => typed.Select(t => (byte)t.Value).ToArray(),
                _ => typed.Select(t => (string)t.Value).ToArray(),
            };
            parameters.Add((paramBase, $"Array({type})", arr));
            return $"{expr} IN {{{paramBase}:Array({type})}}";
        }
        case "between":
        {
            if (values is not { Count: 2 }) throw new RequestValidationException("A range filter needs both From and To.", field);
            var lo = FilterValues.Coerce(category, column, values[0] ?? "", field);
            var hi = FilterValues.Coerce(category, column, values[1] ?? "", field);
            if (FilterValues.Compare(category, lo.Value, hi.Value) > 0)
                throw new RequestValidationException($"From must be less than or equal to To for column {column}.", field);
            var (na, nb) = ($"{paramBase}a", $"{paramBase}b");
            parameters.Add((na, lo.Type, lo.Value));
            parameters.Add((nb, hi.Type, hi.Value));
            return $"{expr} >= {{{na}:{lo.Type}}} AND {expr} <= {{{nb}:{hi.Type}}}";
        }
        default:
        {
            if (!Operators.TryGetValue(op ?? string.Empty, out var sqlOp)) throw new UnknownIdentifierException("Unknown operator.");
            var (type, typedValue) = FilterValues.Coerce(category, column, value ?? "", field);
            parameters.Add((paramBase, type, typedValue));
            return $"{expr} {sqlOp} {{{paramBase}:{type}}}";
        }
    }
}
```

**`BuildSingleTableFilters`** now takes `IReadOnlyList<StatFilter>` and delegates:

```csharp
for (var i = 0; i < filters.Count; i++)
{
    var f = filters[i];
    if (string.IsNullOrEmpty(f.Column) || !byName.TryGetValue(f.Column, out var ci)) throw new UnknownIdentifierException("Unknown column.");
    conditions.Add(BuildCondition(f.Op, $"p{i}", Identifier.Quote(f.Column), ci.Category, f.Column, $"filters[{i}]", f.Value, f.Values, parameters));
}
```

**`QueryAsync` filter loop:**
`conditions.Add(BuildCondition(f.Op, $"p{i}", expr, categories[Key(f.Db, f.Table)][f.Column], f.Column, $"filters[{i}]", f.Value, f.Values, parameters));`

**`QueryAsync` measures** — reject meaningless aggregations and record which outputs are numeric:

```csharp
var measNumeric = new List<bool>();
// inside the foreach, after the Aggregations check:
var category = mAgg == "count" ? ClickHouseType.Numeric : (await ColumnsOf(m.Db, m.Table)).GetValueOrDefault(m.Column, ClickHouseType.Other);
if (mAgg is "sum" or "avg" && category != ClickHouseType.Numeric)
    throw new RequestValidationException($"{mAgg} needs a numeric column — {m.Column} is {category}.", "measures");
measNumeric.Add(mAgg is "count" or "countdistinct" or "sum" or "avg" || category == ClickHouseType.Numeric);
// the implicit count() fallback adds measNumeric.Add(true)
```

**Reading values:** `var values = new object?[measExprs.Count];` and
`values[i] = reader.IsDBNull(idx) ? null : ToResultValue(reader.GetValue(idx), measNumeric[i]);`

```csharp
/// <summary>A measure cell for JSON: finite double, display string for non-numeric min/max, or null
/// (SQL NULL, or NaN/∞ from an aggregate over no rows — System.Text.Json can't write those).</summary>
internal static object? ToResultValue(object? raw, bool numeric)
{
    if (raw is null or DBNull) return null;
    if (!numeric) return FormatCell(raw);
    var d = Convert.ToDouble(raw, CultureInfo.InvariantCulture);
    return double.IsFinite(d) ? d : null;
}
```

Make `FormatCell` `internal static` and add, before the `IFormattable` arm:
`DateTime dt => dt.ToString(dt.TimeOfDay == TimeSpan.Zero ? "yyyy-MM-dd" : "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),`
`DateTimeOffset dto => dto.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture),`

**Box plot:** skip a row whose five numbers aren't all finite (a no-row group yields `nan`) — compute the
five values into locals, `if (!new[] { lo, q1, med, q3, hi }.All(double.IsFinite)) continue;`.

**Models:** `QueryModels.cs` → `QueryResultRow(IReadOnlyList<string?> Keys, IReadOnlyList<object?> Values)`.
`StatisticalModels.cs` → add `public sealed record StatFilter(string Column, string Op, string? Value, string[]? Values = null);`
and use `StatFilter[]? Filters` in `HistogramRequest` and `BoxPlotRequest`. `RequestRules.ValidateStatFilters`
takes `StatFilter[]?` and passes `f.Values`. `CsvUtil` value cells:
`row.Values.Select(v => Escape(v switch { null => "", double d => d.ToString(CultureInfo.InvariantCulture), _ => v.ToString() ?? "" }))`.

## Task 4: Remove the uncalled endpoints; smoke-test the contract

**Files:** Modify `Features/Dashboard/QueryController.cs` (delete `Aggregate`), `Features/Schema/SchemaController.cs`
(delete `Preview`, `Count`), `ClickHouse/ClickHouseGateway.cs` (delete `AggregateAsync`, `PreviewAsync`,
`RowCountAsync`, `MaxPreviewRows`), `ClickHouse/SchemaModels.cs` (delete `PreviewResult`),
`Features/Core/api.js` (delete `preview`, `count`, `aggregate`). Delete `ClickHouse/AggregateModels.cs`.
Test: `tests/DashboardBuilder.Tests/SchemaEndpointTests.cs` (the three tests for these routes).

- [ ] **Step 1: Change the three route tests** to assert the routes are gone:

```csharp
[Theory]
[InlineData("GET", "/api/databases/default/tables/t/preview?limit=10")]
[InlineData("GET", "/api/databases/default/tables/t/count")]
[InlineData("POST", "/api/databases/default/tables/t/aggregate")]
public async Task Removed_endpoints_are_gone(string method, string url)
{
    var req = new HttpRequestMessage(new HttpMethod(method), url);
    if (method == "POST") req.Content = JsonContent.Create(new { });
    var resp = await _factory.CreateClient().SendAsync(req);
    Assert.Equal(HttpStatusCode.NotFound, resp.StatusCode);
}
```

- [ ] **Step 2: Run** `dotnet test --filter SchemaEndpointTests` — expected FAIL (routes still answer 409).
- [ ] **Step 3: Delete** the members and files listed above. Confirm nothing still references them:
  `grep -rn "AggregateAsync\|PreviewAsync\|RowCountAsync\|AggregateRequest\|AggregateFilter\|PreviewResult\|api\.preview\|api\.count\|api\.aggregate" src tests`
  → no output.
- [ ] **Step 4: Run** `dotnet build -c Release && dotnet test` — expected PASS, no warnings about the removed types.
- [ ] **Step 5: Smoke-test** on the dev port. Start: `cd src/DashboardBuilder && ASPNETCORE_URLS=http://localhost:5180 dotnet run &`
  then run:

```bash
B=http://localhost:5180/api; J='-H Content-Type:application/json'
s() { curl -s -o /tmp/p34.out -w '%{http_code} ' "$@"; head -c 160 /tmp/p34.out; echo; }
s $J -d '{ bad'                                        $B/query             # 400 {"error":"Request body is missing or isn't valid JSON."}
s $J -d ''                                             $B/connection        # 400 same message
s $J -d '{"host":"h","port":"abc","user":"u"}'         $B/connection        # 400 field port
s $J -d '{"host":"https://h","port":8443,"user":"u"}'  $B/connection        # 400 field host, scheme message
s $J -d '{"host":"h:8443","port":8443,"user":"u"}'     $B/connection        # 400 field host, port message
s $J -d '{"host":"h","user":"u"}'                      $B/connection        # 400 "Port is required."
s $J -d "{\"host\":\"$(head -c 300000 /dev/zero | tr '\0' a)\"}" $B/connection  # 413 "Request too large."
s $J -d '{}'                                           $B/query             # 409 not connected (rules run after the connection check)
s -X GET $B/databases/default/tables/t/count                              # 404
fuser -k 5180/tcp
```

  Every line must print the status in its comment and a `{"error":…}` body with no `System.` text. If a
  dev ClickHouse is available ([development.md](../../operations/development.md)), also connect and check: 9
  filters → 400 `filters`; `limit: 0` → 400 `limit`; `"value":"abc"` on a numeric column → 400 naming the
  column; `min` of a date column → 200 with an ISO date string in `values`.
- [ ] **Step 6: Checkpoint.**
