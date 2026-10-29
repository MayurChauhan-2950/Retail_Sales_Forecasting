// QUERY NAME: dim_model
// Small lookup used by the "Model" slicer on the Forecast Arena page. It is the 1-side that filters
// both model_accuracy and fact_forecast. Depends on the model_accuracy query (08).
let
    Models   = Table.SelectColumns(model_accuracy, {"model", "rank_rmse"}),
    Renamed  = Table.RenameColumns(Models, {{"rank_rmse", "model_sort"}}),
    AddShort = Table.AddColumn(Renamed, "model_short", each
                 if Text.StartsWith([model], "Holt") then "Holt-Winters"
                 else if Text.StartsWith([model], "SARIMA") then "SARIMA"
                 else "ARIMA", type text),
    AddFam   = Table.AddColumn(AddShort, "model_family", each
                 if Text.StartsWith([model], "Holt") then "Exponential smoothing" else "Box-Jenkins", type text),
    Sorted   = Table.Sort(AddFam, {{"model_sort", Order.Ascending}})
in
    Sorted
