import unittest
from unittest.mock import MagicMock, patch
from rich.table import Table
from grit.ui import get_banner_layout, run_text_input
import sys

class TestUI(unittest.TestCase):
    def test_banner_layout(self):
        layout = get_banner_layout()
        self.assertIsInstance(layout, Table)

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_text_input_basic(self, mock_live, mock_get_key):
        # Simulate: type "hello", then Ctrl+D
        mock_get_key.side_effect = ['h', 'e', 'l', 'l', 'o', '\x04']
        
        result = run_text_input("Title")
        self.assertEqual(result, "hello")

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_text_input_multiline(self, mock_live, mock_get_key):
        # Simulate: type "line1", Enter, "line2", then Ctrl+D
        mock_get_key.side_effect = ['l', '1', '\r', 'l', '2', '\x04']
        
        result = run_text_input("Title")
        self.assertEqual(result, "l1\nl2")

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_text_input_backspace(self, mock_live, mock_get_key):
        # Simulate: type "abc", Backspace, then Ctrl+D
        mock_get_key.side_effect = ['a', 'b', 'c', '\x7f', '\x04']
        
        result = run_text_input("Title")
        self.assertEqual(result, "ab")

if __name__ == '__main__':
    unittest.main()
