"""
Test nextword wrapping bug that Tyler reported.
"""
import unittest
from unittest import mock
import pyte

import tdsr.tdsr as tdsr


class TestNextwordWrapBug(unittest.TestCase):
    """Test nextword incorrectly wrapping instead of saying 'right'."""
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_at_last_word_should_say_right(self, mock_say):
        """nextword at last word of screen should say 'right', not wrap."""
        # Create screen with simple content
        screen = pyte.HistoryScreen(20, 3)
        stream = pyte.Stream(screen)
        
        # Add some scrollback
        stream.feed("old line here\r\n")
        stream.feed("another old\r\n")
        
        # Current screen content
        stream.feed("first line\r\n")
        stream.feed("second line\r\n")
        stream.feed("last word")  # Last line with "last" and "word"
        
        tdsr.screen = screen
        tdsr.synth = mock.MagicMock()
        
        # Position at "word" (the very last word on screen)
        tdsr.state.revy = 2  # Last line
        tdsr.state.revx = 5  # Start of "word"
        
        # Call nextword - should NOT wrap to scrollback
        tdsr.nextword()
        
        # Should say "right" because we're at the last word
        calls = [call[0][0] for call in mock_say.call_args_list]
        print(f"DEBUG: nextword said: {calls}")
        
        self.assertIn("right", calls, "Should say 'right' at last word")
        
        # Position should remain at "word"
        self.assertEqual(tdsr.state.revy, 2)
        self.assertEqual(tdsr.state.revx, 5)
    
    @mock.patch('tdsr.tdsr.say')
    def test_nextword_wrapping_to_scrollback_bug(self, mock_say):
        """Show if nextword incorrectly wraps into scrollback."""
        # Create a screen where we're at the end
        screen = pyte.HistoryScreen(10, 2)
        stream = pyte.Stream(screen)
        
        # Scrollback
        stream.feed("history\r\n")
        
        # Current screen  
        stream.feed("test line\r\n")
        stream.feed("end word")  # Last line
        
        tdsr.screen = screen
        tdsr.synth = mock.MagicMock()
        
        # Position at "word" - the very last word
        tdsr.state.revy = 1
        tdsr.state.revx = 4
        
        # Try to go to next word
        original_y = tdsr.state.revy
        tdsr.nextword()
        
        # Should NOT have moved to a different line
        self.assertEqual(tdsr.state.revy, original_y, "Should not wrap to scrollback")
        
        # Should have said "right"
        calls = [call[0][0] for call in mock_say.call_args_list]
        self.assertIn("right", calls)


if __name__ == '__main__':
    unittest.main()