import unittest
from unittest.mock import patch, MagicMock
import sys
import numpy as np

# Mock UI modules
sys.modules['pywinauto'] = MagicMock()
sys.modules['pywinauto.keyboard'] = MagicMock()
sys.modules['pywinauto.uia_element_info'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['cv2'] = MagicMock()
sys.modules['pyperclip'] = MagicMock()

import tool
from tool import Tool

class TestTool(unittest.TestCase):
    def setUp(self):
        self.mock_app = MagicMock()
        self.mock_dlg = MagicMock()
        self.tool = Tool(self.mock_app, self.mock_dlg)

    def test_init(self):
        self.assertEqual(self.tool.app, self.mock_app)
        self.assertEqual(self.tool.dlg, self.mock_dlg)
        self.assertIsNone(self.tool.box_valid)

    def test_click_position(self):
        coords = (10, 20)
        self.tool._click_position(coords)
        self.mock_dlg.click_input.assert_called_with(coords=coords)

    def test_double_click_position(self):
        coords = (10, 20)
        self.tool._double_click_position(coords)
        self.mock_dlg.double_click_input.assert_called_with(coords=coords)

    @patch('tool.send_keys')
    def test_type_text(self, mock_send_keys):
        self.tool._type_text("hello")
        mock_send_keys.assert_any_call("^a")
        mock_send_keys.assert_any_call("hello")

    @patch('tool.send_keys')
    @patch('tool.pyperclip.copy')
    def test_type_text_no_telex(self, mock_copy, mock_send_keys):
        self.tool._type_text_no_telex("hello")
        mock_copy.assert_called_with("hello")
        mock_send_keys.assert_called_with("^v")

    @patch('tool.UIAElementInfo.from_point')
    @patch('tool.pyautogui.screenshot')
    @patch('tool.cv2.cvtColor')
    @patch('tool.pytesseract.image_to_string')
    def test_extract_text(self, mock_ocr, mock_cv2, mock_screenshot, mock_uia):
        # Setup mocks
        mock_element = MagicMock()
        mock_element.rectangle.left = 0
        mock_element.rectangle.top = 0
        mock_element.rectangle.right = 100
        mock_element.rectangle.bottom = 100
        mock_uia.return_value = mock_element

        # Mock screenshot return to be something convertible to numpy array
        mock_screenshot.return_value = MagicMock()
        # But we need np.array(screenshot) to work.
        # Mocking np.array is hard if it's used inside.
        # Instead, let's mock what np.array returns?
        # The code does: np_arr = np.array(screenshot)
        # If screenshot is a PIL image, np.array works.
        # But we mocked pyautogui.screenshot.

        # Let's verify logic:
        # 1. Double click
        # 2. Get region
        # 3. Screenshot
        # 4. OCR

        # We need to simulate box_valid logic.
        # first call sets self.box_valid

        # Setup a dummy numpy array
        dummy_arr = np.zeros((100, 100, 3), dtype=np.uint8)

        with patch('numpy.array', return_value=dummy_arr):
            mock_ocr.return_value = "Test Text"

            text = self.tool.extract_text(10, 10)

            self.assertEqual(text, "test text")
            self.assertIsNotNone(self.tool.box_valid)
            self.assertEqual(self.tool.box_valid, dummy_arr.shape)

    @patch('tool.Tool.extract_text')
    @patch('tool.convert_info_from_text')
    def test_fill_thu_thuat_data(self, mock_convert, mock_extract):
        # Mock data
        data = [{
            "Ten": "Thu Thuat A",
            "BS CD": "Dr. A",
            "Ngay CD": "01/01/2023",
            "Ngay BD TH": "01/01/2023",
            "Ngay KQ": "01/01/2023",
            "Nguoi Thuc Hien": "Nurse A"
        }]

        # Mock extraction and conversion
        mock_extract.side_effect = ["some text", None, None, None] # Loop runs 4 times
        mock_convert.return_value = ("Thu Thuat A", 30, "bs")

        self.tool.fill_thu_thuat_data(data, mode=True)

        # Verify clicks happened
        # Ideally we check calls to _click_position
        self.assertTrue(self.mock_dlg.click_input.called)

    def test_click_commands(self):
        self.tool.click_reload()
        self.mock_dlg.click_input.assert_called()

        self.tool.click_thuc_hien(True)
        self.mock_dlg.click_input.assert_called()

        self.tool.click_thuc_hien(False)
        self.mock_dlg.click_input.assert_called()

if __name__ == '__main__':
    unittest.main()
