import time
from pywinauto.keyboard import send_keys
from handle_data import convert_info_from_text
from config import DICH_VU_THU_THUAT, BSCD, BSCD_NGUOI_DAU_TIEN, NGAY_CD, NGAY_BDTH, NGAY_KQ, \
    NGAY_KET_THUC, NGAY_BAT_DAU, SUA, ID_BOX, CHO_THUC_HIEN, DA_THUC_HIEN, RELOAD, CCHN_NGUOI_DAU_TIEN, CCHN, LUU
import pyautogui
import pytesseract
import cv2
from pywinauto.uia_element_info import UIAElementInfo
import numpy as np
import pyperclip

class Tool:
    def __init__(self, app, dlg):
        self.app = app
        self.dlg = dlg
        self.box_valid = None


    def _double_click_position(self, coords, wait=0.1):
        self.dlg.double_click_input(coords=coords)
        time.sleep(wait)

    def _click_position(self, coords, wait=0.1):
        self.dlg.click_input(coords=coords)
        time.sleep(wait)
    
    def _type_text(self, text:str, wait=0.1):
        send_keys("^a")
        time.sleep(wait)

        send_keys(text)
        time.sleep(wait)
    def _type_text_no_telex(self, text:str, wait=0.1):
        pyperclip.copy(text)
        send_keys("^v")
        time.sleep(wait)

    def extract_text(self, x, y, save_dir="saved_images", index=0):

        self._double_click_position(coords=(x, y))

        element_info = UIAElementInfo.from_point(x, y)
        rect = element_info.rectangle
        region = (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)

        # Take screenshot of the region
        screenshot = pyautogui.screenshot(region=region)

        np_arr = np.array(screenshot)
        
        if self.box_valid == None:
            self.box_valid = np_arr.shape

        img = cv2.cvtColor(np_arr, cv2.COLOR_RGB2BGR)

        # Save image
        # os.makedirs(save_dir, exist_ok=True)
        # save_path = os.path.join(save_dir, f"rect_{index}.png")
        # cv2.imwrite(save_path, img)

        # OCR text
        if np_arr.shape == self.box_valid:
            text = pytesseract.image_to_string(img, lang='vie')
            if text == "":
                return "cứu"
            return text.strip().lower()
        else:
            return None

    def click_reload(self):
        self._click_position(coords=RELOAD)

    def click_thuc_hien(self, mode:bool = True):
        if mode == False: # Cho thuc hien
            self._click_position(coords=CHO_THUC_HIEN)
        if mode == True: # Da Thuc Hien
            self._click_position(coords=DA_THUC_HIEN)

    
    def _type_date_arrow(self, ngay: str):
        # Format: dd-mm-yyyy or similar. Split by any non-digit.
        # However, user example is 12-02-2025. 
        # Logic: Type day -> Right -> Type month -> Right -> Type year
        
        parts = ngay.replace('/', '-').replace('.', '-').split('-')
        if len(parts) >= 3:
            day, month, year = parts[0], parts[1], parts[2]
            
            # Type Day
            self._type_text(day)
            send_keys("{RIGHT}")
            time.sleep(0.1)
            
            # Type Month
            self._type_text(month)
            send_keys("{RIGHT}")
            time.sleep(0.1)
            
            # Type Year
            self._type_text(year)
        else:
            # Fallback if parsing fails
            self._type_text(ngay)
    
    def type_ngay_bat_dau(self, ngay: str, arrow_mode: bool = False):
        # Nhap ngay bat dau
        self._click_position(coords=NGAY_BAT_DAU)
        if arrow_mode:
            self._type_date_arrow(ngay)
        else:
            self._type_text(ngay)

    def type_ngay_ket_thuc(self, ngay: str, arrow_mode: bool = False):
        self.dlg.click_input(coords=NGAY_KET_THUC)
        if arrow_mode:
            self._type_date_arrow(ngay)
        else:
            self._type_text(ngay)

    def type_id(self, id:str):
        self._click_position(coords=ID_BOX)
        self._type_text(id)

    def fill_thu_thuat_data(self, data: list, mode = True):
        for idx in range(4):
            
            if mode == True:
                x, y = DICH_VU_THU_THUAT[idx]
            else:
                x, y = DICH_VU_THU_THUAT[0]

            text = self.extract_text(x=x,y=y, index=idx)
            
            print("Text Extracted: ", text)
            # time.sleep(0.2)
            # continue
            if text is None or text == "":
                return
            thu_thuat, thuthuat_duration, thuthuat_ability = convert_info_from_text(text)
            
            if thu_thuat is None:
                continue
            
            info = None
            for j in data:
                if thu_thuat == j["Ten"]:
                    info = j
                    
            if info == None:
                print("No info")
                continue
            
            self._click_position(coords=(x,y), wait=0.5) # Click Dich vu ky thuat
            
            if mode:
                self._click_position(coords=SUA, wait=0.1) # Click sua
            
            # Click BS CD
            self._click_position(coords=BSCD,  wait=0.2) # Click BS CD
            self._type_text_no_telex(info["BS CD"])
            self._click_position(coords=BSCD_NGUOI_DAU_TIEN) # Click nguoi dau tien trong danh sach
            
            # Click Ngay CD:
            # print("Ngay CD", info["Ngay CD"])
            self._click_position(coords=NGAY_CD, wait=0.1)
            self._type_text(info["Ngay CD"])

            # Click Ngay BDTH
            self._click_position(coords=NGAY_BDTH, wait=0.1)
            self._type_text(info["Ngay BD TH"], wait=0.1)
            
            # Click Ngay KQ
            self._click_position(coords=NGAY_KQ, wait=0.1)
            self._type_text(info["Ngay KQ"])
            
            # # Click CCHN
            self._click_position(coords=CCHN, wait=0.1)
            self._type_text_no_telex(info["Nguoi Thuc Hien"])
            self._click_position(coords=CCHN_NGUOI_DAU_TIEN) # Click nguoi dau tien trong danh sach

            self._click_position(coords=LUU) # Luu