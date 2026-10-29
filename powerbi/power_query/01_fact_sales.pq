// QUERY NAME: fact_sales
// Source: data\curated\fact_sales.csv (9,994 rows)
// Source columns: row_id, order_id, order_date_key, ship_date_key, customer_key, product_key,
//                 geography_key, ship_mode, sales, quantity, discount, profit
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\curated\fact_sales.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                 {"row_id", Int64.Type}, {"order_id", type text},
                 {"order_date_key", Int64.Type}, {"ship_date_key", Int64.Type},
                 {"customer_key", Int64.Type}, {"product_key", Int64.Type}, {"geography_key", Int64.Type},
                 {"ship_mode", type text},
                 {"sales", type number}, {"quantity", Int64.Type},
                 {"discount", type number}, {"profit", type number}}, "en-US"),
    // yyyymmdd integer -> real date (used for the RFM table and shipping days; relationships use the keys)
    KeyToDate = (k as number) as date =>
                 #date(Number.IntegerDivide(k, 10000), Number.Mod(Number.IntegerDivide(k, 100), 100), Number.Mod(k, 100)),
    AddOrderDate = Table.AddColumn(Typed, "order_date", each KeyToDate([order_date_key]), type date),
    AddShipDate  = Table.AddColumn(AddOrderDate, "ship_date", each KeyToDate([ship_date_key]), type date),
    AddDays      = Table.AddColumn(AddShipDate, "days_to_ship", each Duration.Days([ship_date] - [order_date]), Int64.Type),
    // discount band (labels start with a number so they sort correctly; sort column below)
    AddBand = Table.AddColumn(AddDays, "discount_band", each
                 if [discount] = 0 then "0 No discount"
                 else if [discount] <= 0.2 then "1 Low (up to 20%)"
                 else if [discount] <= 0.4 then "2 Medium (20-40%)"
                 else "3 High (over 40%)", type text),
    AddBandSort = Table.AddColumn(AddBand, "discount_band_sort", each
                 if [discount] = 0 then 0 else if [discount] <= 0.2 then 1 else if [discount] <= 0.4 then 2 else 3, Int64.Type),
    // loss-making order line flag (lets you count loss lines)
    AddLoss = Table.AddColumn(AddBandSort, "is_loss_line", each if [profit] < 0 then 1 else 0, Int64.Type)
in
    AddLoss
