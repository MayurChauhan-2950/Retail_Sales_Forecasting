// QUERY NAME: monthly_actual
// Source: data\forecast\monthly_sales_actual.csv  (48 months, Jan 2015 - Dec 2018)
// Source columns: month (first day of month), actual_sales
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\forecast\monthly_sales_actual.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {{"month", type date}, {"actual_sales", type number}}, "en-US")
in
    Typed
