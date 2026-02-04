#!/usr/bin/env python3
import argparse
import json
import os
import random
import sys
from collections import defaultdict
from datetime import datetime, timedelta

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(REPO_ROOT)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

import config
from handle_data import (
    create_data_from_manual_input,
    export_data_to_csv,
    parse_date_safe,
    validate_all_data,
)
from database import get_disabled_staff, check_staff_available


def normalize_procedures(value):
    if isinstance(value, str):
        if ";" in value:
            parts = value.split(";")
        elif "," in value:
            parts = value.split(",")
        else:
            parts = value.split("-")
    else:
        parts = value

    procs = [str(p).strip().lower() for p in parts if str(p).strip()]
    procs = [p.replace("thuỷ", "thủy") for p in procs]

    if len(procs) != 4:
        raise ValueError(
            "Procedures must contain exactly 4 items (e.g., điện-xoa-kéo-giác)."
        )

    missing = [p for p in procs if p not in config.thu_thuat_dur_mapper]
    if missing:
        raise ValueError(f"Unknown procedures: {', '.join(missing)}")

    return procs


def normalize_time_slots(time_slots):
    slots = []
    for slot in time_slots:
        slot = str(slot).strip()
        if not slot:
            continue
        if ":" not in slot:
            raise ValueError(f"Invalid time slot '{slot}' (expected HH:MM)")
        parts = slot.split(":")
        if len(parts) != 2:
            raise ValueError(f"Invalid time slot '{slot}' (expected HH:MM)")
        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError as exc:
            raise ValueError(f"Invalid time slot '{slot}' (expected HH:MM)") from exc
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time slot '{slot}' (hour/min out of range)")
        slots.append(f"{hour:02d}:{minute:02d}")
    if not slots:
        raise ValueError("No time slots provided. Please configure time slots first.")
    return slots


def parse_time_slots_arg(arg):
    if not arg:
        return []
    cleaned = arg.replace(";", ",")
    parts = [p.strip() for p in cleaned.split(",") if p.strip()]
    return normalize_time_slots(parts)


def read_time_slots_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    return normalize_time_slots(lines)


def normalize_date_key(value):
    return parse_date_safe(str(value)).strftime("%d-%m-%Y")


def read_slots_by_date(payload):
    if not isinstance(payload, dict):
        raise ValueError("Slots-by-date payload must be a dictionary of date -> slots")

    result = {}
    for raw_date, raw_slots in payload.items():
        date_key = normalize_date_key(raw_date)
        if isinstance(raw_slots, str):
            slots = [raw_slots]
        elif isinstance(raw_slots, (list, tuple)):
            slots = list(raw_slots)
        else:
            raise ValueError(f"Slots for date '{raw_date}' must be a list or string")

        result[date_key] = normalize_time_slots(slots)
    return result


def read_slots_by_date_file(path):
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    return read_slots_by_date(payload)


def normalize_proc_key(value):
    return str(value).strip().lower().replace("thuỷ", "thủy")


def is_procedure_payload(payload):
    if not isinstance(payload, dict):
        return False
    proc_keys = {normalize_proc_key(k) for k in config.thu_thuat_dur_mapper.keys()}
    for key in payload.keys():
        if normalize_proc_key(key) in proc_keys:
            return True
    return False


def normalize_proc_slots(payload):
    result = {}
    for raw_proc, spec in payload.items():
        proc_key = normalize_proc_key(raw_proc)
        if proc_key not in config.thu_thuat_dur_mapper:
            raise ValueError(f"Unknown procedure key in slots config: {raw_proc}")

        if isinstance(spec, dict):
            grouped = {}
            for group_key, group_slots in spec.items():
                if isinstance(group_slots, str):
                    slots = [group_slots]
                elif isinstance(group_slots, (list, tuple)):
                    slots = list(group_slots)
                else:
                    raise ValueError(
                        f"Slots for procedure '{raw_proc}' group '{group_key}' must be list or string"
                    )
                grouped[str(group_key)] = normalize_time_slots(slots)
            if not grouped:
                raise ValueError(f"No slots defined for procedure '{raw_proc}'")
            result[proc_key] = grouped
        else:
            if isinstance(spec, str):
                slots = [spec]
            elif isinstance(spec, (list, tuple)):
                slots = list(spec)
            else:
                raise ValueError(
                    f"Slots for procedure '{raw_proc}' must be list or string"
                )
            result[proc_key] = normalize_time_slots(slots)

    if not result:
        raise ValueError("Procedure slots config is empty.")
    return result


def pick_group_key_for_date(grouped, date_index, date_str):
    group_keys = list(grouped.keys())
    if not group_keys:
        raise ValueError("No group keys found in slots config.")

    numeric_keys = []
    all_numeric = True
    for key in group_keys:
        try:
            numeric_keys.append(int(key))
        except ValueError:
            all_numeric = False
            break

    if all_numeric and numeric_keys:
        if all(1 <= k <= 31 for k in numeric_keys):
            day_num = parse_date_safe(date_str).day
            day_key = str(day_num)
            if day_key not in grouped:
                raise ValueError(f"Missing slots for day {day_num} in slots config.")
            return day_key

    try:
        group_keys.sort(key=lambda k: int(k))
    except ValueError:
        group_keys.sort()
    return group_keys[date_index % len(group_keys)]


def pick_slots_for_date_by_procedure(proc_slots, proc_key, date_index, date_str):
    spec = proc_slots.get(proc_key)
    if spec is None:
        raise ValueError(f"No slots configured for procedure '{proc_key}'")
    if isinstance(spec, dict):
        group_key = pick_group_key_for_date(spec, date_index, date_str)
        return spec[group_key]
    return spec


def build_full_to_short_map():
    return {v: k for k, v in config.map_ys_bs.items()}


def record_has_staff_conflict(record, used_staff_times, full_to_short, group1_set):
    for tt in record.get("thu_thuats", []):
        staff_full = tt.get("Nguoi Thuc Hien", "")
        staff_short = full_to_short.get(staff_full)
        if not staff_short:
            continue
        if staff_short not in group1_set:
            continue
        start_raw = tt.get("Ngay BD TH", "").replace("{SPACE}", " ").strip()
        if not start_raw:
            continue
        try:
            start_dt = datetime.strptime(start_raw, "%d-%m-%Y %H:%M")
        except ValueError:
            continue
        date_key = start_dt.strftime("%d-%m-%Y")
        time_key = start_dt.strftime("%H:%M")
        if time_key in used_staff_times[(date_key, staff_short)]:
            return True
    return False


def apply_record_staff_times(record, used_staff_times, full_to_short, group1_set):
    for tt in record.get("thu_thuats", []):
        staff_full = tt.get("Nguoi Thuc Hien", "")
        staff_short = full_to_short.get(staff_full)
        if not staff_short:
            continue
        if staff_short not in group1_set:
            continue
        start_raw = tt.get("Ngay BD TH", "").replace("{SPACE}", " ").strip()
        if not start_raw:
            continue
        try:
            start_dt = datetime.strptime(start_raw, "%d-%m-%Y %H:%M")
        except ValueError:
            continue
        date_key = start_dt.strftime("%d-%m-%Y")
        time_key = start_dt.strftime("%H:%M")
        used_staff_times[(date_key, staff_short)].add(time_key)


def shift_time_str(time_str, minutes):
    base = datetime.strptime(time_str, "%H:%M")
    shifted = base + timedelta(minutes=minutes)
    return shifted.strftime("%H:%M")


def convert_slot_time(time_str, slots_kind):
    kind = (slots_kind or "CD").upper()
    if kind == "CD":
        return shift_time_str(time_str, 5)
    if kind == "BD_TH":
        return time_str
    raise ValueError("slots_kind must be 'CD' or 'BD_TH'")


def build_date_range(start_date, end_date):
    start = parse_date_safe(start_date)
    end = parse_date_safe(end_date)
    if end < start:
        raise ValueError("End date must be on or after start date")

    dates = []
    current = start
    while current <= end:
        dates.append(current.strftime("%d-%m-%Y"))
        current += timedelta(days=1)
    return dates


def is_staff_available(staff_short, db_date, time_str, cache):
    key = (staff_short, db_date, time_str)
    if key in cache:
        return cache[key]
    try:
        ok, _reason = check_staff_available(staff_short, db_date, time_str)
    except Exception:
        ok = True
    cache[key] = ok
    return ok


def pick_staff_for_slot(
    date_str,
    start_time,
    rng,
    disabled,
    availability_cache,
    used_staff_times,
    used_group1=None,
):
    db_date = datetime.strptime(date_str, "%d-%m-%Y").strftime("%Y-%m-%d")

    group1_all = sorted([s for s in config.staff_p1_p3.keys() if s not in disabled])
    group2_all = sorted([s for s in config.staff_p2.keys() if s not in disabled])

    def is_free(staff_short):
        if staff_short not in config.staff_p1_p3:
            return True
        return start_time not in used_staff_times[(date_str, staff_short)]

    group1_avail = [
        s
        for s in group1_all
        if is_staff_available(s, db_date, start_time, availability_cache) and is_free(s)
    ]
    group2_avail = [
        s
        for s in group2_all
        if is_staff_available(s, db_date, start_time, availability_cache) and is_free(s)
    ]

    if not group1_avail:
        raise RuntimeError(f"No available Group 1 staff for {date_str} {start_time}")
    if not group2_avail:
        raise RuntimeError(f"No available Group 2 staff for {date_str} {start_time}")

    if used_group1:
        group1_candidates = [s for s in group1_avail if s not in used_group1]
        if not group1_candidates:
            group1_candidates = group1_avail
    else:
        group1_candidates = group1_avail

    p1 = rng.choice(group1_candidates)
    p3_candidates = [s for s in group1_candidates if s != p1] or [p1]
    p3 = rng.choice(p3_candidates)
    p2 = rng.choice(group2_avail)

    return [p1, p2, p3]


def record_sort_key(record):
    try:
        start_str = record["thu_thuats"][0]["Ngay BD TH"].replace("{SPACE}", " ")
        return datetime.strptime(start_str, "%d-%m-%Y %H:%M")
    except Exception:
        return datetime.strptime(record.get("ngay", "01-01-1970"), "%d-%m-%Y")


def generate_schedule(
    patient_id,
    procedures,
    start_date,
    end_date,
    time_slots,
    slots_by_date=None,
    slots_by_procedure=None,
    slots_kind="CD",
    seed=None,
    rng=None,
    use_all_slots=False,
    shuffle_slots=True,
    validate=True,
    shared_context=None,
):
    if rng is None:
        rng = random.Random(seed)

    if slots_by_date and (not start_date or not end_date):
        all_dates = sorted(slots_by_date.keys(), key=lambda d: parse_date_safe(d))
        if not all_dates:
            raise ValueError("Slots-by-date is empty.")
        start_date = all_dates[0]
        end_date = all_dates[-1]

    dates = build_date_range(start_date, end_date)

    if shared_context is None:
        disabled_staff = set(get_disabled_staff())
        availability_cache = {}
        full_to_short = build_full_to_short_map()
        group1_set = set(config.staff_p1_p3.keys())
        used_group1_by_slot = defaultdict(set)
        used_staff_times = defaultdict(set)
    else:
        disabled_staff = shared_context["disabled_staff"]
        availability_cache = shared_context["availability_cache"]
        full_to_short = shared_context["full_to_short"]
        group1_set = shared_context["group1_set"]
        used_group1_by_slot = shared_context["used_group1_by_slot"]
        used_staff_times = shared_context["used_staff_times"]

    records = []

    for date_index, date_str in enumerate(dates):
        if slots_by_date is not None:
            if date_str not in slots_by_date:
                raise ValueError(f"Missing slots for date {date_str}.")
            slots_for_day = list(slots_by_date[date_str])
        elif slots_by_procedure is not None:
            proc_key = procedures[0]
            slots_for_day = list(
                pick_slots_for_date_by_procedure(
                    slots_by_procedure, proc_key, date_index, date_str
                )
            )
        else:
            slots_for_day = list(time_slots)

        if not slots_for_day:
            raise ValueError(f"No slots available for date {date_str}.")

        if shuffle_slots:
            rng.shuffle(slots_for_day)

        def try_build_record(cd_time):
            start_time = convert_slot_time(cd_time, slots_kind)
            used_group1 = used_group1_by_slot[(date_str, start_time)]

            max_attempts = 50
            for _ in range(max_attempts):
                staff_list = pick_staff_for_slot(
                    date_str,
                    start_time,
                    rng,
                    disabled_staff,
                    availability_cache,
                    used_staff_times,
                    used_group1,
                )

                record = create_data_from_manual_input(
                    patient_id,
                    procedures,
                    staff_list,
                    date_str,
                    start_time,
                )

                if record_has_staff_conflict(
                    record, used_staff_times, full_to_short, group1_set
                ):
                    continue

                apply_record_staff_times(record, used_staff_times, full_to_short, group1_set)
                used_group1.update([staff_list[0], staff_list[2]])
                return record

            return None

        if use_all_slots:
            for cd_time in slots_for_day:
                record = try_build_record(cd_time)
                if record is None:
                    raise RuntimeError(
                        f"Could not find non-conflicting staff for {date_str} {cd_time}"
                    )
                records.append(record)
        else:
            record = None
            for cd_time in slots_for_day:
                record = try_build_record(cd_time)
                if record is not None:
                    break
            if record is None:
                raise RuntimeError(
                    f"Could not find non-conflicting staff for {date_str} "
                    f"with any slot in {', '.join(slots_for_day)}"
                )
            records.append(record)

    records.sort(key=record_sort_key)

    seen_patients = set()
    for record in records:
        pid = record.get("id")
        record["isFirst"] = pid not in seen_patients
        seen_patients.add(pid)

    if validate:
        errors = validate_all_data(records)
        if errors:
            raise RuntimeError("Schedule conflicts detected:\n" + "\n\n".join(errors))

    return records


def generate_schedule_batch(
    patients,
    procedures_default,
    start_date,
    end_date,
    time_slots,
    slots_by_date=None,
    slots_by_procedure=None,
    slots_kind="CD",
    seed=None,
    use_all_slots=False,
    shuffle_slots=True,
):
    rng = random.Random(seed)
    shared_context = {
        "disabled_staff": set(get_disabled_staff()),
        "availability_cache": {},
        "full_to_short": build_full_to_short_map(),
        "group1_set": set(config.staff_p1_p3.keys()),
        "used_group1_by_slot": defaultdict(set),
        "used_staff_times": defaultdict(set),
    }

    all_records = []
    for patient in patients:
        patient_id = patient["patient_id"]
        procedures = patient.get("procedures") or procedures_default
        if not procedures:
            raise ValueError("Procedures are required for batch generation.")

        records = generate_schedule(
            patient_id=patient_id,
            procedures=procedures,
            start_date=start_date,
            end_date=end_date,
            time_slots=time_slots,
            slots_by_date=slots_by_date,
            slots_by_procedure=slots_by_procedure,
            slots_kind=slots_kind,
            rng=rng,
            use_all_slots=use_all_slots,
            shuffle_slots=shuffle_slots,
            validate=False,
            shared_context=shared_context,
        )
        all_records.extend(records)

    errors = validate_all_data(all_records)
    if errors:
        raise RuntimeError("Schedule conflicts detected:\n" + "\n\n".join(errors))

    return all_records


def main():
    parser = argparse.ArgumentParser(
        description="Auto-generate schedule CSV with randomized staff assignments."
    )
    parser.add_argument("--patient-id", dest="patient_id")
    parser.add_argument("--procedures", dest="procedures")
    parser.add_argument("--start-date", dest="start_date")
    parser.add_argument("--end-date", dest="end_date")
    parser.add_argument(
        "--batch-file",
        dest="batch_file",
        help="Batch file with lines: patient_id;procedures(optional)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join("ai", "generated_schedule.csv"),
        help="Output CSV path (default: ai/generated_schedule.csv)",
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument(
        "--time-slots",
        dest="time_slots",
        help="Comma-separated list of time slots (HH:MM)",
    )
    parser.add_argument(
        "--time-slots-file",
        dest="time_slots_file",
        help="Path to a text file with one time slot per line",
    )
    parser.add_argument(
        "--slots-by-date-file",
        dest="slots_by_date_file",
        help=(
            "JSON file: date->slots OR procedure->grouped slots (Ngay CD). "
            "Example date: {\"DD-MM-YY\": [\"HH:MM\", ...]}"
        ),
    )
    parser.add_argument(
        "--slots-by-date-json",
        dest="slots_by_date_json",
        help="Inline JSON dict (same format as --slots-by-date-file)",
    )
    parser.add_argument(
        "--slots-kind",
        dest="slots_kind",
        choices=["CD", "BD_TH"],
        default=getattr(config, "AUTO_SCHEDULE_TIME_SLOTS_KIND", "CD"),
    )
    parser.add_argument(
        "--use-all-slots",
        action="store_true",
        help="Generate an entry for every time slot each day",
    )
    parser.add_argument(
        "--no-shuffle-slots",
        action="store_true",
        help="Keep time slots order (no shuffle)",
    )

    args = parser.parse_args()

    default_slots_file = os.path.join("ai", "slots_by_date.json")

    if not args.patient_id and not args.batch_file:
        args.patient_id = input("Patient ID: ").strip()
    if not args.procedures and not args.batch_file:
        args.procedures = input("Procedures (e.g., điện-xoa-kéo-giác): ").strip()

    slots_by_date = None
    slots_by_procedure = None
    slots_payload = None
    if args.slots_by_date_file:
        with open(args.slots_by_date_file, "r", encoding="utf-8") as f:
            slots_payload = json.load(f)
    elif args.slots_by_date_json:
        slots_payload = json.loads(args.slots_by_date_json)
    elif os.path.exists(default_slots_file):
        with open(default_slots_file, "r", encoding="utf-8") as f:
            slots_payload = json.load(f)

    if slots_payload is not None:
        if is_procedure_payload(slots_payload):
            slots_by_procedure = normalize_proc_slots(slots_payload)
        else:
            slots_by_date = read_slots_by_date(slots_payload)

    if not args.start_date and slots_by_date is None:
        args.start_date = input("Start date (DD-MM-YYYY): ").strip()
    if not args.end_date and slots_by_date is None:
        args.end_date = input("End date (DD-MM-YYYY): ").strip()

    procedures = normalize_procedures(args.procedures) if args.procedures else None

    if slots_by_date is None and slots_by_procedure is None:
        if args.time_slots_file:
            time_slots = read_time_slots_file(args.time_slots_file)
        elif args.time_slots:
            time_slots = parse_time_slots_arg(args.time_slots)
        else:
            time_slots = normalize_time_slots(
                getattr(config, "AUTO_SCHEDULE_TIME_SLOTS", [])
            )
    else:
        time_slots = []

    if args.batch_file:
        patients = []
        with open(args.batch_file, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                parts = [p.strip() for p in raw.split(";") if p.strip()]
                if not parts:
                    continue
                patient_id = parts[0]
                proc_val = parts[1] if len(parts) > 1 else None
                proc_list = normalize_procedures(proc_val) if proc_val else None
                patients.append({"patient_id": patient_id, "procedures": proc_list})

        records = generate_schedule_batch(
            patients=patients,
            procedures_default=procedures,
            start_date=args.start_date,
            end_date=args.end_date,
            time_slots=time_slots,
            slots_by_date=slots_by_date,
            slots_by_procedure=slots_by_procedure,
            slots_kind=args.slots_kind,
            seed=args.seed,
            use_all_slots=args.use_all_slots,
            shuffle_slots=not args.no_shuffle_slots,
        )
    else:
        records = generate_schedule(
            patient_id=args.patient_id,
            procedures=procedures,
            start_date=args.start_date,
            end_date=args.end_date,
            time_slots=time_slots,
            slots_by_date=slots_by_date,
            slots_by_procedure=slots_by_procedure,
            slots_kind=args.slots_kind,
            seed=args.seed,
            use_all_slots=args.use_all_slots,
            shuffle_slots=not args.no_shuffle_slots,
        )

    export_data_to_csv(records, args.output)
    print(f"Generated {len(records)} appointment(s) -> {args.output} (seed={args.seed})")


if __name__ == "__main__":
    main()
