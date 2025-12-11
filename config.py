bs_mapper = {
    0: "Trần Thị Thu Hiền", # Thu 2
    1: "Trần Thị Thu Hiền", # Thu 3
    2: "Trần Thị Thu Hiền", # Thu 4
    3: "Trần Thị Thu Hiền", # Thu 5
    4: "Trần Thị Thu Hiền", # Thu 6
    5: "Trần Thị Thu Hiền", # Thu 7
    6: "Nguyễn Duy Anh" # CN
}
thu_thuat_dur_mapper = {
    "điện": 30,
    # "thuỷ": 30,
    "thủy": 30,
    "xoa": 30,
    "kéo": 20,
    "giác": 20,
    "cứu": 20,
}
thu_thuat_ability_mapper = {
    "điện": "ys",
    # "thuỷ": 'bs',
    "thủy": "bs",
    "xoa": "ys",
    "kéo": "bs",
    "giác": "ys",
    "cứu": "ys",
}

DICH_VU_THU_THUAT = [
    (700,152),
    (700,172),
    (700,193),
    (700,215)
]

ID_BOX = (78, 191)

LUU = (537,966)
TIEP = (464, 964)
SUA = (670,966)

PATIENT_ROW = (181, 249)

BSCD_NGUOI_DAU_TIEN = (1595,348)
CCHN_NGUOI_DAU_TIEN = (1624,444)

CCHN = (1820,344)
NGAY_KQ = (1820,322)
NGAY_BDTH = (1820,299)
NGAY_CD = (1820,278)
BSCD = (1820, 256)

NGAY_KET_THUC = (275, 151)
NGAY_BAT_DAU = (153, 151)

CHO_THUC_HIEN = (126, 133)
DA_THUC_HIEN = (250, 133)

RELOAD = (390, 141)



map_ys_bs = {
    "hiền":"Trần Thị Thu Hiền",
    "hoà":"Trần Thị Diệu Hoà",
    "hòa":"Trần Thị Diệu Hoà",
    "anh": "Nguyễn Duy Anh",
    "duy": "Nguyễn Văn Duy",
    "lya": "H' Lya Niê",
    "thuận": "Võ Thị Bích Thuận",
    "quân": "Lê Văn Quân",
    "khoái": "Nguyễn Công Khoái",
    "thịnh": "Nguyễn Văn Thịnh",
    "quang": "Đinh Văn Quang",
    "hạnh": "Nguyễn Hữu Hạnh",
    "diệu": "Nguyễn Thị Diệu",
    "lực": "Lê Đức Lực",
    "nguyện": "Võ Thị Như Nguyện",
    "trị": "Bùi Tá Việt Trị",  #BS
    "thơ": "Lê Thị Ngọc Thơ",
    "nhẹ": "H' Nhẹ Niê",
    "trúc": "Lê Ngọc Trúc",
}

# List of disabled/excluded staff members (lowercase short names as keys in map_ys_bs)
# Staff in this list will not appear in manual entry and will cause errors during automation
disabled_staff = ["diệu"]
