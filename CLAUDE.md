# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TDSR is a console-based screen reader for *nix systems (macOS, Linux, FreeBSD). It intercepts terminal output using a pseudo-terminal and provides speech feedback through text-to-speech engines. The main application is a single Python file (`tdsr`) that handles terminal emulation, key processing, and speech output.

## Core Architecture

- **Main executable**: `tdsr` - Python 3 script that creates a pty, runs terminal commands, and processes I/O
- **Speech backends**: 
  - `speechdispatcher` - Linux backend using Speech Dispatcher Python bindings
  - `mac` - macOS backend using AVFoundation/PyObjC
- **Terminal emulation**: Uses `pyte` library for VT100/ANSI terminal emulation
- **Configuration**: Uses `configparser` with config file at `~/.tdsr.cfg`

## Key Components

### State Management (`State` class)
- Maintains review cursor position (`revx`, `revy`)
- Handles configuration, key handlers, and speech settings
- Manages delayed functions and silence states

### Screen Management (`MyScreen` class)
- Extends `pyte.Screen` for terminal emulation
- Intercepts drawing operations to generate speech output
- Handles screen modes, scrolling, and buffer management

### Key Handling (`KeyHandler` classes)
- `KeyHandler` - Base class for processing keyboard input
- `ConfigHandler` - Configuration menu navigation
- `CopyHandler` - Text selection and copying
- `BufferHandler` - Text input for configuration values

### Plugin System
- Plugins can be loaded from `plugins/` directory
- Configured via `[plugins]` and `[commands]` sections in config
- Plugins must export `parse_output(lines)` function

## Development Commands

### Installation
```bash
pip3 install -Ur requirements.txt
```

### Running
```bash
./tdsr                    # Start with default shell
./tdsr --debug           # Debug mode with logging to tdsr.log
./tdsr program args      # Run specific program
```

### Configuration
- Config file: `~/.tdsr.cfg`
- Template: `tdsr.cfg.dist`
- Alt+c enters configuration mode

## Key Mappings

The application uses Alt-based key combinations for navigation:
- `alt u/i/o` - previous/current/next line
- `alt j/k/l` - previous/current/next word  
- `alt m/,/.` - previous/current/next character
- `alt c` - configuration mode
- `alt q` - toggle quiet mode
- `alt r` - clipboard selection
- `alt v` - copy mode

## Dependencies

- **Python 3** - Core runtime
- **pyte==0.8.1** - Terminal emulation
- **pyobjc** - macOS speech support (Darwin only)
- **wcwidth** - Character width calculation
- **speechd** - Speech Dispatcher bindings (Linux)

## Platform-Specific Notes

### macOS
- Uses AVFoundation for speech synthesis
- Requires PyObjC bindings
- Terminal.app: Enable "Use Option as Meta key"

### Linux  
- Uses Speech Dispatcher for TTS
- Supports both X11 (xclip) and Wayland (wl-copy) for clipboard
- Requires Speech Dispatcher Python bindings

## Testing
No formal test suite exists. Testing is primarily manual through usage scenarios.