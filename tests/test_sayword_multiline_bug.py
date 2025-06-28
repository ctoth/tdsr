"""
Test that demonstrates sayword reading across multiple lines.
"""
import unittest
from unittest import mock
import pyte

import tdsr.tdsr as tdsr


class TestSaywordMultilineBug(unittest.TestCase):
    """Demonstrate the actual bug where sayword reads multiple lines."""
    
    @mock.patch('tdsr.tdsr.say')
    def test_sayword_crosses_line_boundary(self, mock_say):
        """Show that sayword incorrectly reads across line boundaries."""
        # Create a screen where a word is at the end of a line
        screen = pyte.HistoryScreen(15, 3)  # 15 chars wide
        stream = pyte.Stream(screen)
        
        # Add text where "word" is at end of line and more text follows
        stream.feed("test line word")  # "word" ends at column 13 (0-indexed)
        stream.feed("\r\n")
        stream.feed("next line here")
        stream.feed("\r\n") 
        stream.feed("third line end")
        
        tdsr.screen = screen
        tdsr.synth = mock.MagicMock()
        
        # Position at "word" which is at the end of first line
        tdsr.state.revy = 0
        tdsr.state.revx = 10  # Start of "word"
        
        # Call sayword
        tdsr.sayword()
        
        # What SHOULD happen: say only "word"
        # What Tyler reports: reads to end of scrollback
        said = mock_say.call_args[0][0]
        print(f"DEBUG: sayword said: '{said}'")
        
        # If the bug exists, said might be "wordnextlineherelineend" or similar
        # because move_nextchar() at column 14 would wrap to next line
        self.assertEqual(said, "word", f"Expected 'word' but got '{said}'")
    
    @mock.patch('tdsr.tdsr.say')
    def test_demonstrate_multiline_reading(self, mock_say):
        """Explicitly show move_nextchar wrapping during word building."""
        screen = pyte.HistoryScreen(5, 4)  # Very narrow screen
        stream = pyte.Stream(screen)
        
        # Create scenario where word MUST span lines
        stream.feed("ab cd")  # Line 0: "ab cd"
        stream.feed("\r\n")
        stream.feed("ef gh")  # Line 1: "ef gh"  
        stream.feed("\r\n")
        stream.feed("ij kl")  # Line 2: "ij kl"
        
        tdsr.screen = screen
        tdsr.synth = mock.MagicMock()
        
        # Position at "cd" at end of first line
        tdsr.state.revy = 0
        tdsr.state.revx = 3  # "cd" starts at position 3
        
        # Trace through what sayword does:
        # 1. Saves position (3, 0)
        # 2. Moves back to find word start - already at start
        # 3. word = "c" (get_char)
        # 4. move_nextchar() - goes to position 4
        # 5. word += "d" 
        # 6. move_nextchar() - at column 4 (last column), so wraps to (0, 1)!
        # 7. get_char() = "e", not space, so word += "e"
        # 8. Continues reading...
        
        tdsr.sayword()
        
        said = mock_say.call_args[0][0]
        print(f"DEBUG: Word at end of narrow line said: '{said}'")
        
        # This will likely fail, showing the bug
        self.assertEqual(said, "cd", f"sayword should stop at line end but got '{said}'")


if __name__ == '__main__':
    unittest.main()