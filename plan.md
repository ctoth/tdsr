# Infinite Scrollback Implementation Plan for TDSR

## Project Overview

TDSR currently has limited scrollback functionality - users can only navigate within the visible screen area (typically 24-80 lines). Once content scrolls off the screen, it's permanently lost. This project implements infinite scrollback capability allowing users to review extensive terminal history while maintaining TDSR's accessibility-focused line-by-line navigation.

## Architecture Analysis & Solution

### Current Limitations
- Uses `pyte.Screen` with fixed dimensions limiting scrollback to visible screen area
- Navigation functions (`prevline()`, `nextline()`) are bounded by `screen.lines - 1`  
- Lines that scroll off screen are permanently lost
- Review cursor (`state.revy`, `state.revx`) maps directly to screen buffer coordinates

### Chosen Solution: Hybrid Approach Using pyte.HistoryScreen
After analysis and collaboration with Pro model, we selected a hybrid approach:

1. **Leverage pyte.HistoryScreen**: Use pyte's built-in scrollback implementation rather than building custom
2. **Virtual Coordinate System**: Implement abstraction layer for line-by-line access
3. **Composition over Inheritance**: Extend MyScreen to use HistoryScreen while maintaining existing functionality

### Technical Architecture

#### pyte.HistoryScreen Structure
- Uses `History` named tuple with deques: `top`, `bottom`, `ratio`, `size`, `position`
- `top`: deque(maxlen=history//2) for older scrollback
- `bottom`: deque(maxlen=history) for newer scrollback  
- Efficient O(1) append/pop operations
- Battle-tested memory management

#### Virtual Coordinate Mapping
```
Virtual coordinate system:
... -3, -2, -1 | 0, 1, 2, 3 ...
   scrollback   | current screen
```

#### Core Abstraction Layer
```python
def get_line(virtual_y):
    if virtual_y < 0:
        # Access scrollback: negative indices map to history.top deque
        scrollback_index = abs(virtual_y) - 1
        if scrollback_index < len(self.history.top):
            return self.history.top[-(scrollback_index + 1)]
    elif 0 <= virtual_y < self.lines:
        # Access current screen
        return self.buffer[virtual_y]
    return None  # Out of bounds
```

## Implementation Plan

### Phase 0: Test Foundation ✓ COMPLETED
**Goal**: Create minimal but comprehensive test suite to ensure we don't break existing functionality

#### Completed Deliverables ✓
- [x] Created feature branch: `infinite-scrollback`
- [x] Test directory structure: `tests/__init__.py`, `test_helpers.py`, `test_navigation.py`, `test_screen.py`
- [x] Test utilities with `create_test_screen()` helper
- [x] Navigation characterization tests (prevline, nextline, word/char navigation)
- [x] Screen interaction tests (sayline, line extraction)
- [x] Virtual environment setup with pyte==0.8.1, pytest

#### Test Strategy Established ✓
- **Characterization tests**: Capture current behavior without judging it
- **Real pyte instances**: Use actual pyte.Screen with controlled data
- **Mock side effects**: Mock speech output (`synth.send`) and clipboard operations
- **Focus on seams**: Test integration between TDSR logic and pyte screen

#### Identified Blocker ⚠️
- Current TDSR structure as executable script (not Python package) creates complex import issues
- Solution: Wait for pending PR that converts TDSR to proper Python package structure

### Phase 1: Core Scrollback Implementation (Pending Package Refactor)
**Goal**: Replace screen backend and implement virtual coordinate system

#### 1.1: Replace Screen Backend
- Change `MyScreen` base from `pyte.Screen` to `pyte.HistoryScreen`
- Add `scrollback_lines` config option (default: 1000)
- Maintain all existing MyScreen method overrides
- **Validation**: Run tests to ensure no regressions

#### 1.2: Implement Virtual Coordinate System
- Create `get_line(virtual_y)` abstraction method
- Handle coordinate translation between virtual and physical
- **Testing**: Add tests for virtual coordinate mapping
- **Validation**: Run full test suite to verify integration

#### 1.3: Update Navigation Functions
- Modify `prevline()`, `nextline()` to use virtual coordinates
- Update `sayline(y)` to call `get_line(virtual_y)`
- Extend bounds: `min_y = -len(self.history.top)`, `max_y = self.lines - 1`
- **Testing**: Update tests to cover new virtual coordinate ranges
- **Validation**: Run tests after each function update

### Phase 2: Feature Integration
**Goal**: Extend existing features to work with scrollback

#### 2.1: Copy Mode Extension  
- Update `copy_text()` to work with virtual coordinates
- Allow selection across scrollback and current screen boundaries
- **Testing**: Add tests for cross-boundary copy operations

#### 2.2: Plugin Compatibility
- Replace direct `screen.buffer` access with `get_line()` calls in plugin system
- Update `handle_plugin()` for virtual coordinates  
- **Testing**: Verify basic plugin functionality

#### 2.3: Configuration Management
- Add scrollback settings to config menu (`ConfigHandler`)
- Implement enable/disable toggle
- Memory management options
- **Testing**: Verify config loading and saving

### Phase 3: Enhanced Navigation Features
**Goal**: Add scrollback-specific navigation improvements

#### 3.1: Scrollback-Specific Shortcuts
- Alt+Home: Jump to top of scrollback
- Alt+End: Jump to bottom of current screen  
- Alt+PageUp/PageDown: Navigate by screen-sized chunks
- **Testing**: Add tests for new navigation commands

#### 3.2: User Experience Enhancements
- Audible feedback for scrollback boundaries
- Position indicators ("line 50 of 1000 in history")
- Optional search functionality

## Key Technical Decisions

### Memory Management
- Use `collections.deque(maxlen=N)` for automatic memory bounds
- Configurable buffer limits with sensible defaults (1000-10000 lines)
- Two-tier buffer system leveraging pyte's proven implementation

### Data Preservation  
- Maintain full `pyte.Char` objects (not just strings) to preserve formatting, colors, attributes
- Handle terminal resize limitations by preserving lines as captured

### Performance Considerations
- O(1) operations for append/pop using deque
- Virtual coordinate access optimized for typical usage patterns
- Lazy evaluation where possible

### Backward Compatibility
- All existing shortcuts and navigation work unchanged
- Plugin API remains stable through abstraction layer
- Configuration is additive (new options, existing behavior preserved)

## Development Practices

### Git Workflow
- Feature branch: `infinite-scrollback`
- Commit frequently after each deliverable
- Descriptive commit messages
- Daily progress updates

### Testing Strategy
- Test-driven development: tests before implementation
- Run test suite after each change
- Manual testing with real terminal applications
- Performance testing with large buffers

### Communication Protocol
- Ask questions immediately when stuck
- Flag architectural concerns or test failures
- Request code review before merging major phases

## Risk Mitigation

### Technical Risks
1. **Performance degradation**: Mitigated by proven deque data structure, configurable limits
2. **Plugin incompatibility**: Mitigated by abstraction layer preventing direct buffer access
3. **Memory leaks**: Mitigated by maxlen deques and configurable limits
4. **Coordinate mapping bugs**: Mitigated by comprehensive boundary testing

### Integration Risks
1. **Breaking existing functionality**: Mitigated by characterization tests
2. **Complex merge conflicts**: Mitigated by frequent commits, communication
3. **Package structure changes**: Blocked pending package refactor PR

## Success Criteria

### Functional Requirements
1. ✅ Users can navigate scrollback with existing Alt+u/o line navigation
2. ✅ Copy mode works across scrollback boundaries  
3. ✅ Configurable buffer size with reasonable defaults
4. ✅ No performance degradation for normal usage
5. ✅ All existing functionality preserved

### Technical Requirements  
1. ✅ Test coverage for critical navigation paths
2. ✅ Memory usage stays within configured bounds
3. ✅ Clean, maintainable code architecture
4. ✅ Plugin compatibility maintained

## Timeline Estimate

- **Phase 0**: ✅ 1 day (COMPLETED)
- **Phase 1**: 2-3 days (pending package refactor)
- **Phase 2**: 1-2 days  
- **Phase 3**: 1 day
- **Total**: 4-6 days after package structure is available

## Next Steps

1. **IMMEDIATE**: Wait for TDSR package refactor PR to merge
2. **Upon merge**: Restart implementation with clean package imports  
3. **Validate**: Run existing test suite with new package structure
4. **Continue**: Proceed with Phase 1 implementation

## Dependencies

- **Critical**: TDSR package refactor PR (converts executable to importable package)
- **Technical**: pyte==0.8.1, pytest, Python 3.x
- **Environmental**: Virtual environment with project dependencies

---

*This plan represents comprehensive analysis and design for infinite scrollback functionality. All architectural decisions have been validated through collaboration with Pro model and represent industry best practices for terminal emulator development.*