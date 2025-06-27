"""
Scrollback functionality tests for TDSR.

These tests verify that the infinite scrollback feature works correctly
with the HistoryScreen implementation.
"""
import unittest
from unittest import mock
import pyte

# Import tdsr directly
import tdsr.tdsr as tdsr
from tests.test_helpers import create_test_screen


class TestScrollbackFunctionality(unittest.TestCase):
    """Test scrollback navigation and access."""
    
    def setUp(self):
        """Set up test environment with history."""
        # Create a HistoryScreen directly to test scrollback
        self.screen = pyte.HistoryScreen(80, 3)  # Small screen for testing
        self.stream = pyte.Stream(self.screen)
        
        # Simulate terminal content that will create history
        # Add more lines than screen height to force scrollback
        lines = [
            "History line 1",
            "History line 2", 
            "History line 3",
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
        tdsr.state.revy = 0  # Start at top of current screen
        tdsr.state.revx = 0
    
    def test_get_line_current_screen(self):
        """Test get_line function accesses current screen correctly."""
        # Test accessing current visible screen (y >= 0)
        line0 = tdsr.get_line(0)
        line1 = tdsr.get_line(1) 
        line2 = tdsr.get_line(2)
        
        # Should return current screen content
        self.assertEqual(line0, "Current line 1")
        self.assertEqual(line1, "Current line 2")
        self.assertEqual(line2, "Current line 3")
    
    def test_get_line_scrollback_history(self):
        """Test get_line function accesses scrollback history correctly."""
        # Test accessing scrollback history (y < 0)
        # -1 should be most recent history line
        line_neg1 = tdsr.get_line(-1)
        line_neg2 = tdsr.get_line(-2)
        line_neg3 = tdsr.get_line(-3)
        
        # Should return history content
        self.assertEqual(line_neg1, "History line 3")
        self.assertEqual(line_neg2, "History line 2")
        self.assertEqual(line_neg3, "History line 1")
    
    def test_get_line_invalid_coordinates(self):
        """Test get_line handles invalid coordinates gracefully."""
        # Test coordinates beyond available content
        empty_line = tdsr.get_line(-10)  # Way past history
        empty_line2 = tdsr.get_line(10)  # Beyond current screen
        
        self.assertEqual(empty_line, "")
        self.assertEqual(empty_line2, "")
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_scrollback_navigation(self, mock_say):
        """Test prevline can navigate into scrollback history."""
        # Start at top of current screen (y=0)
        tdsr.state.revy = 0
        
        # Go up one line - should enter scrollback
        tdsr.prevline()
        
        # Should now be at y=-1 (most recent history line)
        self.assertEqual(tdsr.state.revy, -1)
        mock_say.assert_called_once_with("History line 3")
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_scrollback_boundary(self, mock_say):
        """Test prevline stops at beginning of history."""
        # Start at the oldest history line
        tdsr.state.revy = -3  # Oldest history line
        
        # Try to go further back
        tdsr.prevline()
        
        # Should stay at oldest line and say "top"
        self.assertEqual(tdsr.state.revy, -3)
        mock_say.assert_any_call("top")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextline_from_scrollback(self, mock_say):
        """Test nextline can navigate from scrollback to current screen."""
        # Start in scrollback
        tdsr.state.revy = -1
        
        # Go down one line - should move to current screen
        tdsr.nextline()
        
        # Should now be at y=0 (current screen)
        self.assertEqual(tdsr.state.revy, 0)
        mock_say.assert_called_once_with("Current line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayline_with_scrollback(self, mock_say):
        """Test sayline works with virtual coordinates."""
        # Test saying a line from scrollback
        tdsr.sayline(-2)
        mock_say.assert_called_once_with("History line 2")
        
        # Reset mock and test current screen
        mock_say.reset_mock()
        tdsr.sayline(1)
        mock_say.assert_called_once_with("Current line 2")


class TestScrollbackEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions for scrollback."""
    
    def setUp(self):
        """Set up test environment with no history."""
        # Create screen with no scrollback history
        self.screen = pyte.HistoryScreen(80, 3)
        
        # Add only current screen content (no history)
        self.stream = pyte.Stream(self.screen)
        self.stream.feed("Only line 1\r\n")
        self.stream.feed("Only line 2\r\n") 
        self.stream.feed("Only line 3")
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = 0
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_no_history(self, mock_say):
        """Test prevline when there's no scrollback history."""
        # Start at top of screen
        tdsr.state.revy = 0
        
        # Try to go up - should stay at 0 and say "top"
        tdsr.prevline()
        
        self.assertEqual(tdsr.state.revy, 0)
        mock_say.assert_any_call("top")
    
    def test_get_line_no_history(self):
        """Test get_line when there's no scrollback history."""
        # Should return empty for negative coordinates
        line = tdsr.get_line(-1)
        self.assertEqual(line, "")
        
        # Should work normally for current screen
        line = tdsr.get_line(0)
        self.assertEqual(line, "Only line 1")


if __name__ == '__main__':
    unittest.main()