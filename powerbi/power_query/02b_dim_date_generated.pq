// QUERY NAME: dim_date   (FALLBACK ONLY - use instead of 02_dim_date.pq)
// Generates the calendar in M so no CSV is needed. Output columns match 02_dim_date.pq.
let
    StartDate = #date(2015, 1, 1),
    EndDate   = #date(2019, 12, 31),
    Dates     = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    T         = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}, null, ExtraValues.Error),
    TDate     = Table.TransformColumnTypes(T, {{"Date", type date}}),
    Key       = Table.AddColumn(TDate, "date_key", each Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]), Int64.Type),
    Year      = Table.AddColumn(Key, "Year", each Date.Year([Date]), Int64.Type),
    Quarter   = Table.AddColumn(Year, "Quarter", each Date.QuarterOfYear([Date]), Int64.Type),
    MonthNum  = Table.AddColumn(Quarter, "MonthNumber", each Date.Month([Date]), Int64.Type),
    MonthName = Table.AddColumn(MonthNum, "MonthName", each Date.MonthName([Date], "en-US"), type text),
    YearMonth = Table.AddColumn(MonthName, "YearMonth", each Date.ToText([Date], [Format = "yyyy-MM", Culture = "en-US"]), type text),
    Week      = Table.AddColumn(YearMonth, "WeekOfYear", each Date.WeekOfYear([Date], Day.Monday), Int64.Type),
    Day       = Table.AddColumn(Week, "Day", each Date.Day([Date]), Int64.Type),
    DowName   = Table.AddColumn(Day, "DayOfWeek", each Date.DayOfWeekName([Date], "en-US"), type text),
    Weekend   = Table.AddColumn(DowName, "IsWeekend", each if Date.DayOfWeek([Date], Day.Monday) >= 5 then 1 else 0, Int64.Type),
    MonthStart= Table.AddColumn(Weekend, "MonthStart", each Date.StartOfMonth([Date]), type date),
    QLabel    = Table.AddColumn(MonthStart, "QuarterLabel", each "Q" & Text.From([Quarter]), type text),
    YQ        = Table.AddColumn(QLabel, "YearQuarter", each Text.From([Year]) & " Q" & Text.From([Quarter]), type text),
    MShort    = Table.AddColumn(YQ, "MonthShort", each Text.Start([MonthName], 3), type text),
    DowNum    = Table.AddColumn(MShort, "DayOfWeekNumber", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    YMSort    = Table.AddColumn(DowNum, "YearMonthSort", each [Year] * 100 + [MonthNumber], Int64.Type),
    Lbl       = Table.AddColumn(YMSort, "MonthYearLabel", each [MonthShort] & " " & Text.From([Year]), type text),
    Ordered   = Table.ReorderColumns(Lbl, {"date_key", "Date"})
in
    Ordered
