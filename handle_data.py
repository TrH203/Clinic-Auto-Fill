import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
from config import bs_mapper, thu_thuat_ability_mapper, thu_thuat_dur_mapper, map_ys_bs
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
            final_data["ngay"] = parse_date_safe(ngay_raw).strftime("%d-%m-%Y")

            thu_thuats = [x.strip() for x in row[0][1].split("-")]

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

                nguoi = [x.strip() for x in row[i][1].split("-")]

                if thu_thuat_ability_mapper[tt] == "bs":
                    idx_ng = 1 if len(nguoi) > 1 else 0
                else:
                    idx_ng = 2 if flag else 0
                    flag = not flag

                obj["BS CD"] = bs_mapper[thu]
                obj["Ngay CD"] = format_datetime_data(ngay_CĐ, gio_CD.strftime("%H:%M")).replace(" ", "{SPACE}")
                obj["Ngay BD TH"] = format_datetime_data(ngay_CĐ, gio_dau.strftime("%H:%M")).replace(" ", "{SPACE}")
                obj["Ngay KQ"] = format_datetime_data(ngay_CĐ, gio_cuoi.strftime("%H:%M")).replace(" ", "{SPACE}")
                obj["Nguoi Thuc Hien"] = map_ys_bs[nguoi[idx_ng].lower()]

                final_data["thu_thuats"].append(obj)

            list_data.append(final_data)

    return list_data


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

