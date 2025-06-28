"""
Tests for word navigation bugs reported by Tyler.

These tests reproduce the issues:
1. sayword reading from cursor to end of scrollback
2. nextword wrapping instead of saying 'right' at boundary
"""
import unittest
from unittest import mock
import pyte

# Import tdsr directly
import tdsr.tdsr as tdsr
from tests.test_helpers import create_test_screen


class TestWordNavigationBugs(unittest.TestCase):
    """Test word navigation bugs found in scrollback implementation."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a simple screen with known content
        self.screen = pyte.HistoryScreen(20, 3)  # Small 20x3 screen
        self.stream = pyte.Stream(self.screen)
        
        # Add content with words at boundaries
        lines = [
            "first word here",
            "second line text", 
            "third row end"
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
    def test_sayword_should_only_read_current_word(self, mock_say):
        """Test that sayword only reads the word at cursor, not to end of scrollback."""
        # Position cursor at "word" in first line
        tdsr.state.revy = 0
        tdsr.state.revx = 6  # Start of "word"
        
        # Say the word
        tdsr.sayword()
        
        # Should ONLY say "word", not read to end of scrollback
        mock_say.assert_called_once_with("word")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_at_last_word_of_line(self, mock_say):
        """Test sayword at the last word of a line."""
        # Position cursor at "here" in first line
        tdsr.state.revy = 0
        tdsr.state.revx = 11  # Start of "here"
        
        # Say the word
        tdsr.sayword()
        
        # Should only say "here"
        mock_say.assert_called_once_with("here")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_at_end_of_line_should_wrap(self, mock_say):
        """Test nextword at end of line should wrap to next line."""
        # Position cursor at "here" in first line
        tdsr.state.revy = 0
        tdsr.state.revx = 11  # Start of "here"
        
        # Move to next word
        tdsr.nextword()
        
        # Should move to "second" on next line and say it
        self.assertEqual(tdsr.state.revy, 1)
        self.assertEqual(tdsr.state.revx, 0)
        mock_say.assert_called_once_with("second")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_at_last_word_of_screen_should_say_right(self, mock_say):
        """Test nextword at last word of screen should say 'right'."""
        # Position cursor at "end" in last line
        tdsr.state.revy = 2
        tdsr.state.revx = 10  # Start of "end"
        
        # Move to next word
        tdsr.nextword()
        
        # Should stay at same position and say "right"
        self.assertEqual(tdsr.state.revy, 2)
        self.assertEqual(tdsr.state.revx, 10)
        mock_say.assert_any_call("right")
        # And then say the current word
        mock_say.assert_any_call("end")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_wrapping_behavior(self, mock_say):
        """Test the specific wrapping bug Tyler reported."""
        # Create a screen where last position has a space
        self.screen = pyte.HistoryScreen(10, 2)  # 10x2 screen
        self.stream = pyte.Stream(self.screen)
        
        # Add content that ends with a space at screen edge
        self.stream.feed("word ")  # 5 chars, space at position 4
        self.stream.feed("test")   # Continues on same line, wraps
        self.stream.feed("\r\n")
        self.stream.feed("next line")
        
        tdsr.screen = self.screen
        
        # Position at "word"
        tdsr.state.revy = 0
        tdsr.state.revx = 0
        
        # Move to next word - should handle the space at position 4 correctly
        tdsr.nextword()
        
        # This is where the bug might be - let's see what happens
        # It should either say "test" if it wraps, or handle the boundary correctly
        calls = mock_say.call_args_list
        # Should have said something sensible, not read to end of scrollback
        self.assertTrue(len(calls) > 0)
        self.assertTrue(len(calls) < 5)  # Shouldn't read everything


class TestWordBoundaryEdgeCases(unittest.TestCase):
    """Test edge cases for word navigation at boundaries."""
    
    def setUp(self):
        """Set up edge case scenarios."""
        self.screen = pyte.HistoryScreen(15, 2)  # 15x2 screen
        self.stream = pyte.Stream(self.screen)
        
        # Create edge case: word exactly at end of line
        self.stream.feed("short line end")  # Exactly 14 chars, "end" at columns 11-13
        self.stream.feed("\r\n")
        self.stream.feed("second line")
        
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_at_exact_line_end(self, mock_say):
        """Test sayword when word is exactly at line end."""
        # Position at "end" which ends at column 13 (0-based)
        tdsr.state.revy = 0
        tdsr.state.revx = 11
        
        tdsr.sayword()
        
        # Should only say "end", not continue reading
        mock_say.assert_called_once_with("end")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_from_exact_line_end(self, mock_say):
        """Test nextword from word at exact line end."""
        # Position at "end"
        tdsr.state.revy = 0
        tdsr.state.revx = 11
        
        tdsr.nextword()
        
        # Should move to next line's first word
        self.assertEqual(tdsr.state.revy, 1)
        self.assertEqual(tdsr.state.revx, 0)
        mock_say.assert_called_with("second")


if __name__ == '__main__':
    unittest.main()