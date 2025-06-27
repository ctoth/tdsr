"""
Tests for copy functionality with scrollback support.

These tests ensure that copying text works correctly whether the text
is on the current screen or in scrollback history.
"""
import unittest
from unittest import mock
import pyte

# Import tdsr directly
import tdsr.tdsr as tdsr
from tests.test_helpers import create_test_screen


class TestCopyWithScrollback(unittest.TestCase):
    """Test copy functionality works with scrollback history."""
    
    def setUp(self):
        """Set up test environment with scrollback history."""
        # Create a HistoryScreen with content that creates scrollback
        self.screen = pyte.HistoryScreen(80, 3)
        self.stream = pyte.Stream(self.screen)
        
        # Add content that will create scrollback history
        lines = [
            "History line 1 content",
            "History line 2 content", 
            "Current line 1",
            "Current line 2",
            "Current line 3"
        ]
        
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = 0
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_current_screen_line(self, mock_copy_to_clip):
        """Test copying a line from current screen."""
        # Copy current line 1 (y=0)
        tdsr.copy_text(0, 0, 0, 15)  # Copy "Current line 1"
        
        mock_copy_to_clip.assert_called_once_with("Current line 1")
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_scrollback_line(self, mock_copy_to_clip):
        """Test copying a line from scrollback history."""
        # Copy scrollback line (-1 = most recent history)
        tdsr.copy_text(-1, 0, -1, 22)  # Copy "History line 2 content"
        
        mock_copy_to_clip.assert_called_once_with("History line 2 content")
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_partial_scrollback_line(self, mock_copy_to_clip):
        """Test copying part of a scrollback line."""
        # Copy "line 2" from "History line 2 content"
        tdsr.copy_text(-1, 8, -1, 13)
        
        mock_copy_to_clip.assert_called_once_with("line 2")
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_multiline_current_screen(self, mock_copy_to_clip):
        """Test copying multiple lines from current screen."""
        # Copy from "Current line 1" to "Current line 2"
        tdsr.copy_text(0, 0, 1, 15)
        
        expected = "Current line 1\nCurrent line 2"
        mock_copy_to_clip.assert_called_once_with(expected)
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_multiline_scrollback(self, mock_copy_to_clip):
        """Test copying multiple lines from scrollback."""
        # Copy from oldest to most recent history line
        tdsr.copy_text(-2, 0, -1, 22)
        
        expected = "History line 1 content\nHistory line 2 content"
        mock_copy_to_clip.assert_called_once_with(expected)
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_spanning_scrollback_and_current(self, mock_copy_to_clip):
        """Test copying from scrollback history to current screen."""
        # Copy from scrollback line to current screen
        tdsr.copy_text(-1, 8, 0, 7)  # "line 2 content" to "Current"
        
        expected = "line 2 content\nCurrent "
        mock_copy_to_clip.assert_called_once_with(expected)
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_coordinates_reversed(self, mock_copy_to_clip):
        """Test copy works when start/end coordinates are reversed."""
        # Copy with end coordinates before start coordinates
        tdsr.copy_text(0, 15, -1, 0)  # Should be same as (-1, 0, 0, 15)
        
        expected = "History line 2 content\nCurrent line 1"
        mock_copy_to_clip.assert_called_once_with(expected)
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_single_character(self, mock_copy_to_clip):
        """Test copying a single character from scrollback."""
        # Copy just the "H" from "History line 1 content"
        tdsr.copy_text(-2, 0, -2, 0)
        
        mock_copy_to_clip.assert_called_once_with("H")
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    def test_copy_empty_range(self, mock_copy_to_clip):
        """Test copying when the range is effectively empty."""
        # Copy from beyond line length
        tdsr.copy_text(-1, 100, -1, 105)
        
        mock_copy_to_clip.assert_called_once_with("")


class TestCopyIntegrationWithNavigation(unittest.TestCase):
    """Test copy functionality integrated with navigation state."""
    
    def setUp(self):
        """Set up test environment with scrollback."""
        self.screen = pyte.HistoryScreen(80, 2)
        self.stream = pyte.Stream(self.screen)
        
        # Create minimal scrollback
        lines = ["Old text here", "Current line 1", "Current line 2"]
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.copy_x = None
        tdsr.state.copy_y = None
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    @mock.patch('tdsr.tdsr.say')
    def test_copy_line_from_scrollback_position(self, mock_say, mock_copy_to_clip):
        """Test copy_line works when cursor is in scrollback."""
        from tests.test_helpers import create_test_screen
        
        # Position cursor in scrollback
        tdsr.state.revy = -1  # In scrollback
        tdsr.state.revx = 0
        
        # Use CopyHandler to copy line
        handler = tdsr.CopyHandler()
        result = handler.copy_line()
        
        # Should copy the scrollback line
        mock_copy_to_clip.assert_called_once()
        # Verify it copied from virtual coordinates
        call_args = mock_copy_to_clip.call_args[0][0]
        self.assertIn("Old text here", call_args)
        
        # Should announce success and remove handler
        mock_say.assert_called_with("line")
        self.assertEqual(result, tdsr.KeyHandler.REMOVE)
    
    @mock.patch('tdsr.tdsr.copy_to_clip')
    @mock.patch('tdsr.tdsr.say')
    def test_clipboard_selection_across_scrollback_boundary(self, mock_say, mock_copy_to_clip):
        """Test clipboard selection that spans scrollback and current screen."""
        # Start selection in scrollback
        tdsr.state.revy = -1
        tdsr.state.revx = 4  # "text" in "Old text here"
        
        # Start clipboard selection
        tdsr.handle_clipboard()
        mock_say.assert_called_with("select")
        
        # Move to current screen and end selection
        tdsr.state.revy = 0
        tdsr.state.revx = 7  # "line" in "Current line 1"
        
        # End clipboard selection
        mock_say.reset_mock()
        tdsr.handle_clipboard()
        
        # Should copy from scrollback to current screen
        mock_copy_to_clip.assert_called_once()
        call_args = mock_copy_to_clip.call_args[0][0]
        self.assertIn("text here", call_args)
        self.assertIn("Current", call_args)
        
        mock_say.assert_called_with("copied")


if __name__ == '__main__':
    unittest.main()