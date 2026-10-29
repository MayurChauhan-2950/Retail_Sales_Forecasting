// QUERY NAME: dim_date
// Source: data\curated\dim_date.csv (1,826 rows, 2015-01-01 .. 2019-12-31; covers the 2019 forecast year)
// Source columns: date_key, date, year, quarter, month, month_name, year_month, week_of_year, day, day_of_week, is_weekend
// If you ever get a dim_date without these columns, use 02b_dim_date_generated.pq instead.
let
    Source   = Csv.Document(File.Contents(Text.TrimEnd(DataFolder, "\") & "\curated\dim_date.csv"),
                 [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed    = Table.TransformColumnTypes(Promoted, {
                 {"date_key", Int64.Type}, {"date", type date}, {"year", Int64.Type}, {"quarter", Int64.Type},
                 {"month", Int64.Type}, {"month_name", type text}, {"year_month", type text},
                 {"week_of_year", Int64.Type}, {"day", Int64.Type}, {"day_of_week", type text},
                 {"is_weekend", Int64.Type}}, "en-US"),
    Renamed  = Table.RenameColumns(Typed, {
                 {"date", "Date"}, {"year", "Year"}, {"quarter", "Quarter"}, {"month", "MonthNumber"},
                 {"month_name", "MonthName"}, {"year_month", "YearMonth"}, {"week_of_year", "WeekOfYear"},
                 {"day", "Day"}, {"day_of_week", "DayOfWeek"}, {"is_weekend", "IsWeekend"}}, MissingField.Ignore),
    AddMonthStart = Table.AddColumn(Renamed, "MonthStart", each Date.StartOfMonth([Date]), type date),
    AddQLabel     = Table.AddColumn(AddMonthStart, "QuarterLabel", each "Q" & Text.From([Quarter]), type text),
    AddYQ         = Table.AddColumn(AddQLabel, "YearQuarter", each Text.From([Year]) & " Q" & Text.From([Quarter]), type text),
    AddMonthShort = Table.AddColumn(AddYQ, "MonthShort", each Text.Start([MonthName], 3), type text),
    AddDowNum     = Table.AddColumn(AddMonthShort, "DayOfWeekNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    AddYMSort     = Table.AddColumn(AddDowNum, "YearMonthSort", each [Year] * 100 + [MonthNumber], Int64.Type),
    AddLabel      = Table.AddColumn(AddYMSort, "MonthYearLabel", each [MonthShort] & " " & Text.From([Year]), type text)
in
    AddLabel
