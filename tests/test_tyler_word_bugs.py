"""
Tests that specifically reproduce Tyler's reported word navigation bugs.
"""
import unittest
from unittest import mock
import pyte

import tdsr.tdsr as tdsr


class TestTylerWordBugs(unittest.TestCase):
    """Test the exact bugs Tyler reported."""
    
    def setUp(self):
        """Set up test with scrollback content."""
        # Create a screen with scrollback history
        self.screen = pyte.HistoryScreen(20, 3)
        self.stream = pyte.Stream(self.screen)
        
        # Add content that will create scrollback
        lines = [
            "history line one",
            "history line two",
            "history line three",
            "current line one", 
            "current line two",
            "current line three"
        ]
        
        for i, line in enumerate(lines):
            if i > 0:
                self.stream.feed("\r\n")
            self.stream.feed(line)
        
        # Set up tdsr globals
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_reads_too_much_across_lines(self, mock_say):
        """Test Tyler's bug: sayword reads from cursor to end of scrollback."""
        # Position at "line" in "current line one"
        tdsr.state.revy = 0
        tdsr.state.revx = 8  # Start of "line"
        
        # Call sayword
        tdsr.sayword()
        
        # BUG: If sayword reads across line boundaries, it might read:
        # "line" + wrapping to next line and continuing...
        # It should ONLY read "line"
        mock_say.assert_called_once_with("line")
        
        # But Tyler says it reads to end of scrollback, so let's check
        # if the word is longer than expected
        call_args = mock_say.call_args[0][0]
        self.assertEqual(call_args, "line")
        self.assertLess(len(call_args), 10, "Word should not be reading multiple lines!")
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_at_end_of_line_bug(self, mock_say):
        """Test sayword when word is at end of line - might wrap."""
        # Position at "three" in "current line three" (last word)
        tdsr.state.revy = 2
        tdsr.state.revx = 13  # Start of "three"
        
        # This word is at position 13-17, and screen width is 20
        # So it ends at column 17, not quite at the edge
        tdsr.sayword()
        
        # Should only say "three"
        mock_say.assert_called_once_with("three")
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_wrapping_instead_of_right(self, mock_say):
        """Test Tyler's bug: nextword wraps instead of saying 'right'."""
        # Position at last word of last line
        tdsr.state.revy = 2  # Last line on screen
        tdsr.state.revx = 13  # "three"
        
        # Try to go to next word
        tdsr.nextword()
        
        # Should say "right" and stay in place since we're at the last word
        calls = [call[0][0] for call in mock_say.call_args_list]
        self.assertIn("right", calls)
        
        # Position should not have wrapped to scrollback or anywhere else
        self.assertEqual(tdsr.state.revy, 2)
        self.assertEqual(tdsr.state.revx, 13)
    
    @mock.patch('tdsr.tdsr.say')  
    def test_word_at_exact_screen_edge(self, mock_say):
        """Test behavior when word ends exactly at screen edge."""
        # Create specific scenario
        self.screen = pyte.HistoryScreen(10, 2)  # Narrow screen
        self.stream = pyte.Stream(self.screen)
        
        # Create a word that ends exactly at column 9 (0-based)
        self.stream.feed("test word")  # "word" is at columns 5-8
        self.stream.feed("\r\n")
        self.stream.feed("next line")
        
        tdsr.screen = self.screen
        tdsr.state.revy = 0
        tdsr.state.revx = 5  # Position at "word"
        
        # Say the word - should not wrap to next line
        tdsr.sayword()
        
        mock_say.assert_called_once_with("word")
        
        # Now test nextword from here
        mock_say.reset_mock()
        tdsr.state.revx = 5  # Reset position
        tdsr.nextword()
        
        # Should move to "next" on the next line
        self.assertEqual(tdsr.state.revy, 1)
        self.assertEqual(tdsr.state.revx, 0)
        mock_say.assert_called_with("next")


class TestWordCrossingLineBoundary(unittest.TestCase):
    """Test the specific case where sayword might read across lines."""
    
    def setUp(self):
        """Create a scenario where move_nextchar would wrap."""
        self.screen = pyte.HistoryScreen(10, 3)  # Very narrow
        self.stream = pyte.Stream(self.screen)
        
        # Create text where words might span lines due to wrapping
        self.stream.feed("short")
        self.stream.feed("longerword")  # This might wrap
        self.stream.feed("\r\n")
        self.stream.feed("next text")
        
        tdsr.screen = self.screen
        tdsr.synth = mock.MagicMock()
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_should_not_cross_lines(self, mock_say):
        """Ensure sayword stops at line boundaries."""
        # If "longerword" wrapped, we need to handle it
        # Position at start of wrapped content
        tdsr.state.revy = 0
        tdsr.state.revx = 5  # After "short"
        
        tdsr.sayword()
        
        # Get what was actually said
        if mock_say.called:
            said = mock_say.call_args[0][0]
            # Should be a single word, not multiple lines of content
            self.assertNotIn('\n', said)
            self.assertLess(len(said), 20)  # Reasonable word length


if __name__ == '__main__':
    unittest.main()