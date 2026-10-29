// QUERY NAME: dim_product
// Source: data\curated\dim_product.csv (1,862 rows)
// Source columns: product_key, Product ID, Product Name, Category, Sub-Category
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\curated\dim_product.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                 {"product_key", Int64.Type}, {"Product ID", type text}, {"Product Name", type text},
                 {"Category", type text}, {"Sub-Category", type text}}, "en-US"),
    Renamed  = Table.RenameColumns(Typed, {
                 {"Product ID", "ProductID"}, {"Product Name", "ProductName"}, {"Sub-Category", "SubCategory"}}, MissingField.Ignore)
in
    Renamed
