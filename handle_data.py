import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from config import bs_mapper, thu_thuat_ability_mapper, thu_thuat_dur_mapper, map_ys_bs, staff_p1_p3, staff_p2
from pywinauto.uia_element_info import UIAElementInfo
import pyautogui
import pytesseract
import cv2
import re

# -----------------------------
# Helpers chung
# -----------------------------

def parse_date_safe(date_str: str):
    date_str = date_str.strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d-%m-%y", "%d/%m/%y"):
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            pass
    raise ValueError(f"Không parse được ngày: {date_str}")


def format_datetime_data(ngay, gio):
    ngay = ngay.strip()
    gio = gio.strip()

    for fmt in ["%d/%m/%y", "%d/%m/%Y", "%d-%m-%y", "%d-%m-%Y"]:
        try:
            dt = datetime.strptime(f"{ngay} {gio}", f"{fmt} %H:%M")
            return dt.strftime("%d-%m-%Y %H:%M")
        except:
            continue

    raise ValueError(f"Không parse được ngày giờ: {ngay} {gio}")


def remove_special_chars(s: str) -> str:
    return re.sub(r'[^A-Za-z0-9]', '', s)


def extract_text(x, y):
    element_info = UIAElementInfo.from_point(x, y)
    rect = element_info.rectangle

    region = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

    screenshot = pyautogui.screenshot(region=region)
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

    text = pytesseract.image_to_string(img, lang='vie')

    if text:
        return remove_special_chars(text.strip().replace("thủy", "thuỷ"))
    else:
        raise "ERROR in extract text"


# -----------------------------
# AUTO-DETECT CSV
# -----------------------------
def load_csv_auto(source):
    """
    Tự nhận dạng file CSV kiểu 1 hay kiểu 2
    """
    try:
        df = pd.read_csv(source, header=None, delimiter=';')
        if df.shape[1] > 1:
            return df   # file 2
    except:
        pass

    return pd.read_csv(source, header=None)  # file 1 mặc định


# -----------------------------
# LOGIC CHUNG XỬ LÝ DATA
# -----------------------------
def read_data(source='data.csv') -> list:
    data = load_csv_auto(source)

    all_data = []
    i = 0

    # Nhóm theo block giống cả 2 file
    while i < len(data):
        row = list(data.iloc[i])
        if isinstance(row[-1], float):
            raw_data = [row[:-1]]

            i += 1
            if i >= len(data): break

            row = list(data.iloc[i])

            while isinstance(row[-1], str):
                raw_data.append(row)
                i += 1
                if i < len(data):
                    row = list(data.iloc[i])
                else:
                    break

            all_data.append(raw_data)

        else:
            i += 1

    # -----------------------------
    # Chuyển thành output list
    # -----------------------------
    list_data = []

    for row in all_data:
        isFirst = True

        for i in range(1, len(row)):

            final_data = {
                "id": row[0][0],
                "isFirst": isFirst
            }
            if isFirst:
                isFirst = False

            ngay_raw = row[i][-1]
            try:
                final_data["ngay"] = parse_date_safe(ngay_raw).strftime("%d-%m-%Y")
            except ValueError as e:
                raise ValueError(f"Lỗi ID {final_data['id']}: Ngày '{ngay_raw}' không hợp lệ. {e}")

            thu_thuats_raw = row[0][1]
            if not isinstance(thu_thuats_raw, str):
                 raise ValueError(f"Lỗi ID {final_data['id']}: Dòng dịch vụ không đúng định dạng.")

            thu_thuats = [x.strip() for x in thu_thuats_raw.split("-")]

            # Validate thu thuat names
            for tt in thu_thuats:
                 if tt not in thu_thuat_dur_mapper:
                     raise ValueError(f"Lỗi ID {final_data['id']}: Tên thủ thuật '{tt}' sai hoặc thiếu dấu gạch ngang (-).")

            final_data["thu_thuats"] = []

            flag = False
            ngay_CĐ = row[i][-1]

            for idx, tt in enumerate(thu_thuats):
                obj = {"Ten": tt}

                if idx == 0:
                    gio_dau = datetime.strptime(row[i][0], "%H:%M")
                    lui = 5
                    gio_CD = gio_dau - timedelta(minutes=lui)

                    sang_start = datetime.strptime("07:00", "%H:%M").time()
                    sang_early = datetime.strptime("06:00", "%H:%M").time()
                    chieu_start = datetime.strptime("13:30", "%H:%M").time()
                    chieu_early = datetime.strptime("12:00", "%H:%M").time()

                    # fix giờ quá sớm
                    if sang_early < gio_CD.time() < sang_start:
                        gio_CD = datetime.combine(gio_CD.date(), sang_start)
                    elif chieu_early < gio_CD.time() < chieu_start:
                        gio_CD = datetime.combine(gio_CD.date(), chieu_start)

                else:
                    gio_dau = gio_cuoi + timedelta(minutes=2)

                gio_cuoi = gio_dau + timedelta(minutes=thu_thuat_dur_mapper[tt])

                d = parse_date_safe(ngay_CĐ)
                thu = d.weekday()

                nguoi_raw = row[i][1]
                if not isinstance(nguoi_raw, str):
                    raise ValueError(f"Lỗi ID {final_data['id']}: Dòng người thực hiện không đúng định dạng.")

                nguoi = [x.strip() for x in nguoi_raw.split("-")]

                # Validate staff names globally first
                for n in nguoi:
                    if n.lower() not in map_ys_bs:
                         raise ValueError(f"Lỗi ID {final_data['id']}: Tên nhân viên '{n}' sai hoặc thiếu dấu gạch ngang (-).")

                if thu_thuat_ability_mapper[tt] == "bs":
                    idx_ng = 1 if len(nguoi) > 1 else 0
                else:
                    idx_ng = 2 if flag else 0
                    flag = not flag
                
                # Strict validation based on position
                staff_key = nguoi[idx_ng].lower()
                if idx_ng == 1:
                    if staff_key not in staff_p2:
                        raise ValueError(f"Lỗi ID {final_data['id']}: Nhân viên '{map_ys_bs[staff_key]}' (vị trí 2) không có trong danh sách Group 2.")
                else:
                    if staff_key not in staff_p1_p3:
                        raise ValueError(f"Lỗi ID {final_data['id']}: Nhân viên '{map_ys_bs[staff_key]}' (vị trí {idx_ng+1}) không có trong danh sách Group 1.")

                obj["BS CD"] = bs_mapper[thu]

                try:
                    obj["Ngay CD"] = format_datetime_data(ngay_CĐ, gio_CD.strftime("%H:%M")).replace(" ", "{SPACE}")
                    obj["Ngay BD TH"] = format_datetime_data(ngay_CĐ, gio_dau.strftime("%H:%M")).replace(" ", "{SPACE}")
                    obj["Ngay KQ"] = format_datetime_data(ngay_CĐ, gio_cuoi.strftime("%H:%M")).replace(" ", "{SPACE}")
                except ValueError as e:
                     raise ValueError(f"Lỗi ID {final_data['id']}: {e}")

                obj["Nguoi Thuc Hien"] = map_ys_bs[staff_key]

                final_data["thu_thuats"].append(obj)

            list_data.append(final_data)

    return list_data

def convert_info_from_text(text:str):
    for i in thu_thuat_dur_mapper.keys():
        if i.lower() in text.strip().lower():
            return i, thu_thuat_dur_mapper[i], thu_thuat_ability_mapper[i]
    
    return None, None, None


# -----------------------------
# MANUAL DATA ENTRY SUPPORT
# -----------------------------

def create_data_from_manual_input(patient_id, procedures_list, staff_list, appointment_date, appointment_time):
    """
    Create automation data from manual input.
    
    Args:
        patient_id: Patient ID string
        procedures_list: List of procedure names (e.g., ["điện", "thuỷ"])
        staff_list: List of staff names (e.g., ["Hiền", "Hoà"])
        appointment_date: Date string in format "dd-mm-yyyy"
        appointment_time: Time string in format "HH:MM"
    
    Returns:
        Dictionary in the same format as read_data() output
    """
    from datetime import datetime, timedelta
    
    # Validate procedures
    for proc in procedures_list:
        if proc not in thu_thuat_dur_mapper:
            raise ValueError(f"Unknown procedure: {proc}")
    
    # Validate staff
    for staff in staff_list:
        if staff.lower() not in map_ys_bs:
            raise ValueError(f"Unknown staff member: {staff}")
    
    # Parse date and time
    try:
        ngay_dt = datetime.strptime(appointment_date, "%d-%m-%Y")
        gio_start = datetime.strptime(appointment_time, "%H:%M")
    except ValueError as e:
        raise ValueError(f"Invalid date/time format: {e}")
    
    thu_thuats = []
    flag = False
    
    # Calculate times for first procedure
    gio_dau = datetime.combine(ngay_dt.date(), gio_start.time())
    lui = 5
    gio_CD = gio_dau - timedelta(minutes=lui)
    
    # Fix times that are too early
    sang_start = datetime.strptime("07:00", "%H:%M").time()
    sang_early = datetime.strptime("06:00", "%H:%M").time()
    chieu_start = datetime.strptime("13:30", "%H:%M").time()
    chieu_early = datetime.strptime("12:00", "%H:%M").time()
    
    if sang_early < gio_CD.time() < sang_start:
        gio_CD = datetime.combine(gio_CD.date(), sang_start)
    elif chieu_early < gio_CD.time() < chieu_start:
        gio_CD = datetime.combine(gio_CD.date(), chieu_start)
    
    thu = ngay_dt.weekday()
    
    for idx, tt in enumerate(procedures_list):
        obj = {"Ten": tt}
        
        if idx > 0:
            gio_dau = gio_cuoi + timedelta(minutes=2)
        
        gio_cuoi = gio_dau + timedelta(minutes=thu_thuat_dur_mapper[tt])
        
        # Determine staff
        if thu_thuat_ability_mapper[tt] == "bs":
            idx_ng = 1 if len(staff_list) > 1 else 0
        else:
            idx_ng = 2 if flag else 0
            flag = not flag
        
        obj["BS CD"] = bs_mapper[thu]
        obj["Ngay CD"] = format_datetime_data(appointment_date, gio_CD.strftime("%H:%M")).replace(" ", "{SPACE}")
        obj["Ngay BD TH"] = format_datetime_data(appointment_date, gio_dau.strftime("%H:%M")).replace(" ", "{SPACE}")
        obj["Ngay KQ"] = format_datetime_data(appointment_date, gio_cuoi.strftime("%H:%M")).replace(" ", "{SPACE}")
        obj["Nguoi Thuc Hien"] = map_ys_bs[staff_list[idx_ng].lower()]
        
        thu_thuats.append(obj)
    
    return {
        "id": patient_id,
        "isFirst": True,
        "ngay": appointment_date,
        "thu_thuats": thu_thuats
    }


def save_manual_data_to_json(data_list, filename="manual_data.json"):
    """Save manual data entries to JSON file."""
    import json
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        raise Exception(f"Failed to save manual data: {e}")


def load_manual_data_from_json(filename="manual_data.json"):
    """Load manual data entries from JSON file."""
    import json
    import os
    
    if not os.path.exists(filename):
        return []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise Exception(f"Failed to load manual data: {e}")


def merge_csv_and_manual_data(csv_data, manual_data):
    """
    Merge CSV and manual data into a single list.
    
    Args:
        csv_data: List from read_data()
        manual_data: List from manual entry
    
    Returns:
        Combined list sorted by date
    """
    combined = csv_data + manual_data
    
    # Sort by date (optional, but helpful)
    try:
        combined.sort(key=lambda x: datetime.strptime(x["ngay"], "%d-%m-%Y"))
    except:
        pass  # If sorting fails, just return unsorted
    
    return combined


def export_data_to_csv(data_list, filename):
    """
    Export data to CSV file in the same format as the import format.
    
    Format:
    PatientID;procedure1-procedure2-procedure3-procedure4;
    HH:MM;staff1-staff2-staff3;DD-MM-YY
    HH:MM;staff1-staff2-staff3;DD-MM-YY
    ...
    
    Args:
        data_list: List of data records from read_data()
        filename: Output CSV filename
    """
    import csv
    from collections import defaultdict
    
    # Group records by patient ID
    grouped_data = defaultdict(list)
    for record in data_list:
        patient_id = record.get('id', '')
        grouped_data[patient_id].append(record)
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        for patient_id, records in grouped_data.items():
            # Get procedures from first record (they should be the same for all records of this patient)
            if records and records[0].get('thu_thuats'):
                procedures = [tt.get('Ten', '') for tt in records[0]['thu_thuats']]
                procedures_str = '-'.join(procedures)
                
                # Write patient ID and procedures line
                writer.writerow([patient_id, procedures_str, ''])
                
                # Write each appointment (time, staff, date)
                for record in records:
                    ngay = record.get('ngay', '')
                    # Convert DD-MM-YYYY to DD-MM-YY
                    if ngay:
                        parts = ngay.split('-')
                        if len(parts) == 3:
                            ngay_short = f"{parts[0]}-{parts[1]}-{parts[2][-2:]}"
                        else:
                            ngay_short = ngay
                    else:
                        ngay_short = ''
                    
                    # Extract time from first thu_thuat
                    if record.get('thu_thuats') and len(record['thu_thuats']) > 0:
                        first_tt = record['thu_thuats'][0]
                        ngay_bd_th = first_tt.get('Ngay BD TH', '')
                        # Extract time from "DD-MM-YYYY{SPACE}HH:MM" format
                        if '{SPACE}' in ngay_bd_th:
                            time_part = ngay_bd_th.split('{SPACE}')[1] if len(ngay_bd_th.split('{SPACE}')) > 1 else ''
                        else:
                            time_part = ''
                        
                        # Extract staff members (get unique staff from all thu_thuats)
                        staff_set = []
                        for tt in record['thu_thuats']:
                            staff_name = tt.get('Nguoi Thuc Hien', '')
                            if staff_name:
                                # Convert full name to short name
                                staff_short = None
                                for short, full in map_ys_bs.items():
                                    if full == staff_name:
                                        staff_short = short
                                        break
                                if staff_short and staff_short not in staff_set:
                                    staff_set.append(staff_short)
                        
                        staff_str = '-'.join(staff_set) if staff_set else ''
                        
                        # Write appointment row
                        writer.writerow([time_part, staff_str, ngay_short])


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    from collections import Counter

    def count_values(data):
        counter = Counter()
        for item in data:
            for k, v in item.items():
                counter[k] += 1
        return counter
    
    import json

    in1 = read_data("data-Linh.csv")
    in2 = read_data("data-QN.csv")

    true_in1 = json.load(open("data-Linh.json", encoding="utf-8"))
    true_in2 = json.load(open("data-QN.json", encoding="utf-8"))

    if (count_values(in1) == count_values(true_in1)
        and count_values(in2) == count_values(true_in2)):
        print("All tests passed!")
    else:
        print("Mismatch detected!")
        print("Linh diff:", count_values(in1) - count_values(true_in1))
        print("QN diff:", count_values(in2) - count_values(true_in2))

