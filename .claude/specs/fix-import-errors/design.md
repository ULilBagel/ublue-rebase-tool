# Design - Fix Import Errors

## Overview
This design document outlines the technical approach to resolve import errors in the test suite caused by the hyphenated filename `ublue-image-manager.py` not matching the underscore-based import statements `ublue_image_manager`.

## Architecture Analysis

### Current State
```
src/
├── ublue-image-manager.py  (hyphenated - main application)
├── command_executor.py
├── deployment_manager.py
├── history_manager.py
├── progress_tracker.py
└── ui/
    └── confirmation_dialog.py

tests/
├── test_error_handling.py    (imports ublue_image_manager)
├── test_integration.py       (imports ublue_image_manager)
├── test_ui_components.py     (imports ublue_image_manager)
└── ... (other test files)
```

### Import Problem
- Python cannot import modules with hyphens in their names using standard import syntax
- `import ublue-image-manager` is invalid Python syntax
- Tests expect `from ublue_image_manager import ...`

## Design Decisions

### 1. Solution Approach: Create Import Bridge
**Decision**: Create a new file `src/ublue_image_manager.py` that acts as an import bridge

**Rationale**:
- Preserves the original hyphenated filename
- No changes needed to test files
- Follows Python import conventions
- Minimal code changes
- Clear and maintainable

**Alternatives Considered**:
- ❌ Rename main file: Breaks Universal Blue naming convention
- ❌ Modify all tests: Too many changes, error-prone
- ❌ Use importlib in each test: Complex, repetitive
- ❌ Symlink: Platform-dependent, git issues

### 2. Implementation Strategy
**Bridge Module Pattern**: Create a simple Python module that imports and re-exports all necessary classes

```python
# src/ublue_image_manager.py
"""
Import bridge for ublue-image-manager.py
Allows tests to import using Python-compliant module name
"""

# Import all classes from the hyphenated module
import importlib.util
import sys
from pathlib import Path

# Load the hyphenated module
module_path = Path(__file__).parent / "ublue-image-manager.py"
spec = importlib.util.spec_from_file_location("ublue_image_manager_impl", module_path)
module = importlib.util.module_from_spec(spec)
sys.modules["ublue_image_manager_impl"] = module
spec.loader.exec_module(module)

# Re-export all necessary classes
UBlueImageAPI = module.UBlueImageAPI
UBlueImageWindow = module.UBlueImageWindow
UBlueImageApplication = module.UBlueImageApplication

# Re-export any other needed symbols
__all__ = ["UBlueImageAPI", "UBlueImageWindow", "UBlueImageApplication"]
```

### 3. Module Loading Approach
**Dynamic Import**: Use importlib to load the hyphenated file

**Benefits**:
- Works with any Python 3.x version
- No filesystem tricks needed
- Clear intent in the code
- Handles module caching properly

## Component Design

### Bridge Module (`src/ublue_image_manager.py`)

**Purpose**: Provide a Python-compliant import interface to the hyphenated main module

**Responsibilities**:
1. Load the hyphenated module dynamically
2. Re-export all public classes
3. Maintain the same API surface
4. Handle any import errors gracefully

**Implementation Details**:
- Use `importlib.util` for dynamic loading
- Register in `sys.modules` to prevent reload
- Export all classes needed by tests
- Include proper module docstring

### Error Handling

**Import Failures**:
- If hyphenated file not found: Clear error message
- If classes missing: List what's expected vs found
- Maintain stack trace for debugging

## Testing Strategy

### Verification Steps
1. Run each affected test file individually
2. Verify import statements work
3. Check all 93 tests execute
4. Ensure no regression in other tests

### Test Commands
```bash
# Individual test files
python -m unittest tests.test_error_handling
python -m unittest tests.test_integration
python -m unittest tests.test_ui_components

# Full suite
python tests/run_all_tests.py
```

## Implementation Plan

### Phase 1: Create Bridge Module
1. Create `src/ublue_image_manager.py`
2. Implement dynamic import logic
3. Export required classes

### Phase 2: Verify Tests
1. Run affected test files
2. Verify imports succeed
3. Check test execution

### Phase 3: Full Validation
1. Run complete test suite
2. Verify all 93 tests run
3. Document any remaining issues

## Security Considerations

### Import Safety
- Only import from known local file
- No external module loading
- No exec() or eval() usage
- Clear module boundaries

## Maintenance

### Future Considerations
- Document why bridge exists
- Include in project documentation
- Consider gradual migration if needed
- Keep bridge minimal and focused

### Documentation
Include clear comments explaining:
- Why this bridge module exists
- What it imports and exports
- How to add new exports if needed

---

Do the design look good? If so, we can move on to creating the task breakdown.