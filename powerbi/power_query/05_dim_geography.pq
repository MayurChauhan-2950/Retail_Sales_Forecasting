// QUERY NAME: dim_geography
// Source: data\curated\dim_geography.csv (632 rows)
// Source columns: geography_key, Country, Region, State, City, Postal Code
// Postal Code is kept as TEXT (never summed; a blank postal code does not cause an error).
// After loading, set Data category (Column tools tab): State = State or Province, City = City,
// Country = Country/Region, PostalCode = Postal Code, so the map visual geocodes correctly.
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\curated\dim_geography.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                 {"geography_key", Int64.Type}, {"Country", type text}, {"Region", type text},
                 {"State", type text}, {"City", type text}, {"Postal Code", type text}}, "en-US"),
    Renamed  = Table.RenameColumns(Typed, {{"Postal Code", "PostalCode"}}, MissingField.Ignore),
    // "City, State, Country" label for unambiguous map locations (many city names repeat across states)
    AddLoc   = Table.AddColumn(Renamed, "Location", each [City] & ", " & [State] & ", " & [Country], type text)
in
    AddLoc
