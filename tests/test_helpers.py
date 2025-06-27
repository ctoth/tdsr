"""
Test utilities and helpers for TDSR testing.
"""
import os
import sys
import importlib.util
import pyte


# No longer needed - TDSR is now a proper package!


def create_test_screen(columns=80, lines=24, content=None):
    """Creates a predictable screen for testing.
    
    Args:
        columns: Screen width (default 80)
        lines: Screen height (default 24)
        content: List of strings to populate screen with, or None for default content
        
    Returns:
        pyte.Screen instance with predictable content
    """
    screen = pyte.Screen(columns, lines)
    stream = pyte.Stream(screen)
    
    if content:
        for i, line in enumerate(content):
            if i > 0:
                stream.feed("\r\n")
            stream.feed(line)
    else:
        # Default test content
        stream.feed("Line 1: Test content\r\n")
        stream.feed("Line 2: More test data\r\n") 
        stream.feed("Line 3: Final line")
    
    return screen


def create_test_screen_with_cursor(columns=80, lines=24, cursor_x=0, cursor_y=0, content=None):
    """Creates a test screen with cursor at specific position.
    
    Args:
        columns: Screen width
        lines: Screen height  
        cursor_x: Cursor column position
        cursor_y: Cursor row position
        content: List of strings for screen content
        
    Returns:
        pyte.Screen instance with cursor at specified position
    """
    screen = create_test_screen(columns, lines, content)
    stream = pyte.Stream(screen)
    
    # Move cursor to specified position (1-based coordinates for escape sequence)
    stream.feed(f"\x1b[{cursor_y + 1};{cursor_x + 1}H")
    
    return screen


def get_screen_line_text(screen, line_number):
    """Extract text content from a specific line of the screen.
    
    Args:
        screen: pyte.Screen instance
        line_number: 0-based line number
        
    Returns:
        String content of the line, stripped of trailing whitespace
    """
    if 0 <= line_number < screen.lines:
        line_chars = [screen.buffer[line_number][x].data for x in range(screen.columns)]
        return "".join(line_chars).rstrip()
    return ""