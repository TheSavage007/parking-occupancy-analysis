# Data Dictionary

`parking_occupancy.csv` has one row per reading (4,138 rows, 9 lots).

| Column | Type | Description |
|---|---|---|
| lot_code | string | Lot identifier, Lot01 to Lot09 |
| lot_capacity | integer | Rated number of spaces in the lot |
| lot_occupancy | integer | Vehicles counted in the lot at the reading |
| timestamp | datetime | Reading time, to the minute (YYYY-MM-DD HH:MM) |
| day | string | Day of week of the reading |
| occupancy_rate | float | lot_occupancy divided by lot_capacity, as a percent. Can exceed 100 when a lot is over its rated capacity |
