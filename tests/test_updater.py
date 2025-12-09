import unittest
from unittest.mock import patch, MagicMock
import sys
import os

import updater

class TestUpdater(unittest.TestCase):

    @patch('updater.update_version_in_db')
    @patch('sys.argv', ['updater.py', 'old.exe', 'new.exe', '1.1.0'])
    @patch('os.remove')
    @patch('os.rename')
    @patch('subprocess.Popen')
    def test_main_success(self, mock_popen, mock_rename, mock_remove, mock_update_db):
        # Arguments are passed Bottom-Up (reverse of decorators order)
        # 1. subprocess.Popen -> mock_popen
        # 2. os.rename -> mock_rename
        # 3. os.remove -> mock_remove
        # 4. sys.argv (skipped)
        # 5. updater.update_version_in_db -> mock_update_db

        updater.main()

        mock_remove.assert_called_with('old.exe')
        mock_rename.assert_called_with('new.exe', 'old.exe')
        mock_update_db.assert_called_with('1.1.0')
        mock_popen.assert_called_with(['old.exe'])

    @patch('sys.argv', ['updater.py'])
    @patch('sys.exit')
    def test_main_invalid_args(self, mock_exit):
        mock_exit.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            updater.main()

        mock_exit.assert_called_with(1)

    @patch('sys.argv', ['updater.py', 'old.exe', 'new.exe', '1.1.0'])
    @patch('os.remove')
    @patch('time.sleep')
    @patch('sys.exit')
    def test_main_permission_error_retries(self, mock_exit, mock_sleep, mock_remove):
        # Bottom-Up:
        # 1. sys.exit -> mock_exit
        # 2. time.sleep -> mock_sleep
        # 3. os.remove -> mock_remove

        mock_remove.side_effect = PermissionError("Access denied")

        with self.assertRaises(PermissionError):
            updater.main()

        self.assertEqual(mock_remove.call_count, 10)
        self.assertEqual(mock_sleep.call_count, 9)

    @patch('sys.argv', ['updater.py', 'old.exe', 'new.exe', '1.1.0'])
    @patch('os.remove')
    @patch('os.rename')
    @patch('sys.exit')
    def test_main_general_exception(self, mock_exit, mock_rename, mock_remove):
        # Bottom-Up:
        # 1. sys.exit -> mock_exit
        # 2. os.rename -> mock_rename
        # 3. os.remove -> mock_remove

        mock_rename.side_effect = Exception("Rename failed")
        mock_exit.side_effect = SystemExit

        with self.assertRaises(SystemExit):
            updater.main()

        mock_exit.assert_called_with(1)

if __name__ == '__main__':
    unittest.main()
