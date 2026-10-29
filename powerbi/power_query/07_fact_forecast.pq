// QUERY NAME: fact_forecast
// Combines (a) the hold-out predictions of the 3 models (2018, with the actual value) and
//          (b) the future forecast for 2019 (best model refit on all 48 months, with intervals)
// into ONE long table: month, model, kind, actual, forecast, lower_80, upper_80, lower_95, upper_95, abs_error
// Sources: data\forecast\holdout_predictions.csv  (month, actual, <one column per model>)
//          data\forecast\sales_forecast.csv       (month, forecast, lower_95, upper_95, model [, level, series, ...])
// Extra columns are ignored and missing optional columns (lower_80, upper_80 ...) become null.
let
    Folder = Text.TrimEnd(DataFolder, "\") & "\forecast\",
    Load = (name as text) as table =>
        Table.PromoteHeaders(Csv.Document(File.Contents(Folder & name),
            [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]), [PromoteAllScalars = true]),

    // ---- (a) hold-out: wide -> long (one row per month per model) ----
    Hold      = Load("holdout_predictions.csv"),
    HoldLong  = Table.UnpivotOtherColumns(Hold, {"month", "actual"}, "model", "forecast"),
    HoldKind  = Table.AddColumn(HoldLong, "kind", each "Holdout", type text),

    // ---- (b) future forecast ----
    Fut       = Load("sales_forecast.csv"),
    FutKind   = Table.AddColumn(Fut, "kind", each "Future", type text),

    // ---- union (Table.Combine fills columns that exist on only one side with null) ----
    Combined  = Table.Combine({HoldKind, FutKind}),
    Wanted    = {"month", "model", "kind", "actual", "forecast", "lower_80", "upper_80", "lower_95", "upper_95"},
    Missing   = List.Select(Wanted, each not List.Contains(Table.ColumnNames(Combined), _)),
    AddMissing= List.Accumulate(Missing, Combined, (t, c) => Table.AddColumn(t, c, each null)),
    Selected  = Table.SelectColumns(AddMissing, Wanted),
    Typed     = Table.TransformColumnTypes(Selected, {
                  {"month", type date}, {"model", type text}, {"kind", type text},
                  {"actual", type number}, {"forecast", type number},
                  {"lower_80", type number}, {"upper_80", type number},
                  {"lower_95", type number}, {"upper_95", type number}}, "en-US"),
    // absolute error only where an actual exists (hold-out rows)
    AddErr    = Table.AddColumn(Typed, "abs_error",
                  each if [actual] = null or [forecast] = null then null else Number.Abs([forecast] - [actual]), type number)
in
    AddErr
