# P34 plan — Server A: error contract & limits (Tasks 1–2)

Part of the [P34 plan](plan-overview.md); read its Global Constraints first. Paths are relative to the app
root `src/DashboardBuilder/` unless they start with `tests/`.

### Task 1: One error contract

**Files:**
- Create: `ClickHouse/RequestValidation.cs` (exception + `ApiLimits` only in this task), `Features/ApiErrors.cs`
- Modify: `Features/ApiControllerBase.cs`, `Program.cs`, every `Features/*/…Controller.cs` action body
- Test: create `tests/DashboardBuilder.Tests/ErrorContractTests.cs`; update `QueryGuardTests.cs` (3 `DescribeFailure` calls)

**Interfaces:**
- Produces: `RequestValidationException(string message, string? field = null)` with `.Field`;
  `ApiLimits.*` constants; `ApiError(string Error, string? Field = null)` record;
  `ApiErrors.FromModelState(ModelStateDictionary) : IActionResult`; `ApiErrors.UseApiBodyLimit(this WebApplication)`;
  `ApiErrors.WriteUnhandledAsync(HttpContext) : Task`; `ApiControllerBase.RunAsync(Func<ClickHouseConnectionInfo, Task<IResult>> work, int unknownIdentifierStatus = 400)`;
  `ApiControllerBase.Invalid(RequestValidationException) : IResult`; `ApiControllerBase.DescribeFailure(Exception ex, string traceId) : (int Status, string Message)`.

- [ ] **Step 1: Write the failing tests** — `ErrorContractTests.cs`:

```csharp
using System.Net; using System.Text; using System.Text.Json;
using ClickHouse.Client; using DashboardBuilder.ClickHouse; using DashboardBuilder.Features;
using Microsoft.AspNetCore.Diagnostics; using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc.Testing; using Microsoft.Extensions.DependencyInjection; using Xunit;
namespace DashboardBuilder.Tests;
public class ErrorContractTests(WebApplicationFactory<Program> factory) : IClassFixture<WebApplicationFactory<Program>>
{
    private static StringContent Json(string s) => new(s, Encoding.UTF8, "application/json");
    private static async Task<JsonElement> Body(HttpResponseMessage r) => JsonDocument.Parse(await r.Content.ReadAsStringAsync()).RootElement;

    [Fact] public async Task Malformed_json_is_a_400_with_one_error_and_no_type_names()
    {
        var r = await factory.CreateClient().PostAsync("/api/query", Json("{ not json"));
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
        var text = await r.Content.ReadAsStringAsync();
        Assert.Contains("\"error\"", text); Assert.DoesNotContain("errors", text); Assert.DoesNotContain("System.", text);
    }
    [Fact] public async Task A_wrongly_typed_field_names_the_field()
    {
        var r = await factory.CreateClient().PostAsync("/api/connection", Json("{\"host\":\"h\",\"port\":\"abc\",\"user\":\"u\"}"));
        Assert.Equal(HttpStatusCode.BadRequest, r.StatusCode);
        Assert.Equal("port", (await Body(r)).GetProperty("field").GetString());
    }
    [Fact] public async Task An_oversized_body_is_a_413()
    {
        var big = "{\"host\":\"" + new string('a', ApiLimits.MaxBodyBytes) + "\"}";
        var r = await factory.CreateClient().PostAsync("/api/connection", Json(big));
        Assert.Equal(HttpStatusCode.RequestEntityTooLarge, r.StatusCode);
        Assert.Equal("Request too large.", (await Body(r)).GetProperty("error").GetString());
    }
    [Fact] public void Our_own_bug_is_a_500_with_a_reference()
        => Assert.Equal((500, "Unexpected error (ref t-1)."), ApiControllerBase.DescribeFailure(new InvalidOperationException(), "t-1"));
    [Fact] public void A_network_failure_is_a_502()
        => Assert.Equal(502, ApiControllerBase.DescribeFailure(new HttpRequestException(), "t").Status);
    [Fact] public void A_clickhouse_rejection_is_a_502()
        => Assert.Equal(502, ApiControllerBase.DescribeFailure(new ClickHouseServerException("x", "SELECT", 62), "t").Status);
    [Fact] public async Task The_unhandled_writer_never_echoes_the_exception_message()
    {
        var ctx = new DefaultHttpContext { TraceIdentifier = "t-9" };
        ctx.Response.Body = new MemoryStream();
        ctx.RequestServices = new ServiceCollection().AddLogging().BuildServiceProvider();
        ctx.Features.Set<IExceptionHandlerFeature>(new ExceptionHandlerFeature { Error = new InvalidOperationException("pw=secret") });
        await ApiErrors.WriteUnhandledAsync(ctx);
        ctx.Response.Body.Position = 0;
        var text = await new StreamReader(ctx.Response.Body).ReadToEndAsync();
        Assert.Equal(500, ctx.Response.StatusCode); Assert.Contains("t-9", text); Assert.DoesNotContain("secret", text);
    }
}
```

- [ ] **Step 2: Run** `dotnet test --filter ErrorContractTests` — expected FAIL (compile errors: `ApiLimits`, `ApiErrors`, 2-arg `DescribeFailure` missing).

- [ ] **Step 3: Implement.** `ClickHouse/RequestValidation.cs`:

```csharp
namespace DashboardBuilder.ClickHouse;
/// <summary>Client input that breaks a rule. Always a 400 with this message and the offending field path.</summary>
public sealed class RequestValidationException(string message, string? field = null) : Exception(message)
{ public string? Field { get; } = field; }
/// <summary>Every input bound — mirrored in Features/Core/validate.js LIMITS. Reject beyond these, never clamp.</summary>
public static class ApiLimits
{
    public const int MaxBodyBytes = 256 * 1024;
    public const int MaxHostLength = 253, MaxUserLength = 64, MaxPasswordLength = 256;
    public const int MaxDimensions = 12, MaxMeasures = 10, MaxJoins = 10, MaxFilters = 8;
    public const int MaxInValues = 500, MaxFilterValueLength = 1000;
    public const int MaxRowLimit = 500, MaxBuckets = 100, MaxDistinct = 1000;
}
```

`Features/ApiErrors.cs`:

```csharp
using System.Text.Json.Serialization;
using DashboardBuilder.ClickHouse;
using Microsoft.AspNetCore.Diagnostics; using Microsoft.AspNetCore.Http.Features;
using Microsoft.AspNetCore.Mvc; using Microsoft.AspNetCore.Mvc.ModelBinding;
namespace DashboardBuilder.Features;
/// <summary>The one error body every API failure returns.</summary>
public sealed record ApiError(string Error, [property: JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)] string? Field = null);
public static class ApiErrors
{
    /// <summary>Model-binding failures → { error, field }: first error only, no CLR names or parser positions.</summary>
    public static IActionResult FromModelState(ModelStateDictionary state)
    {
        var bad = state.FirstOrDefault(kv => kv.Value is { Errors.Count: > 0 });
        var field = ToFieldPath(bad.Key);
        var required = bad.Value?.Errors.Any(e => e.ErrorMessage.EndsWith("field is required.", StringComparison.Ordinal)) == true;
        var message = field is null ? "Request body is missing or isn't valid JSON."
            : required ? $"'{field}' is required." : $"'{field}' has an invalid value.";
        return new BadRequestObjectResult(new ApiError(message, field));
    }
    // "$.filters[0].Value" → "filters[0].value"; the body parameter itself ("req"/"request"/"$") isn't a field.
    internal static string? ToFieldPath(string? key)
    {
        if (string.IsNullOrEmpty(key) || key == "$") return null;
        var k = key.StartsWith("$.", StringComparison.Ordinal) ? key[2..] : key;
        if (k is "req" or "request") return null;
        return string.Join('.', k.Split('.').Select(s => s.Length == 0 ? s : char.ToLowerInvariant(s[0]) + s[1..]));
    }
    /// <summary>Reject API bodies over <see cref="ApiLimits.MaxBodyBytes"/> with a 413 (declared length up front;
    /// chunked bodies via Kestrel's per-request limit, surfaced by <see cref="WriteUnhandledAsync"/>).</summary>
    public static WebApplication UseApiBodyLimit(this WebApplication app)
    {
        app.Use(async (ctx, next) =>
        {
            if (ctx.Request.Path.StartsWithSegments("/api"))
            {
                if (ctx.Request.ContentLength > ApiLimits.MaxBodyBytes)
                {
                    ctx.Response.StatusCode = StatusCodes.Status413PayloadTooLarge;
                    await ctx.Response.WriteAsJsonAsync(new ApiError("Request too large."));
                    return;
                }
                if (ctx.Features.Get<IHttpMaxRequestBodySizeFeature>() is { IsReadOnly: false } f) f.MaxRequestBodySize = ApiLimits.MaxBodyBytes;
            }
            await next();
        });
        return app;
    }
    /// <summary>Last resort for anything a controller didn't catch. Logs the exception TYPE only (messages can carry credentials).</summary>
    public static async Task WriteUnhandledAsync(HttpContext ctx)
    {
        var ex = ctx.Features.Get<IExceptionHandlerFeature>()?.Error;
        if (ex is BadHttpRequestException bad)
        {
            ctx.Response.StatusCode = bad.StatusCode;
            await ctx.Response.WriteAsJsonAsync(new ApiError(bad.StatusCode == 413 ? "Request too large." : "Bad request."));
            return;
        }
        ctx.RequestServices.GetRequiredService<ILoggerFactory>().CreateLogger("DashboardBuilder.Unhandled")
            .LogError("Unhandled {ErrorType} (ref {TraceId})", ex?.GetType().Name, ctx.TraceIdentifier);
        ctx.Response.StatusCode = StatusCodes.Status500InternalServerError;
        await ctx.Response.WriteAsJsonAsync(new ApiError($"Unexpected error (ref {ctx.TraceIdentifier})."));
    }
}
```

`Program.cs`: change `builder.Services.AddControllersWithViews();` to
`builder.Services.AddControllersWithViews().ConfigureApiBehaviorOptions(o => o.InvalidModelStateResponseFactory = ctx => ApiErrors.FromModelState(ctx.ModelState));`
and, right after the `UsePathBase` block, add
`app.UseExceptionHandler(new ExceptionHandlerOptions { ExceptionHandler = ApiErrors.WriteUnhandledAsync });` and
`app.UseApiBodyLimit();` (add `using DashboardBuilder.Features;`).

`ApiControllerBase.cs` — replace `NotConnected`, `SafeError`, `DescribeFailure`; add `Invalid`, `RunAsync`, `IsUpstreamFailure`:

```csharp
protected static IResult NotConnected() => Results.Json(new ApiError("Not connected to a ClickHouse server."), statusCode: 409);
protected static IResult Invalid(RequestValidationException ex) => Results.Json(new ApiError(ex.Message, ex.Field), statusCode: 400);
/// <summary>The one action wrapper: 409 when not connected, 400 for rule breaks, <paramref name="unknownIdentifierStatus"/>
/// for catalog misses, 502/504 for ClickHouse, 500 for our own bugs. Client aborts are left to the framework.</summary>
protected async Task<IResult> RunAsync(Func<ClickHouseConnectionInfo, Task<IResult>> work, int unknownIdentifierStatus = StatusCodes.Status400BadRequest)
{
    var info = Registry.Current;
    if (info is null) return NotConnected();
    try { return await work(info); }
    catch (RequestValidationException ex) { return Invalid(ex); }
    catch (UnknownIdentifierException ex) { return Results.Json(new ApiError(ex.Message), statusCode: unknownIdentifierStatus); }
    catch (Exception ex) when (!IsClientAbort(ex)) { return SafeError(ex); }
}
protected IResult SafeError(Exception ex)
{
    var trace = HttpContext.TraceIdentifier;
    var (status, message) = DescribeFailure(ex, trace);
    var log = _loggers.CreateLogger(GetType().FullName!);
    if (status == 500) log.LogError("Unexpected {ErrorType} (ref {TraceId})", ex.GetType().Name, trace);
    else log.LogWarning("Query failed: {ErrorType}", ex.GetType().Name);
    return Results.Json(new ApiError(message), statusCode: status);
}
internal static (int Status, string Message) DescribeFailure(Exception ex, string traceId) => ex switch
{
    ClickHouseServerException { ErrorCode: 159 } => TimedOut(ClickHouseGateway.MaxExecutionSeconds),
    _ when ClickHouseGateway.IsHttpTimeout(ex) => TimedOut(ClickHouseGateway.HttpTimeoutSeconds),
    _ when IsUpstreamFailure(ex) => (StatusCodes.Status502BadGateway, "Query failed against ClickHouse."),
    _ => (StatusCodes.Status500InternalServerError, $"Unexpected error (ref {traceId})."),
};
internal static bool IsUpstreamFailure(Exception ex) => ex switch
{
    ClickHouseServerException or HttpRequestException or IOException or System.Security.Authentication.AuthenticationException => true,
    _ => ex.InnerException is { } inner && IsUpstreamFailure(inner),
};
```

Rewrite every API action to one `RunAsync` call — e.g. `QueryController.Query`:

```csharp
[HttpPost("query")]
public Task<IResult> Query([FromBody] QueryRequest request, CancellationToken ct)
    => RunAsync(async info => Results.Ok(await Gateway.QueryAsync(info, request, ct)));
```

`SchemaController` actions pass `StatusCodes.Status404NotFound` as the second argument. Delete the
now-unused `LogCategory` constants. In `QueryGuardTests.cs` pass `"t"` as the new `traceId` argument
to each `DescribeFailure` call; if one asserts 502 for an exception that isn't upstream, change that
exception to `new ClickHouseServerException("x", "SELECT", 62)`.

- [ ] **Step 4: Run** `dotnet test` — expected: all PASS (new + existing).
- [ ] **Step 5: Checkpoint** — both suites green; Task 1 done.

### Task 2: Limits and connection rules — reject, never clamp

**Files:**
- Modify: `ClickHouse/RequestValidation.cs` (add `RequestRules`), `ClickHouse/ClickHouseGateway.cs` (make `IsValidSortAlias` `internal static`; replace `8`/`500`/`MaxInValues` literals with `ApiLimits`), `Features/Connection/ConnectionController.cs`, `Features/Dashboard/QueryController.cs`, `Features/Schema/SchemaController.cs`
- Test: create `tests/DashboardBuilder.Tests/ValidationTests.cs`; update `ConnectionEndpointTests.cs` (every connect body sends `port = 8443`)

**Interfaces:**
- Consumes: `RequestValidationException`, `ApiLimits` (Task 1).
- Produces: `RequestRules.HostError(string?) : string?`; `RequestRules.ValidateConnect(string? host, int? port, string? user, string? password)`;
  `RequestRules.ValidateFilterShape(string? op, string? value, string[]? values, string field)`;
  `RequestRules.ValidateQuery(QueryRequest)`; `ValidateHistogram(HistogramRequest)`; `ValidateBoxPlot(BoxPlotRequest)`;
  `ValidateDistinctLimit(int?)`. Host message constants `HostSchemeMessage`, `HostPortMessage`, `HostPathMessage`, `HostInvalidMessage`.

The test file and the implementation are in [plan-server-b.md § Task 2 code](plan-server-b.md#task-2-code).
Steps: (1) write `ValidationTests.cs` from there; (2) `dotnet test --filter ValidationTests` → FAIL
(`RequestRules` missing); (3) add `RequestRules` and wire the controllers as shown; (4) `dotnet test` → PASS;
(5) checkpoint.
