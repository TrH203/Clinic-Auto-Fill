import unittest
import sqlite3
import os
from unittest.mock import patch
import database

class TestDatabase(unittest.TestCase):

    def setUp(self):
        # Use a temporary database file for testing
        self.test_db = "test_app_data.db"
        self.original_db = database.DATABASE_FILE
        database.DATABASE_FILE = self.test_db

        # Remove if exists
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def tearDown(self):
        # Clean up
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        database.DATABASE_FILE = self.original_db

    def test_initialize_database_creates_file_and_table(self):
        database.initialize_database()
        self.assertTrue(os.path.exists(self.test_db))

        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='version'")
        table = cursor.fetchone()
        self.assertIsNotNone(table)

        # Check initial version
        cursor.execute("SELECT version_string FROM version WHERE id = 1")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        # Default fallback is 1.0.0 if VERSION file not present, or whatever is in VERSION
        # Since we didn't mock open("VERSION"), it might try to read real VERSION or fail if not present.
        # But initialize_database handles FileNotFoundError.
        conn.close()

    def test_get_current_version_from_db(self):
        database.initialize_database()
        version = database.get_current_version_from_db()
        self.assertIsNotNone(version)
        self.assertIsInstance(version, str)

    def test_update_version_in_db(self):
        database.initialize_database()
        new_version = "9.9.9"
        database.update_version_in_db(new_version)

        fetched_version = database.get_current_version_from_db()
        self.assertEqual(fetched_version, new_version)

    @patch("builtins.open", new_callable=unittest.mock.mock_open, read_data="2.0.0")
    def test_initialize_database_reads_version_file(self, mock_file):
        # Ensure db is fresh
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

        database.initialize_database()
        version = database.get_current_version_from_db()
        self.assertEqual(version, "2.0.0")

if __name__ == '__main__':
    unittest.main()
