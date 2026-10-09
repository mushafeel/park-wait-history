# park-wait-history

Automatically records Tokyo Disneyland and Tokyo DisneySea standby wait times every 5 minutes
(08:00–23:00 Japan time) using GitHub Actions, building a day-by-day history for the RideOrder planner.

- Data: `data/<park>/<YYYY-MM>/<YYYY-MM-DD>.csv` — one row per 5 minutes, one column per attraction
  (number = posted wait in minutes, `D` = down, `C` = closed, `R` = refurbishment).
- Ride names: `data/<park>/rides.json`.
- Source: live data from [ThemeParks.wiki](https://themeparks.wiki).

Unofficial; not affiliated with The Walt Disney Company or Oriental Land Co.
