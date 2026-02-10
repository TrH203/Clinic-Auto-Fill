import time
from pywinauto.keyboard import send_keys
from handle_data import convert_info_from_text
import config
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
        print(f"Double clicking at: {coords}")
        self.dlg.double_click_input(coords=coords)
        time.sleep(wait)

    def _click_position(self, coords, wait=0.1):
        print(f"Clicking at: {coords}")
        self.dlg.click_input(coords=coords)
        time.sleep(wait)
    
    def _type_text(self, text:str, wait=0.1):
        send_keys("^a")
        time.sleep(wait)

        send_keys(text)
        time.sleep(wait)



    def _type_text_pure(self, text:str, wait=0.1):
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
        print(f"DEBUG: Reloading at {config.RELOAD}")
        self._click_position(coords=config.RELOAD)

    def click_thuc_hien(self, mode:bool = True):
        if mode == False: # Cho thuc hien
            print(f"DEBUG: Clicking CHO_THUC_HIEN at {config.CHO_THUC_HIEN}")
            self._click_position(coords=config.CHO_THUC_HIEN)
        if mode == True: # Da Thuc Hien
            print(f"DEBUG: Clicking DA_THUC_HIEN at {config.DA_THUC_HIEN}")
            self._click_position(coords=config.DA_THUC_HIEN)

    
    def _type_date_arrow(self, ngay: str):
        # User format example: 16-12-2025{SPACE}09:05
        # Logic: 16 -> 12 -> 2025 -> 09 -> 05
        send_keys("^a")
        # Replace common separators with a standard one
        clean_ngay = ngay.replace('{SPACE}', '-').replace(' ', '-').replace('/', '-').replace('.', '-').replace(':', '-')
        parts = clean_ngay.split('-')
        
        # Filter empty parts just in case
        parts = [p for p in parts if p]
        
        for i, part in enumerate(parts):
            self._type_text_pure(part)
            # Press right arrow if it's not the last part
            if i < len(parts) - 1:
                send_keys("{RIGHT}")
                time.sleep(0.1)
    
    def type_ngay_bat_dau(self, ngay: str, arrow_mode: bool = False):
        # Nhap ngay bat dau
        self._click_position(coords=config.NGAY_BAT_DAU)
        if arrow_mode:
            self._type_date_arrow(ngay)
        else:
            self._type_text(ngay)

    def type_ngay_ket_thuc(self, ngay: str, arrow_mode: bool = False):
        self.dlg.click_input(coords=config.NGAY_KET_THUC)
        if arrow_mode:
            self._type_date_arrow(ngay)
        else:
            self._type_text(ngay)

    def type_id(self, id:str):
        self._click_position(coords=config.ID_BOX)
        self._type_text(id)

    def fill_thu_thuat_data(self, data: list, mode = True, arrow_mode: bool = False):
        for idx in range(4):
            
            if mode == True:
                x, y = config.DICH_VU_THU_THUAT[idx]
            else:
                x, y = config.DICH_VU_THU_THUAT[0]

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
                self._click_position(coords=config.SUA, wait=0.1) # Click sua
            
            # Click BS CD
            self._click_position(coords=config.BSCD,  wait=0.2) # Click BS CD
            self._type_text_no_telex(info["BS CD"])
            self._click_position(coords=config.BSCD_NGUOI_DAU_TIEN) # Click nguoi dau tien trong danh sach
            
            # Click Ngay CD:
            # print("Ngay CD", info["Ngay CD"])
            self._click_position(coords=config.NGAY_CD, wait=0.1)
            if arrow_mode:
                self._type_date_arrow(info["Ngay CD"])
            else:
                self._type_text(info["Ngay CD"])

            # Click Ngay BDTH
            self._click_position(coords=config.NGAY_BDTH, wait=0.1)
            if arrow_mode:
                self._type_date_arrow(info["Ngay BD TH"])
            else:
                self._type_text(info["Ngay BD TH"], wait=0.1)
            
            # Click Ngay KQ
            self._click_position(coords=config.NGAY_KQ, wait=0.1)
            if arrow_mode:
                self._type_date_arrow(info["Ngay KQ"])
            else:
                self._type_text(info["Ngay KQ"])
            
            # # Click CCHN
            self._click_position(coords=config.CCHN, wait=0.1)
            self._type_text_no_telex(info["Nguoi Thuc Hien"])
            self._click_position(coords=config.CCHN_NGUOI_DAU_TIEN) # Click nguoi dau tien trong danh sach

            # Click KTV
            self._click_position(coords=config.KTV, wait=0.1)
            self._type_text_no_telex(info["Nguoi Thuc Hien"])
            self._click_position(coords=config.KTV_NGUOI_DAU_TIEN) # Click nguoi dau tien trong danh sach

            self._click_position(coords=config.LUU) # Luu
