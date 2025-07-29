# Universal Blue Rebase Tool - Implementation Plan

## Task Overview
This implementation plan breaks down the Universal Blue Rebase Tool feature into atomic, executable coding tasks. The approach prioritizes extending existing components and following established patterns in the codebase.

## Tasks

- [x] 1. Create CommandExecutor service for safe command execution
  - Create `src/command_executor.py` extending existing threading patterns
  - Implement `execute_with_progress()` method using subprocess with list arguments
  - Add polkit authentication handling via D-Bus
  - Write unit tests mocking subprocess calls
  - _Requirements: 3.2, 3.6_
  - _Leverage: src/ublue-image-manager.py (threading patterns), existing D-Bus integration_

- [x] 2. Create DeploymentManager service for rpm-ostree deployments
  - Create `src/deployment_manager.py` extending existing rpm-ostree status parsing
  - Implement `get_all_deployments()` parsing full deployment list
  - Add `generate_rollback_command()` for deployment selection
  - Create Deployment data class with proper typing
  - Write tests for various rpm-ostree status formats
  - _Requirements: 8.1, 8.2, 8.4_
  - _Leverage: src/ublue-image-manager.py:get_system_status() parsing logic_

- [x] 3. Implement ConfirmationDialog using libadwaita
  - Create `src/ui/confirmation_dialog.py` using Adw.MessageDialog
  - Implement rebase confirmation with command display and warnings
  - Add rollback confirmation variant with deployment info
  - Style using existing libadwaita patterns
  - Test dialog responses and cancellation
  - _Requirements: 3.1, 3.3, 8.3_
  - _Leverage: Existing Adw.ToastOverlay usage patterns_

- [x] 4. Create ProgressTracker for real-time output display
  - Create `src/progress_tracker.py` for command output streaming
  - Implement JavaScript injection for web UI updates
  - Add line buffering and formatting for terminal output
  - Create progress UI component in web interface
  - Test with mock command outputs
  - _Requirements: 3.5, 8.7_
  - _Leverage: src/ublue-image-manager.py:execute_js() method, WebKit bridge_

- [x] 5. Extend UBlueImageAPI with execution methods
  - Add `execute_rebase()` method to UBlueImageAPI class
  - Add `execute_rollback()` method for deployment selection
  - Add `get_deployments()` method returning all deployments
  - Integrate CommandExecutor and DeploymentManager
  - Update error handling for execution scenarios
  - _Requirements: 3.2, 8.4_
  - _Leverage: src/ublue-image-manager.py:UBlueImageAPI class structure_

- [x] 6. Update WebKit JavaScript bridge for new operations
  - Extend `inject_api_bridge()` with executeRebase and executeRollback methods
  - Add getDeployments method to JavaScript API
  - Update `on_script_message()` handler for new methods
  - Test bridge communication with mock calls
  - _Requirements: 3.1, 8.1_
  - _Leverage: src/ublue-image-manager.py:inject_api_bridge() existing bridge_

- [x] 7. Create HistoryManager for command tracking
  - Create `src/history_manager.py` using GLib user data directory
  - Implement JSON-based storage with automatic pruning
  - Add methods for storing and retrieving history entries
  - Create HistoryEntry data class
  - Write tests for storage limits and pruning logic
  - _Requirements: 4.1, 4.2, 4.4_
  - _Leverage: Application data directory patterns, existing JSON handling_

- [x] 8. Update web interface for rebase execution
  - Modify `data/web/index.html` to add Execute buttons for images
  - Add confirmation dialog trigger on Execute click
  - Implement progress display area for command output
  - Add visual indicators for currently installed variant
  - Test responsive behavior on different screen sizes
  - _Requirements: 2.1, 2.4, 3.1_
  - _Leverage: data/web/index.html existing UI structure and styling_

- [x] 9. Implement deployment list UI in web interface
  - Add deployments section to `data/web/index.html`
  - Create deployment cards showing version, date, status
  - Add rollback buttons for each deployment
  - Implement visual indicators for booted/pinned deployments
  - Style consistently with existing UI components
  - _Requirements: 8.1, 8.2, 8.5, 8.6_
  - _Leverage: data/web/index.html card and panel patterns_

- [x] 10. Add command history UI section
  - Create history panel in web interface
  - Implement history list with timestamps and commands
  - Add copy-to-clipboard functionality for history items
  - Create clear visual distinction for success/failure
  - Test clipboard integration via portal
  - _Requirements: 4.2, 4.3, 5.1_
  - _Leverage: Existing clipboard handling patterns_

- [x] 11. Update sidebar for execution mode
  - Modify sidebar buttons from "Guide" to "Execute" mode
  - Add mode toggle or settings for guide vs execute
  - Update button callbacks to trigger confirmation dialogs
  - Ensure demo mode shows appropriate warnings
  - _Requirements: 3.1, 6.3_
  - _Leverage: src/ublue-image-manager.py:create_sidebar() structure_

- [x] 12. Implement error handling and recovery
  - Add error toast notifications for all failure scenarios
  - Implement network error detection and user guidance
  - Add authentication failure handling with retry
  - Create fallback for non-rpm-ostree systems
  - Write tests for each error scenario
  - _Requirements: 3.4, 6.2, 6.3_
  - _Leverage: Existing Adw.ToastOverlay for notifications_

- [x] 13. Add system compatibility checking enhancements
  - Enhance startup compatibility check with more detail
  - Add visual indicators for demo vs real mode
  - Disable execution features appropriately in demo mode
  - Add informational messages for incompatible systems
  - _Requirements: 6.1, 6.2, 6.3, 6.4_
  - _Leverage: src/ublue-image-manager.py:get_system_status() demo mode logic_

- [x] 14. Implement security validations
  - Add image URL validation against allowed registries
  - Implement command sanitization before execution
  - Add audit logging for all executed commands
  - Ensure no shell injection vulnerabilities
  - Write security-focused unit tests
  - _Requirements: Security Requirements_
  - _Leverage: Existing security patterns in codebase_

- [x] 15. Create comprehensive test suite
  - Write unit tests for all new components
  - Add integration tests for full execution flow
  - Create UI tests for dialog interactions
  - Test error scenarios and recovery paths
  - Ensure all requirements have test coverage
  - _Requirements: All requirements_
  - _Leverage: Existing test patterns and utilities_