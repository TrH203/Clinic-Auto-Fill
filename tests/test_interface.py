import unittest
from unittest.mock import patch, MagicMock
import sys

# Mock UI and external libs
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.ttk'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.scrolledtext'] = MagicMock()

# Mock pywinauto completely
sys.modules['pywinauto'] = MagicMock()
sys.modules['pywinauto.keyboard'] = MagicMock()
sys.modules['pywinauto.uia_element_info'] = MagicMock()

sys.modules['pyperclip'] = MagicMock()
sys.modules['pyautogui'] = MagicMock()
sys.modules['pytesseract'] = MagicMock()
sys.modules['cv2'] = MagicMock()

sys.modules['requests'] = MagicMock()
sys.modules['subprocess'] = MagicMock()

# Do NOT mock internal modules here to avoid polluting sys.modules for other tests.
# handle_data and tool will be imported for real, but their dependencies (above) are mocked.

import interface

class TestInterface(unittest.TestCase):

    def setUp(self):
        self.root = MagicMock()
        with patch('database.get_current_version_from_db', return_value="1.0.0"):
            self.app = interface.AutomationGUI(self.root)

    def test_init(self):
        self.assertIsNotNone(self.app)
        self.assertEqual(self.app.root, self.root)
        self.assertFalse(self.app.is_running)

    @patch('interface.read_data')
    def test_load_data_file(self, mock_read_data):
        self.app.data_file_path.get.return_value = "data.csv"
        mock_read_data.return_value = [{"id": 1}, {"id": 2}]

        self.app.load_data_file()

        self.assertEqual(len(self.app.all_data), 2)
        self.app.progress_bar.__setitem__.assert_called_with('maximum', 2)

    @patch('interface.requests.get')
    def test_check_for_updates_thread_found(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"tag_name": "2.0.0"}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        with patch('interface.CURRENT_VERSION', "1.0.0"):
             self.app._check_for_updates_thread()

             self.assertIsNotNone(self.app.update_info)
             self.assertEqual(self.app.update_info["tag_name"], "2.0.0")

    @patch('interface.requests.get')
    @patch('interface.subprocess.Popen')
    @patch('builtins.open', new_callable=MagicMock)
    def test_download_and_update(self, mock_open, mock_popen, mock_get):
        self.app.update_info = {
            "tag_name": "2.0.0",
            "assets": [{"browser_download_url": "http://example.com/app.exe", "name": "app.exe"}]
        }

        mock_response = MagicMock()
        mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.return_value = mock_response

        self.app.download_and_update()

        mock_get.assert_called_with("http://example.com/app.exe", stream=True)
        mock_open.assert_called()
        mock_popen.assert_called()
        self.root.destroy.assert_called()

    @patch('interface.Application')
    def test_connect_to_app(self, mock_application):
        mock_app_instance = MagicMock()
        mock_application.return_value.connect.return_value = mock_app_instance
        mock_app_instance.window.return_value = MagicMock()

        self.app.connect_to_app()

        self.assertIsNotNone(self.app.app)
        self.assertIsNotNone(self.app.dlg)
        self.assertEqual(self.app.conn_status_label.config.call_args[1]['foreground'], 'green')

if __name__ == '__main__':
    unittest.main()
