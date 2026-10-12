# P34 plan — Server B: rules, typed filters, results, endpoint removal (Tasks 2–4)

Part of the [P34 plan](plan-overview.md). Paths are relative to `src/DashboardBuilder/` unless they start
with `tests/`.

## Task 2 code

**`tests/DashboardBuilder.Tests/ValidationTests.cs`:**

```csharp
using DashboardBuilder.ClickHouse; using Xunit;
namespace DashboardBuilder.Tests;
public class ValidationTests
{
    [Theory]
    [InlineData("clickhouse.example.com")] [InlineData("10.168.49.13")] [InlineData("localhost")]
    [InlineData("::1")] [InlineData("[::1]")] [InlineData("ch_1.internal")] [InlineData("  padded.host  ")]
    public void Valid_hosts_pass(string host) => Assert.Null(RequestRules.HostError(host));

    [Theory]
    [InlineData("https://h", RequestRules.HostSchemeMessage)] [InlineData("h:8443", RequestRules.HostPortMessage)]
    [InlineData("[::1]:8443", RequestRules.HostPortMessage)] [InlineData("h/db", RequestRules.HostPathMessage)]
    [InlineData("bad host", RequestRules.HostInvalidMessage)] [InlineData("-bad.com", RequestRules.HostInvalidMessage)]
    [InlineData("   ", "Host is required.")]
    public void Invalid_hosts_say_why(string host, string message) => Assert.Equal(message, RequestRules.HostError(host));

    [Fact] public void An_overlong_host_is_rejected() => Assert.Equal("Host must be at most 253 characters.", RequestRules.HostError(new string('a', 254)));

    [Theory] [InlineData(null, "port")] [InlineData(0, "port")] [InlineData(65536, "port")]
    public void Port_is_required_and_in_range(int? port, string field)
        => Assert.Equal(field, Assert.Throws<RequestValidationException>(() => RequestRules.ValidateConnect("h", port, "u", "")).Field);

    [Fact] public void A_blank_user_is_rejected()
        => Assert.Equal("user", Assert.Throws<RequestValidationException>(() => RequestRules.ValidateConnect("h", 8443, "  ", "")).Field);
    [Fact] public void An_overlong_password_is_rejected()
        => Assert.Equal("password", Assert.Throws<RequestValidationException>(() => RequestRules.ValidateConnect("h", 8443, "u", new string('p', 257))).Field);

    private static QueryRequest Q(int dims = 1, int measures = 1, int joins = 0, QueryFilter[]? filters = null, int? limit = null, SortRef? sort = null) =>
        new(new TableRef("db", "t"),
            Enumerable.Range(0, joins).Select(i => new JoinRef(new ColumnRef("db", "t", "id"), new ColumnRef("db", $"t{i}", "id"))).ToArray(),
            Enumerable.Range(0, dims).Select(i => new ColumnRef("db", "t", $"d{i}")).ToArray(), [],
            Enumerable.Range(0, measures).Select(i => new MeasureRef("db", "t", $"m{i}", "sum")).ToArray(), filters, limit, sort);
    private static QueryFilter F(string op = "=", string? value = "1", string[]? values = null) => new("db", "t", "c", op, value, values);
    private static string? FieldOf(QueryRequest q) => Assert.Throws<RequestValidationException>(() => RequestRules.ValidateQuery(q)).Field;

    [Fact] public void At_the_limits_a_query_passes()
        => RequestRules.ValidateQuery(Q(dims: 12, measures: 10, joins: 10, filters: Enumerable.Repeat(F(), 8).ToArray(), limit: 500));
    [Fact] public void Thirteen_dimensions_are_rejected() => Assert.Equal("rowDimensions", FieldOf(Q(dims: 13)));
    [Fact] public void Eleven_measures_are_rejected() => Assert.Equal("measures", FieldOf(Q(measures: 11)));
    [Fact] public void Eleven_joins_are_rejected() => Assert.Equal("joins", FieldOf(Q(joins: 11)));
    [Fact] public void Nine_filters_are_rejected_not_dropped() => Assert.Equal("filters", FieldOf(Q(filters: Enumerable.Repeat(F(), 9).ToArray())));
    [Theory] [InlineData(0)] [InlineData(501)] public void Out_of_range_limits_are_rejected(int limit) => Assert.Equal("limit", FieldOf(Q(limit: limit)));
    [Fact] public void An_unknown_operator_is_rejected() => Assert.Equal("filters[0].op", FieldOf(Q(filters: [F("LIKE")])));
    [Fact] public void An_empty_in_list_is_rejected() => Assert.Equal("filters[0].values", FieldOf(Q(filters: [F("in", null, [])])));
    [Fact] public void A_501_value_in_list_is_rejected() => Assert.Equal("filters[0].values", FieldOf(Q(filters: [F("in", null, Enumerable.Repeat("x", 501).ToArray())])));
    [Fact] public void A_half_range_is_rejected() => Assert.Equal("filters[0].values", FieldOf(Q(filters: [F("between", null, ["1", " "])])));
    [Fact] public void An_overlong_value_is_rejected() => Assert.Equal("filters[0]", FieldOf(Q(filters: [F("=", new string('x', 1001))])));
    [Fact] public void A_sort_alias_past_the_dimensions_is_rejected() => Assert.Equal("sort.column", FieldOf(Q(dims: 1, sort: new SortRef("k5", false))));
    [Fact] public void A_null_filter_entry_is_rejected() => Assert.Equal("filters[0]", FieldOf(Q(filters: [null!])));
    [Theory] [InlineData(0)] [InlineData(101)]
    public void Out_of_range_bins_are_rejected(int bins)
        => Assert.Equal("buckets", Assert.Throws<RequestValidationException>(() => RequestRules.ValidateHistogram(new HistogramRequest("c", bins, null))).Field);
    [Theory] [InlineData(0)] [InlineData(1001)]
    public void Out_of_range_distinct_limits_are_rejected(int n)
        => Assert.Equal("limit", Assert.Throws<RequestValidationException>(() => RequestRules.ValidateDistinctLimit(n)).Field);
}
```

**Add to `ClickHouse/RequestValidation.cs`** (`using System.Net; using System.Net.Sockets; using System.Text.RegularExpressions;`):

```csharp
/// <summary>Input rules for every API request. Throws <see cref="RequestValidationException"/>; never clamps.</summary>
public static class RequestRules
{
    public const string HostSchemeMessage = "Enter the host name only — no http:// or https://.";
    public const string HostPortMessage = "Enter the host name only — put the port in Port.";
    public const string HostPathMessage = "Enter the host name only — no path.";
    public const string HostInvalidMessage = "Enter a valid host name or IP address.";
    private static readonly Regex HostName = new(
        @"^[A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?(\.[A-Za-z0-9_]([A-Za-z0-9_-]{0,61}[A-Za-z0-9_])?)*\.?$", RegexOptions.CultureInvariant);
    private static readonly HashSet<string> Ops = new(StringComparer.OrdinalIgnoreCase) { "=", "!=", ">", ">=", "<", "<=", "in", "between" };
    private static RequestValidationException Bad(string message, string field) => new(message, field);

    /// <summary>Null when the host is valid, else the user-facing reason (same text as validate.js).</summary>
    public static string? HostError(string? raw)
    {
        var h = raw?.Trim() ?? "";
        if (h.Length == 0) return "Host is required.";
        if (h.Length > ApiLimits.MaxHostLength) return $"Host must be at most {ApiLimits.MaxHostLength} characters.";
        if (h.Contains("://")) return HostSchemeMessage;
        if (h.Contains('/')) return HostPathMessage;
        if (h.StartsWith('['))
        {
            var close = h.IndexOf(']');
            if (close < 0) return HostInvalidMessage;
            if (close != h.Length - 1) return HostPortMessage;
            return IsIPv6(h[1..close]) ? null : HostInvalidMessage;
        }
        if (h.Count(c => c == ':') >= 2) return IsIPv6(h) ? null : HostInvalidMessage;
        if (h.Contains(':')) return HostPortMessage;
        return HostName.IsMatch(h) ? null : HostInvalidMessage;
    }
    private static bool IsIPv6(string s) => IPAddress.TryParse(s, out var a) && a.AddressFamily == AddressFamily.InterNetworkV6;

    public static void ValidateConnect(string? host, int? port, string? user, string? password)
    {
        if (HostError(host) is { } hostError) throw Bad(hostError, "host");
        if (port is null) throw Bad("Port is required.", "port");
        if (port is < 1 or > 65535) throw Bad("Port must be a whole number from 1 to 65535.", "port");
        if (string.IsNullOrWhiteSpace(user)) throw Bad("User is required.", "user");
        if (user.Trim().Length > ApiLimits.MaxUserLength) throw Bad($"User must be at most {ApiLimits.MaxUserLength} characters.", "user");
        if ((password?.Length ?? 0) > ApiLimits.MaxPasswordLength) throw Bad($"Password must be at most {ApiLimits.MaxPasswordLength} characters.", "password");
    }

    public static void ValidateFilterShape(string? op, string? value, string[]? values, string field)
    {
        if (op is null || !Ops.Contains(op)) throw Bad("Unknown filter operator.", field + ".op");
        switch (op.ToLowerInvariant())
        {
            case "in":
                if (values is not { Length: > 0 }) throw Bad("Pick at least one value.", field + ".values");
                if (values.Length > ApiLimits.MaxInValues) throw Bad($"An 'in' filter can list at most {ApiLimits.MaxInValues} values.", field + ".values");
                break;
            case "between":
                if (values is not { Length: 2 } || values.Any(string.IsNullOrWhiteSpace)) throw Bad("A range filter needs both From and To.", field + ".values");
                break;
            default:
                if (value is null) throw Bad("A filter value is required.", field + ".value");
                break;
        }
        if (values?.Any(v => v is null) == true) throw Bad("A filter value is required.", field + ".values");
        if ((value?.Length ?? 0) > ApiLimits.MaxFilterValueLength || values?.Any(v => v.Length > ApiLimits.MaxFilterValueLength) == true)
            throw Bad($"A filter value must be at most {ApiLimits.MaxFilterValueLength} characters.", field);
    }

    private static void ValidateRange(int? v, int max, string label, string field)
    { if (v is { } n && (n < 1 || n > max)) throw Bad($"{label} must be between 1 and {max}.", field); }
    private static void NoNulls<T>(T?[]? items, string field) where T : class
    { for (var i = 0; i < (items?.Length ?? 0); i++) if (items![i] is null) throw Bad($"'{field}[{i}]' is required.", $"{field}[{i}]"); }

    public static void ValidateQuery(QueryRequest r)
    {
        if (r.From is null) throw Bad("'from' is required.", "from");
        NoNulls(r.Joins, "joins"); NoNulls(r.RowDimensions, "rowDimensions"); NoNulls(r.ColumnDimensions, "columnDimensions"); NoNulls(r.Measures, "measures");
        var dims = (r.RowDimensions?.Length ?? 0) + (r.ColumnDimensions?.Length ?? 0);
        if (dims > ApiLimits.MaxDimensions) throw Bad($"A view can group by at most {ApiLimits.MaxDimensions} fields.", "rowDimensions");
        var measures = r.Measures?.Length ?? 0;
        if (measures > ApiLimits.MaxMeasures) throw Bad($"A view can show at most {ApiLimits.MaxMeasures} measures.", "measures");
        if ((r.Joins?.Length ?? 0) > ApiLimits.MaxJoins) throw Bad($"A view can join at most {ApiLimits.MaxJoins} tables.", "joins");
        var filters = r.Filters ?? [];
        if (filters.Length > ApiLimits.MaxFilters) throw Bad($"A view can have at most {ApiLimits.MaxFilters} filters.", "filters");
        for (var i = 0; i < filters.Length; i++)
        {
            if (filters[i] is not { } f) throw Bad($"'filters[{i}]' is required.", $"filters[{i}]");
            ValidateFilterShape(f.Op, f.Value, f.Values, $"filters[{i}]");
        }
        ValidateRange(r.Limit, ApiLimits.MaxRowLimit, "Limit", "limit");
        if (r.Sort is { } s && !ClickHouseGateway.IsValidSortAlias(s.Column, dims, Math.Max(1, measures)))
            throw Bad("Unknown sort column.", "sort.column");
    }
    public static void ValidateHistogram(HistogramRequest r) { ValidateRange(r.Buckets, ApiLimits.MaxBuckets, "Bins", "buckets"); ValidateStatFilters(r.Filters); }
    public static void ValidateBoxPlot(BoxPlotRequest r) { ValidateRange(r.Limit, ApiLimits.MaxRowLimit, "Limit", "limit"); ValidateStatFilters(r.Filters); }
    public static void ValidateDistinctLimit(int? limit) => ValidateRange(limit, ApiLimits.MaxDistinct, "Limit", "limit");
    private static void ValidateStatFilters(AggregateFilter[]? filters) // Task 3 changes the type to StatFilter[] and passes f.Values
    {
        if ((filters?.Length ?? 0) > ApiLimits.MaxFilters) throw Bad($"A view can have at most {ApiLimits.MaxFilters} filters.", "filters");
        for (var i = 0; i < (filters?.Length ?? 0); i++)
        {
            if (filters![i] is not { } f) throw Bad($"'filters[{i}]' is required.", $"filters[{i}]");
            ValidateFilterShape(f.Op, f.Value, null, $"filters[{i}]");
        }
    }
}
```

**Wire it.** In each action, call the rule first inside the `RunAsync` lambda — `RequestRules.ValidateQuery(request);`
(Query, ExportCsv), `ValidateHistogram`, `ValidateBoxPlot`, `ValidateDistinctLimit(limit)` (Schema `Distinct`).
`ConnectionController.Connect` starts with
`try { RequestRules.ValidateConnect(req.Host, req.Port, req.User, req.Password); } catch (RequestValidationException ex) { return Invalid(ex); }`
then uses `req.Host!.Trim()`, `req.Port!.Value`, `req.User!.Trim()` (delete the old required/port checks
and the 8443/8123 default). In the gateway: make `IsValidSortAlias` `internal static`; drop the `&& i < 8`
loop caps; replace `MaxInValues` with `ApiLimits.MaxInValues`; keep `ProbeLimit`/`ClampBuckets`/`ClampDistinct`
(defence in depth) but read their maxima from `ApiLimits`.

## Task 3: Typed filter values, honest result values, stat-chart filters

**Files:** Modify `ClickHouse/RequestValidation.cs` (add `FilterValues`), `ClickHouse/ClickHouseGateway.cs`,
`ClickHouse/QueryModels.cs`, `ClickHouse/StatisticalModels.cs`, `ClickHouse/CsvUtil.cs`. Test: create
`tests/DashboardBuilder.Tests/TypedFilterTests.cs`; update `FilterTests.cs`, `StatisticalTests.cs`, and any
test that builds `QueryResultRow` with `new double[]` (use `new object?[]`).

**Interfaces:**
- Produces: `FilterValues.Coerce(string category, string column, string raw, string field) : (string Type, object Value)`;
  `FilterValues.Compare(string category, object a, object b) : int`;
  `ClickHouseGateway.BuildCondition(string? op, string paramBase, string expr, string category, string column, string field, string? value, IReadOnlyList<string>? values, List<(string Name, string Type, object Value)> parameters)`;
  `ClickHouseGateway.ToResultValue(object? raw, bool numeric) : object?`;
  `StatFilter(string Column, string Op, string? Value, string[]? Values = null)` (replaces `AggregateFilter` in `HistogramRequest`/`BoxPlotRequest`);
  `QueryResultRow(IReadOnlyList<string?> Keys, IReadOnlyList<object?> Values)` — values are `double`, display `string`, or `null`.

- [ ] **Step 1: Write the failing tests** (`TypedFilterTests.cs`):

```csharp
using DashboardBuilder.ClickHouse; using Xunit;
namespace DashboardBuilder.Tests;
public class TypedFilterTests
{
    private static (string, object) C(string cat, string raw) => FilterValues.Coerce(cat, "amount", raw, "filters[0]");
    [Theory] [InlineData("12.5", 12.5)] [InlineData(" -3 ", -3.0)] [InlineData("1e3", 1000.0)] [InlineData(".5", 0.5)]
    public void Plain_numbers_bind_as_float(string raw, double expected) => Assert.Equal(("Float64", (object)expected), C(ClickHouseType.Numeric, raw));
    [Theory] [InlineData("1,5")] [InlineData("1,000")] [InlineData("1 000")] [InlineData("0x10")] [InlineData("abc")] [InlineData("NaN")] [InlineData("Infinity")] [InlineData("")]
    public void Anything_else_on_a_number_column_is_rejected_naming_the_column(string raw)
        => Assert.Contains("amount", Assert.Throws<RequestValidationException>(() => C(ClickHouseType.Numeric, raw)).Message);
    [Theory] [InlineData("2024-01-31", "2024-01-31")] [InlineData("2024-01-31T10:20", "2024-01-31 10:20:00")] [InlineData("2024-01-31 10:20:30", "2024-01-31 10:20:30")]
    public void Iso_dates_normalise(string raw, string bound) => Assert.Equal(("String", (object)bound), C(ClickHouseType.Temporal, raw));
    [Theory] [InlineData("31/01/2024")] [InlineData("2024-13-01")] [InlineData("yesterday")]
    public void Other_dates_are_rejected(string raw) => Assert.Throws<RequestValidationException>(() => C(ClickHouseType.Temporal, raw));
    [Fact] public void Booleans_accept_true_false_1_0() => Assert.Equal(("UInt8", (object)(byte)1), C(ClickHouseType.Boolean, "TRUE"));
    [Fact] public void Yes_is_not_a_boolean() => Assert.Throws<RequestValidationException>(() => C(ClickHouseType.Boolean, "yes"));
    [Fact] public void Compound_columns_cannot_be_filtered() => Assert.Throws<RequestValidationException>(() => C(ClickHouseType.Compound, "x"));
    [Fact] public void An_inverted_numeric_range_is_rejected()
        => Assert.Throws<RequestValidationException>(() => ClickHouseGateway.BuildCondition("between", "p0", "c", ClickHouseType.Numeric, "c", "filters[0]", null, ["9", "1"], []));
    [Fact] public void A_numeric_in_list_binds_a_float_array()
    {
        var p = new List<(string, string, object)>();
        Assert.Equal("c IN {p0:Array(Float64)}", ClickHouseGateway.BuildCondition("in", "p0", "c", ClickHouseType.Numeric, "c", "f", null, ["1", "2"], p));
        Assert.Equal("Array(Float64)", p[0].Item2);
    }
    [Fact] public void Not_a_number_results_become_null() => Assert.Null(ClickHouseGateway.ToResultValue(double.NaN, true));
    [Fact] public void Infinite_results_become_null() => Assert.Null(ClickHouseGateway.ToResultValue(double.PositiveInfinity, true));
    [Fact] public void Integers_become_doubles() => Assert.Equal(5.0, ClickHouseGateway.ToResultValue(5L, true));
    [Fact] public void Date_min_max_read_as_iso_text() => Assert.Equal("2024-01-02", ClickHouseGateway.ToResultValue(new DateTime(2024, 1, 2), false));
    [Fact] public void Csv_writes_null_as_empty_and_text_as_is()
        => Assert.Contains("a,,2024-01-02", CsvUtil.FromQueryResult(new QueryResult(["k"], [], ["min x", "max d"], [new QueryResultRow(["a"], [null, "2024-01-02"])])));
}
```

- [ ] **Step 2: Run** `dotnet test --filter TypedFilterTests` — expected FAIL (missing members).
- [ ] **Step 3: Implement** — see [plan-server-c.md § Task 3 implementation](plan-server-c.md#task-3-implementation).
- [ ] **Step 4: Run** `dotnet test` — expected PASS after updating `FilterTests`/`StatisticalTests` to the new
  signatures (the old "empty `in` / half `between` is a no-op" tests now assert `RequestValidationException`).
- [ ] **Step 5: Checkpoint.**
