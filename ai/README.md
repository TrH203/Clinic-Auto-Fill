# Auto Schedule Generator

This folder contains a small script to generate CSV schedules for the app.

## Configure time slots
Edit `config.py`:

```
AUTO_SCHEDULE_TIME_SLOTS_KIND = "CD"  # "CD" or "BD_TH"
AUTO_SCHEDULE_TIME_SLOTS = [
    "07:00",
    "07:30",
    "08:00",
]
```

- `CD` means the list is **Ngay CD** times; the script will add 5 minutes to get **Ngay BD TH**.
- `BD_TH` means the list is already **Ngay BD TH** times and will be used as-is.

## Usage
Run from repo root:

```
python ai/auto_schedule.py \
  --patient-id 2601016716 \
  --procedures "điện-xoa-kéo-giác" \
  --start-date 29-01-2026 \
  --end-date 07-02-2026 \
  --output ai/generated_schedule.csv
```

Optional flags:

- `--seed 42` for reproducible randomness (default is 42)
- `--use-all-slots` to generate an entry for every time slot each day
- `--time-slots "07:00,07:30,08:00"` to override config
- `--time-slots-file path/to/slots.txt` (one time per line)
- `--slots-kind CD|BD_TH` to override config
- `--slots-by-date-file path/to/slots.json` for per-day time slots (Ngay CD)
- `--slots-by-date-json '{"19-12-25":["7:39","13:36"]}'` for inline per-day slots

### Slots-by-date example
Create a JSON file like this (Ngay CD per day):

```
{
  "19-12-25": ["7:39"],
  "20-12-25": ["7:05", "8:10"],
  "21-12-25": ["7:44"]
}
```

Run:

```
python ai/auto_schedule.py \
  --patient-id 2505012345 \
  --procedures "xoa-điện-kéo-giác" \
  --slots-by-date-file ai/slots_by_date.json \
  --output sample.csv
```

When multiple slots are provided for a day, the script will randomly pick **one** slot
(seeded for reproducibility).

### Procedure-based slots config
You can also provide a JSON where the top-level key is the **first procedure** name.
Example (Ngay CD):

```
{
  "điện": {
    "0": ["7:04", "7:41", "8:18"],
    "1": ["7:05", "7:42", "8:19"]
  },
  "xoa": {
    "0": ["7:03", "7:40", "8:17"],
    "1": ["7:05", "7:42", "8:19"]
  }
}
```

Rules:
- The script picks the list based on the **first procedure** in `--procedures`.
- If there are grouped keys like `"0"`/`"1"`, it alternates by day index
  (day 1 -> `"0"`, day 2 -> `"1"`, then repeat).
- One slot is randomly chosen for each day (seeded).

## Notes
- Staff assignment is randomized but respects Group 1/Group 2 roles, disabled staff,
  and leave schedule rules from the database.
- By default, the script generates **one appointment per day** in the date range.
