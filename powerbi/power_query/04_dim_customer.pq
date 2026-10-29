// QUERY NAME: dim_customer
// Source: data\curated\dim_customer.csv (793 rows)
// Source columns: customer_key, Customer ID, Customer Name, Segment
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\curated\dim_customer.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                 {"customer_key", Int64.Type}, {"Customer ID", type text},
                 {"Customer Name", type text}, {"Segment", type text}}, "en-US"),
    Renamed  = Table.RenameColumns(Typed, {{"Customer ID", "CustomerID"}, {"Customer Name", "CustomerName"}}, MissingField.Ignore)
in
    Renamed
