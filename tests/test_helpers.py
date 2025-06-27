"""
Test utilities and helpers for TDSR testing.
"""
import os
import sys
import importlib.util
import pyte


def import_tdsr_as_module():
    """
    Imports the 'tdsr' executable script as a Python module.

    This function handles the complexities of loading a non-.py file,
    ensuring that __file__ is set correctly so the script's internal
    path logic works as expected.

    It caches the imported module in sys.modules, so subsequent calls
    do not re-execute the script.
    """
    # 1. Check if already imported to avoid re-execution.
    if 'tdsr' in sys.modules:
        return sys.modules['tdsr']

    # 2. Define paths. This assumes test_helpers.py is in tests/
    #    and tdsr is in the parent directory.
    tests_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(tests_dir)
    tdsr_path = os.path.join(project_root, 'tdsr')

    if not os.path.exists(tdsr_path):
        raise FileNotFoundError(f"Could not find 'tdsr' executable at {tdsr_path}")

    # 3. Create a module spec from the file location.
    spec = importlib.util.spec_from_file_location('tdsr', tdsr_path)
    if spec is None:
        raise ImportError(f"Could not create module spec for {tdsr_path}")

    # 4. Create a new module based on the spec.
    tdsr_module = importlib.util.module_from_spec(spec)

    # 5. Add the module to sys.modules BEFORE execution.
    sys.modules['tdsr'] = tdsr_module

    # 6. Execute the module's code in its own namespace.
    spec.loader.exec_module(tdsr_module)

    return tdsr_module


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
        for line in content:
            stream.feed(line + "\r\n")
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