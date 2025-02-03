import unittest
from unittest.mock import MagicMock, patch
from rich.table import Table
from grit.ui import get_banner_layout, run_text_input, run_selection_menu
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

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_selection_menu(self, mock_live, mock_get_key):
        # Simulate: Down, then Enter
        mock_get_key.side_effect = ['\x1b[B', '\r']
        
        options = ["Opt1", "Opt2", "Opt3"]
        choice, idx = run_selection_menu("Title", options)
        
        self.assertEqual(choice, "Opt2")
        self.assertEqual(idx, 1)

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_text_input_with_timeout(self, mock_live, mock_get_key):
        # Simulate: timeout twice (None), type "a", then Ctrl+D
        mock_get_key.side_effect = [None, None, 'a', '\x04']
        
        result = run_text_input("Title")
        self.assertEqual(result, "a")
        # Ensure get_key was called with timeout
        self.assertEqual(mock_get_key.call_args[1].get('timeout'), 0.1)

    @patch('grit.ui.get_key')
    @patch('grit.ui.Live')
    def test_selection_menu_abort(self, mock_live, mock_get_key):
        # Simulate: Q
        mock_get_key.side_effect = ['q']
        
        options = ["Opt1", "Opt2"]
        choice, idx = run_selection_menu("Title", options)
        
        self.assertIsNone(choice)
        self.assertEqual(idx, -1)

    @patch('sys.stdout.write')
    def test_reset_terminal_title(self, mock_write):
        import grit.ui
        from grit.ui import reset_terminal_title
        with patch('sys.stdout.isatty', return_value=True):
            # We need to set _title_pushed to True so reset_terminal_title actually writes to stdout
            grit.ui._title_pushed = True
            reset_terminal_title()
            mock_write.assert_called_with("\033[23;0t")

    @patch('grit.ui.Live')
    @patch('random.random', return_value=0.9)
    @patch('random.choice', return_value='✨')
    @patch('time.sleep', return_value=None)
    def test_victory_animation(self, mock_sleep, mock_choice, mock_random, mock_live):
        from grit.ui import show_victory_animation
        
        # Setup Live mock to work as context manager
        mock_live_instance = mock_live.return_value
        mock_live_instance.__enter__.return_value = mock_live_instance
        
        show_victory_animation()
        
        self.assertTrue(mock_live.called)

if __name__ == '__main__':
    unittest.main()
