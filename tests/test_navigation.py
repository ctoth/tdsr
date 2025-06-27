"""
Navigation tests for TDSR.

These tests verify the core navigation functions work correctly
before and after implementing scrollback functionality.
"""
import unittest
from unittest import mock

from tests.test_helpers import create_test_screen, get_screen_line_text, import_tdsr_as_module

# Import tdsr module using centralized helper
tdsr = import_tdsr_as_module()


class TestLineNavigation(unittest.TestCase):
    """Test line-based navigation functions."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a test screen with known content
        self.screen = create_test_screen(80, 5, [
            "Line 0: First line",
            "Line 1: Second line", 
            "Line 2: Third line",
            "Line 3: Fourth line",
            "Line 4: Fifth line"
        ])
        
        # Replace the global screen object in tdsr with our test screen
        tdsr.screen = self.screen
        
        # Reset state for consistent testing
        tdsr.state.revy = 2  # Start at middle line
        tdsr.state.revx = 0
    
    @mock.patch('tdsr.say')
    def test_prevline_normal_movement(self, mock_say):
        """Test prevline moves up one line and speaks correctly."""
        # Starting at line 2, move to line 1
        tdsr.prevline()
        
        self.assertEqual(tdsr.state.revy, 1)
        mock_say.assert_called_once_with("Line 1: Second line")
    
    @mock.patch('tdsr.say') 
    def test_prevline_at_top_boundary(self, mock_say):
        """Test prevline at top of screen stays at top and says 'top'."""
        tdsr.state.revy = 0  # Set to top line
        
        tdsr.prevline()
        
        self.assertEqual(tdsr.state.revy, 0)  # Should stay at 0
        mock_say.assert_called_once_with("top")
    
    @mock.patch('tdsr.say')
    def test_nextline_normal_movement(self, mock_say):
        """Test nextline moves down one line and speaks correctly."""
        # Starting at line 2, move to line 3
        tdsr.nextline()
        
        self.assertEqual(tdsr.state.revy, 3)
        mock_say.assert_called_once_with("Line 3: Fourth line")
    
    @mock.patch('tdsr.say')
    def test_nextline_at_bottom_boundary(self, mock_say):
        """Test nextline at bottom of screen stays at bottom and says 'bottom'."""
        tdsr.state.revy = 4  # Set to bottom line (screen.lines - 1)
        
        tdsr.nextline()
        
        self.assertEqual(tdsr.state.revy, 4)  # Should stay at 4
        mock_say.assert_called_once_with("bottom")


class TestCharacterNavigation(unittest.TestCase):
    """Test character-based navigation functions."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.screen = create_test_screen(80, 3, [
            "Hello world test",
            "Another line here", 
            "Final test line"
        ])
        
        tdsr.screen = self.screen
        tdsr.state.revy = 0
        tdsr.state.revx = 5  # Start at 'w' in "Hello world"
    
    @mock.patch('tdsr.say_character')
    def test_prevchar_normal_movement(self, mock_say_char):
        """Test prevchar moves left one character."""
        tdsr.prevchar()
        
        self.assertEqual(tdsr.state.revx, 4)  # Should move from 5 to 4
        # Should say the character at the new position
        char_at_pos = self.screen.buffer[tdsr.state.revy][tdsr.state.revx].data
        mock_say_char.assert_called_once_with(char_at_pos)
    
    @mock.patch('tdsr.say')
    def test_prevchar_at_left_boundary(self, mock_say):
        """Test prevchar at left edge says 'left' and stays put."""
        tdsr.state.revx = 0  # Set to leftmost position
        
        tdsr.prevchar()
        
        self.assertEqual(tdsr.state.revx, 0)  # Should stay at 0
        mock_say.assert_called_once_with("left")
    
    @mock.patch('tdsr.say_character')
    def test_nextchar_normal_movement(self, mock_say_char):
        """Test nextchar moves right one character."""
        tdsr.nextchar()
        
        self.assertEqual(tdsr.state.revx, 6)  # Should move from 5 to 6
        char_at_pos = self.screen.buffer[tdsr.state.revy][tdsr.state.revx].data
        mock_say_char.assert_called_once_with(char_at_pos)
    
    @mock.patch('tdsr.say')
    def test_nextchar_at_right_boundary(self, mock_say):
        """Test nextchar at right edge says 'right' and stays put."""
        tdsr.state.revx = 79  # Set to rightmost position
        
        tdsr.nextchar()
        
        self.assertEqual(tdsr.state.revx, 79)  # Should stay at 79
        mock_say.assert_called_once_with("right")


class TestWordNavigation(unittest.TestCase):
    """Test word-based navigation functions."""
    
    def setUp(self):
        """Set up test environment before each test."""
        self.screen = create_test_screen(80, 3, [
            "word1 word2 word3",
            "another test line",
            "final words here"
        ])
        
        tdsr.screen = self.screen
        tdsr.state.revy = 0
        tdsr.state.revx = 0  # Start at beginning
    
    @mock.patch('tdsr.say')
    def test_sayword_at_beginning(self, mock_say):
        """Test sayword speaks the current word."""
        tdsr.sayword()
        
        mock_say.assert_called_once_with("word1")
    
    @mock.patch('tdsr.say')
    def test_sayword_spell_mode(self, mock_say):
        """Test sayword with spelling enabled."""
        tdsr.sayword(spell=True)
        
        # Should call say with each character separated by spaces
        mock_say.assert_called_once_with("w o r d 1")
    
    @mock.patch('tdsr.say')
    def test_nextword_movement(self, mock_say):
        """Test nextword moves to next word and speaks it."""
        tdsr.nextword()
        
        # Should move to "word2" and speak it
        mock_say.assert_called_once_with("word2")
    
    @mock.patch('tdsr.say')
    def test_prevword_movement(self, mock_say):
        """Test prevword moves to previous word."""
        # Start at word2 position
        tdsr.state.revx = 6  # Position at start of "word2"
        
        tdsr.prevword()
        
        # Should move back to "word1" and speak it
        mock_say.assert_called_once_with("word1")


if __name__ == '__main__':
    unittest.main()