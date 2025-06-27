"""
Tests for Phase 3: Scrollback position indicators and user feedback.

These tests verify that users receive proper feedback about their position
in scrollback vs current screen for accessibility.
"""
import unittest
from unittest import mock
import pyte

# Import tdsr directly
import tdsr.tdsr as tdsr
from tests.test_helpers import create_test_screen


class TestScrollbackPositionIndicators(unittest.TestCase):
    """Test scrollback position indicators for user feedback."""
    
    def setUp(self):
        """Set up test environment with history."""
        # Create a HistoryScreen with content that creates scrollback
        self.screen = pyte.HistoryScreen(80, 3)
        self.stream = pyte.Stream(self.screen)
        
        # Add content that will create scrollback history
        lines = [
            "Old line 1", 
            "Old line 2",
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
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayline_no_position_spam(self, mock_say):
        """Test sayline doesn't spam position indicators on every line."""
        # sayline should just speak content, not position indicators
        tdsr.sayline(-1)
        mock_say.assert_called_once_with("Old line 2")
        
        # Test deeper scrollback line
        mock_say.reset_mock()
        tdsr.sayline(-2)
        mock_say.assert_called_once_with("Old line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayline_current_screen_no_indicator(self, mock_say):
        """Test sayline on current screen has no position indicator."""
        # Current screen lines should have no scrollback indicator
        tdsr.sayline(0)
        mock_say.assert_called_once_with("Current line 1")
        
        mock_say.reset_mock()
        tdsr.sayline(1)
        mock_say.assert_called_once_with("Current line 2")
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_entering_scrollback_announcement(self, mock_say):
        """Test prevline announces when entering scrollback."""
        # Start at current screen top
        tdsr.state.revy = 0
        
        # Go up into scrollback
        tdsr.prevline()
        
        # Should announce entering scrollback and speak the line
        self.assertEqual(tdsr.state.revy, -1)
        self.assertEqual(mock_say.call_count, 2)
        mock_say.assert_any_call("entering scrollback")
        mock_say.assert_any_call("Old line 2")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextline_exiting_scrollback_announcement(self, mock_say):
        """Test nextline announces when exiting scrollback to current screen."""
        # Start in scrollback
        tdsr.state.revy = -1
        
        # Go down to current screen
        tdsr.nextline()
        
        # Should announce returning to current screen
        self.assertEqual(tdsr.state.revy, 0)
        self.assertEqual(mock_say.call_count, 2)
        mock_say.assert_any_call("back to current screen")
        mock_say.assert_any_call("Current line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_scrollback_boundary_indicator(self, mock_say):
        """Test prevline at scrollback boundary says 'top of scrollback'."""
        # Start at oldest scrollback line
        tdsr.state.revy = -2
        
        # Try to go further back
        tdsr.prevline()
        
        # Should stay at boundary and announce top of scrollback
        self.assertEqual(tdsr.state.revy, -2)
        mock_say.assert_any_call("top of scrollback")
        mock_say.assert_any_call("Old line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextline_current_screen_boundary_indicator(self, mock_say):
        """Test nextline at current screen boundary says 'bottom of screen'."""
        # Start at bottom of current screen
        tdsr.state.revy = 2  # Bottom line (screen.lines - 1)
        
        # Try to go further down
        tdsr.nextline()
        
        # Should stay at bottom and announce bottom of screen
        self.assertEqual(tdsr.state.revy, 2)
        mock_say.assert_any_call("bottom of screen")
        mock_say.assert_any_call("Current line 3")


class TestScrollbackIndicatorsWithoutHistory(unittest.TestCase):
    """Test scrollback indicators when no history exists."""
    
    def setUp(self):
        """Set up test environment with no scrollback history."""
        self.screen = pyte.HistoryScreen(80, 3)
        self.stream = pyte.Stream(self.screen)
        
        # Add only current screen content (no scrollback)
        self.stream.feed("Only line 1\r\n")
        self.stream.feed("Only line 2\r\n")
        self.stream.feed("Only line 3")
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = 0
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_no_history_boundary_message(self, mock_say):
        """Test prevline with no history shows appropriate boundary message."""
        # Start at top of screen with no history
        tdsr.state.revy = 0
        
        # Try to go up
        tdsr.prevline()
        
        # Should stay at top and say "top of scrollback"
        self.assertEqual(tdsr.state.revy, 0)
        mock_say.assert_any_call("top of scrollback")
        mock_say.assert_any_call("Only line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayline_no_scrollback_context(self, mock_say):
        """Test sayline without scrollback history doesn't add position indicators."""
        # All lines should be treated as current screen
        tdsr.sayline(0)
        mock_say.assert_called_once_with("Only line 1")
        
        mock_say.reset_mock()
        tdsr.sayline(1)
        mock_say.assert_called_once_with("Only line 2")


class TestScrollbackIndicatorsEdgeCases(unittest.TestCase):
    """Test edge cases for scrollback indicators."""
    
    def setUp(self):
        """Set up test environment with minimal history."""
        self.screen = pyte.HistoryScreen(80, 2)  # Small screen
        self.stream = pyte.Stream(self.screen)
        
        # Create minimal scrollback
        lines = ["History line", "Current line 1", "Current line 2"]
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = 0
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.tdsr.say')
    def test_single_scrollback_line_no_spam(self, mock_say):
        """Test sayline doesn't spam position indicators even with minimal scrollback."""
        # Test the single scrollback line - should just speak content
        tdsr.sayline(-1)
        mock_say.assert_called_once_with("History line")
    
    @mock.patch('tdsr.tdsr.say')
    def test_scrollback_navigation_with_minimal_history(self, mock_say):
        """Test navigation announcements with minimal scrollback."""
        # Start at current screen
        tdsr.state.revy = 0
        
        # Enter scrollback (should announce)
        tdsr.prevline()
        self.assertEqual(mock_say.call_count, 2)
        mock_say.assert_any_call("entering scrollback")
        mock_say.assert_any_call("History line")
        
        # Try to go further back (should hit boundary)
        mock_say.reset_mock()
        tdsr.prevline()
        mock_say.assert_any_call("top of scrollback")
        
        # Return to current screen (should announce)
        mock_say.reset_mock()
        tdsr.nextline()
        mock_say.assert_any_call("back to current screen")


if __name__ == '__main__':
    unittest.main()