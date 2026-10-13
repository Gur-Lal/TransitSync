---
name: "gtfs-data"
description: "Query or process TransitSync GTFS data (REM and STM metro) in the Supabase gtfs schema or local feed files, including headways, dwells, platform IDs and service calendars."
---

# TransitSync GTFS data

Use this for the GTFS extraction task, loading new feed versions, or any question about schedules. Full background is on the "Reading GTFS Data" wiki page.

## Where the data is

- Supabase Postgres, schema `gtfs`: tables `feeds, routes, stops, calendar, calendar_dates, trips, stop_times, frequencies, shapes`
- Every row has a `feed_id` such as `rem_20260520` or `stm_20260805110000_26S`. Always filter by `feed_id`. Never mix versions in one result
- Connection string is `SUPABASE_DB_URL` in `.env`. Never print or log it, and do not read `.env` directly
- Original zips are in the Storage bucket `gtfs-raw`
- Only rail routes are loaded: REM (`route_type` 0) and STM metro (`route_type` 1; route IDs 1 green, 2 orange, 4 yellow, 5 blue)
- New feed versions are loaded with `scripts/load_gtfs.py <folder> --agency REM|STM`, dry run first

## Interchange platforms (REM)

| Station | Toward Brossard (direction 1) | Away from Brossard (direction 0) |
|---|---|---|
| Gare Centrale | STA_ZCD_BT_QUAI_02_GCT | STA_ZCD_BT_QUAI_01_GCT |
| McGill | STA_ZCD_BT_QUAI_02_MCG | STA_ZCD_BT_QUAI_01_MCG |
| Edouard-Montpetit | STA_ZCD_BT_QUAI_02_EDM | STA_ZCD_BT_QUAI_01_EDM |

Look up STM metro platform IDs from `gtfs.stops` by name (Bonaventure, McGill, Edouard-Montpetit) and record them in config. Do not guess them.

## Rules

- Use `arrival_s` / `departure_s` (seconds after midnight of the service day). Text times can exceed 24:00:00
- Pick service for a date with the calendar, then remove `calendar_dates` rows with `exception_type` 2 and add rows with `exception_type` 1. Holidays use Sunday service
- `stop_times` points to platforms (`location_type` 0), never station rows
- Headway = difference between consecutive departures from the same platform, in the same direction and service
- Dwell = `departure_s - arrival_s` at a platform
- Time bands: early (<6h), AM (6-9h), midday (9-15h), PM (15-18h), evening (18-21h), late (21h+). Report medians per band, plus min and max so outliers are visible
- Read files with every column as text (`dtype=str`) and strip whitespace. Some REM values have leading spaces
- Files are UTF-8 with French characters

## Output of extraction

The simulator never reads GTFS at runtime. Extraction writes one committed file in `config/` containing:
- feed IDs and validity dates it was built from
- platform IDs per interchange, network and direction
- headway per direction, time band and day type (weekday, Saturday, Sunday)
- REM scheduled dwell per station and direction

## Checks before committing extracted values

- REM weekday headway is 210 s in the AM and PM peaks and 450 s midday (feed rem_20260520)
- REM dwell at the three interchanges is between 28 and 45 s
- No time band is empty for a direction that has service
- The STM feed has an end date; flag it if it expires within 30 days

## Licence

REM data is CC BY 4.0. Published output needs: "Schedule data from the Réseau express métropolitain (REM), https://rem.info, used under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Data has been processed and modified for this project."