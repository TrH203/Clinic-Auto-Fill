import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import os
import sys

# Mocking Windows-specific modules
sys.modules['pywinauto'] = MagicMock()
sys.modules['pywinauto.uia_element_info'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['cv2'] = MagicMock()

from handle_data import (
    parse_date_safe,
    format_datetime_data,
    remove_special_chars,
    load_csv_auto,
    convert_info_from_text,
    read_data,
)

class TestHandleData(unittest.TestCase):

    def test_parse_date_safe(self):
        self.assertEqual(parse_date_safe("22-11-2023"), datetime(2023, 11, 22))
        self.assertEqual(parse_date_safe("22/11/2023"), datetime(2023, 11, 22))
        self.assertEqual(parse_date_safe("22-11-23"), datetime(2023, 11, 22))
        self.assertEqual(parse_date_safe("22/11/23"), datetime(2023, 11, 22))
        with self.assertRaises(ValueError):
            parse_date_safe("2023-11-22")

    def test_format_datetime_data(self):
        self.assertEqual(format_datetime_data("22/11/23", "08:30"), "22-11-2023 08:30")
        self.assertEqual(format_datetime_data("22-11-2023", "14:00"), "22-11-2023 14:00")
        with self.assertRaises(ValueError):
            format_datetime_data("2023-11-22", "08:30")

    def test_remove_special_chars(self):
        self.assertEqual(remove_special_chars("a-b@c#1$2%3"), "abc123")
        self.assertEqual(remove_special_chars("   "), "")

    def test_load_csv_auto(self):
        # Test with file type 1
        with open("test1.csv", "w") as f:
            f.write("a,b,c")
        df = load_csv_auto("test1.csv")
        self.assertEqual(df.shape, (1, 3))
        os.remove("test1.csv")

        # Test with file type 2
        with open("test2.csv", "w") as f:
            f.write("a;b;c")
        df = load_csv_auto("test2.csv")
        self.assertEqual(df.shape, (1, 3))
        os.remove("test2.csv")

    def test_convert_info_from_text(self):
        # Mocking the config dictionaries used by the function
        with patch('handle_data.thu_thuat_dur_mapper', {'Sieu am bung': 15, 'Sieu am tuyen giap': 15}):
             with patch('handle_data.thu_thuat_ability_mapper', {'Sieu am bung': 'bs', 'Sieu am tuyen giap': 'bs'}):
                self.assertEqual(convert_info_from_text("sieu am bung"), ("Sieu am bung", 15, "bs"))
        self.assertEqual(convert_info_from_text("sieu am mat"), (None, None, None))

    def test_read_data(self):
        # Create a dummy csv file for testing
        with open("test_data.csv", "w") as f:
            f.write("1,Thủ thuật 1 - Thủ thuật 2,col3,col4,\n")
            f.write("10:00,Người 1 - Người 2,col3,col4,22-11-2023\n")

        # Mocking the config dictionaries used by the function
        with patch('handle_data.bs_mapper', {2: 'BS Vy'}):
            with patch('handle_data.thu_thuat_dur_mapper', {'Thủ thuật 1': 15, 'Thủ thuật 2': 15}):
                with patch('handle_data.thu_thuat_ability_mapper', {'Thủ thuật 1': 'bs', 'Thủ thuật 2': 'bs'}):
                    with patch('handle_data.map_ys_bs', {'người 1': 'BS Vy', 'người 2': 'BS Vy'}):
                        # Expected output
                        expected_output = [
                            {
                                'id': '1',
                                'isFirst': True,
                                'ngay': '22-11-2023',
                                'thu_thuats': [
                                    {
                                        'Ten': 'Thủ thuật 1',
                                        'BS CD': 'BS Vy',
                                        'Ngay CD': '22-11-2023{SPACE}09:55',
                                        'Ngay BD TH': '22-11-2023{SPACE}10:00',
                                        'Ngay KQ': '22-11-2023{SPACE}10:15',
                                        'Nguoi Thuc Hien': 'BS Vy'
                                    },
                                    {
                                        'Ten': 'Thủ thuật 2',
                                        'BS CD': 'BS Vy',
                                        'Ngay CD': '22-11-2023{SPACE}09:55',
                                        'Ngay BD TH': '22-11-2023{SPACE}10:17',
                                        'Ngay KQ': '22-11-2023{SPACE}10:32',
                                        'Nguoi Thuc Hien': 'BS Vy'
                                    }
                                ]
                            }
                        ]

                        # Call the function with the dummy csv
                        result = read_data("test_data.csv")

                        # Assert the result is as expected
                        self.assertEqual(result, expected_output)

        # Clean up the dummy file
        os.remove("test_data.csv")

if __name__ == '__main__':
    unittest.main()
