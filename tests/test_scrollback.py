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
        # Should announce entering scrollback and speak the line with position
        self.assertEqual(mock_say.call_count, 2)
        mock_say.assert_any_call("entering scrollback")
        mock_say.assert_any_call("scrollback line 1: History line 3")
    
    @mock.patch('tdsr.tdsr.say')
    def test_prevline_scrollback_boundary(self, mock_say):
        """Test prevline stops at beginning of history."""
        # Start at the oldest history line
        tdsr.state.revy = -3  # Oldest history line
        
        # Try to go further back
        tdsr.prevline()
        
        # Should stay at oldest line and say "top of scrollback"
        self.assertEqual(tdsr.state.revy, -3)
        mock_say.assert_any_call("top of scrollback")
        mock_say.assert_any_call("scrollback line 3: History line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextline_from_scrollback(self, mock_say):
        """Test nextline can navigate from scrollback to current screen."""
        # Start in scrollback
        tdsr.state.revy = -1
        
        # Go down one line - should move to current screen
        tdsr.nextline()
        
        # Should now be at y=0 (current screen)
        self.assertEqual(tdsr.state.revy, 0)
        # Should announce returning to current screen and speak the line
        self.assertEqual(mock_say.call_count, 2)
        mock_say.assert_any_call("back to current screen")
        mock_say.assert_any_call("Current line 1")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayline_with_scrollback(self, mock_say):
        """Test sayline works with virtual coordinates."""
        # Test saying a line from scrollback (includes position indicator)
        tdsr.sayline(-2)
        mock_say.assert_called_once_with("scrollback line 2: History line 2")
        
        # Reset mock and test current screen (no position indicator)
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
        
        # Try to go up - should stay at 0 and say "top of scrollback"
        tdsr.prevline()
        
        self.assertEqual(tdsr.state.revy, 0)
        mock_say.assert_any_call("top of scrollback")
        mock_say.assert_any_call("Only line 1")
    
    def test_get_line_no_history(self):
        """Test get_line when there's no scrollback history."""
        # Should return empty for negative coordinates
        line = tdsr.get_line(-1)
        self.assertEqual(line, "")
        
        # Should work normally for current screen
        line = tdsr.get_line(0)
        self.assertEqual(line, "Only line 1")


class TestScrollbackCharacterNavigation(unittest.TestCase):
    """Test character navigation in scrollback history."""
    
    def setUp(self):
        """Set up test environment with history."""
        self.screen = pyte.HistoryScreen(80, 3)
        self.stream = pyte.Stream(self.screen)
        
        # Create content with scrollback
        lines = [
            "history word1 word2",
            "another line here",
            "current line 1",
            "current line 2", 
            "current line 3"
        ]
        
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = -2  # Start in scrollback
        tdsr.state.revx = 0
    
    def test_get_char_at_scrollback(self):
        """Test get_char_at function with scrollback coordinates."""
        # Test accessing characters in scrollback history
        char = tdsr.get_char_at(-2, 0)  # First char of oldest history line
        self.assertEqual(char, "h")  # "history word1 word2"
        
        char = tdsr.get_char_at(-2, 7)  # Space after "history"
        self.assertEqual(char, " ")
        
        char = tdsr.get_char_at(-1, 0)  # First char of recent history line
        self.assertEqual(char, "a")  # "another line here"
    
    def test_get_char_at_current_screen(self):
        """Test get_char_at function with current screen coordinates."""
        char = tdsr.get_char_at(0, 0)
        self.assertEqual(char, "c")  # "current line 1"
        
        char = tdsr.get_char_at(1, 8)
        self.assertEqual(char, "l")  # "current line 2"
    
    def test_get_char_at_invalid_coordinates(self):
        """Test get_char_at handles invalid coordinates."""
        # Invalid line coordinates
        char = tdsr.get_char_at(-10, 0)
        self.assertEqual(char, "")
        
        char = tdsr.get_char_at(10, 0)
        self.assertEqual(char, "")
        
        # Invalid column coordinates
        char = tdsr.get_char_at(0, -1)
        self.assertEqual(char, "")
        
        char = tdsr.get_char_at(0, 100)
        self.assertEqual(char, "")
    
    @mock.patch('tdsr.tdsr.say_character')
    def test_saychar_in_scrollback(self, mock_say_char):
        """Test saychar function works in scrollback."""
        # Say a character from scrollback
        tdsr.saychar(-2, 0)  # First char of "history word1 word2"
        mock_say_char.assert_called_once_with("h")
        
        # Say a character from current screen
        mock_say_char.reset_mock()
        tdsr.saychar(0, 0)  # First char of "current line 1"
        mock_say_char.assert_called_once_with("c")
    
    @mock.patch('tdsr.tdsr.say_character')
    def test_character_navigation_across_scrollback(self, mock_say_char):
        """Test character navigation moves correctly across scrollback boundaries."""
        # Start at beginning of scrollback line
        tdsr.state.revy = -2
        tdsr.state.revx = 0
        
        # Move right and verify character
        tdsr.nextchar()
        self.assertEqual(tdsr.state.revy, -2)
        self.assertEqual(tdsr.state.revx, 1)
        mock_say_char.assert_called_with("i")  # Second char of "history"
    
    def test_get_char_convenience_function(self):
        """Test get_char() convenience function with current state position."""
        # Set position in scrollback
        tdsr.state.revy = -2
        tdsr.state.revx = 7
        
        char = tdsr.get_char()
        self.assertEqual(char, " ")  # Space after "history"
        
        # Set position in current screen
        tdsr.state.revy = 0
        tdsr.state.revx = 0
        
        char = tdsr.get_char()
        self.assertEqual(char, "c")  # First char of "current line 1"


class TestScrollbackWordNavigation(unittest.TestCase):
    """Test word navigation in scrollback history."""
    
    def setUp(self):
        """Set up test environment with words in history."""
        self.screen = pyte.HistoryScreen(80, 3) 
        self.stream = pyte.Stream(self.screen)
        
        # Create content with clear word boundaries
        lines = [
            "first second third",  # Will be in history
            "alpha beta gamma",    # Will be in history
            "current words here",  # Current screen
            "more text content",   # Current screen
            "final line end"       # Current screen
        ]
        
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
        tdsr.state.revy = -2  # Start in scrollback
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_in_scrollback(self, mock_say):
        """Test sayword works correctly in scrollback history."""
        # Position at start of word in scrollback
        tdsr.state.revy = -2
        tdsr.state.revx = 0  # At "first"
        
        tdsr.sayword()
        mock_say.assert_called_once_with("first")
        
        # Position at middle of word in scrollback  
        mock_say.reset_mock()
        tdsr.state.revy = -2
        tdsr.state.revx = 2  # In middle of "first"
        
        tdsr.sayword()
        mock_say.assert_called_once_with("first")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_spell_in_scrollback(self, mock_say):
        """Test sayword with spelling in scrollback."""
        tdsr.state.revy = -1
        tdsr.state.revx = 0  # At "alpha"
        
        tdsr.sayword(spell=True)
        mock_say.assert_called_once_with("a l p h a", force_process_symbols=True)
    
    def test_move_prevchar_across_line_boundary_in_scrollback(self):
        """Test move_prevchar can cross line boundaries in scrollback."""
        # Start at beginning of a scrollback line
        tdsr.state.revy = -1
        tdsr.state.revx = 0
        
        # Move to previous character (should go to end of previous line)
        result = tdsr.move_prevchar()
        
        self.assertEqual(tdsr.state.revy, -2)  # Previous line
        self.assertEqual(tdsr.state.revx, 79)  # End of line
    
    def test_move_prevchar_at_history_boundary(self):
        """Test move_prevchar at very beginning of history."""
        # Start at very beginning of history
        tdsr.state.revy = -2
        tdsr.state.revx = 0
        
        # Try to move further back
        result = tdsr.move_prevchar()
        
        # Should return empty string and not move
        self.assertEqual(result, '')
        self.assertEqual(tdsr.state.revy, -2)
        self.assertEqual(tdsr.state.revx, 0)


if __name__ == '__main__':
    unittest.main()