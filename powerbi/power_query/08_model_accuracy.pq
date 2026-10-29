// QUERY NAME: model_accuracy
// Built from the REAL numbers in reports\model_accuracy.md (identical to data\forecast\model_accuracy.csv):
// 12-month hold-out, Jan-Dec 2018, models trained on Jan 2015 - Dec 2017.
// Typed in so the page still works if the CSV is moved. Source "MAPE_%" is named MAPE_pct here.
let
    Source = #table(
        type table [model = text, MAE = number, RMSE = number, MAPE_pct = number, rank_rmse = Int64.Type],
        {
            {"Holt-Winters (additive)", 10896.6345, 14117.724,  18.5068, 1},
            {"SARIMA(1,1,1)(0,1,1,12)", 15104.5647, 17570.5088, 33.9769, 2},
            {"ARIMA(1,1,1)",            23450.6273, 27208.4475, 54.1058, 3}
        })
in
    Source
