# Universal Blue Rebase Tool - Feature Requirements

## Project Overview
A modern GTK4/libadwaita application for managing Universal Blue custom images, following Universal Blue development best practices and community standards.

## Codebase Analysis Summary

### Existing Components to Leverage:
- **GTK4/libadwaita UI Framework**: Already implemented with proper window management, toasts, and responsive design
- **WebKit Integration**: Hybrid UI approach with web-based interface for enhanced interactivity
- **Portal-First Security Model**: XDG Desktop Portal integration already in place
- **rpm-ostree D-Bus Integration**: System status monitoring via D-Bus already functional
- **UBlueImageAPI Class**: Backend API structure for system operations
- **Guidance Pattern**: Existing implementation follows UB pattern of providing instructions rather than direct modification

### Architecture Patterns:
- Directory structure follows Universal Blue standards (src/, data/, docs/, tests/)
- Flatpak manifest with minimal permissions model
- JavaScript bridge for WebView communication
- Threading support for async operations

## Requirements

### Requirement 1: System Status Display
**User Story:** As a Universal Blue user, I want to see my current system deployment status, so that I understand which image variant and version I'm running.

#### Acceptance Criteria
1. WHEN the application starts THEN the system SHALL display the current rpm-ostree deployment status
2. IF the system is not running rpm-ostree THEN the application SHALL display a demo mode indicator
3. WHEN the status is displayed THEN it SHALL show the image name, version, and deployment ID
4. IF the current deployment is a Universal Blue image THEN the system SHALL indicate this with a special badge

### Requirement 2: Image Variant Selection
**User Story:** As a Universal Blue user, I want to browse and select from available Universal Blue image variants, so that I can choose the best variant for my needs.

#### Acceptance Criteria
1. WHEN viewing available images THEN the system SHALL display official Universal Blue variants (Bluefin, Aurora, Bazzite, Silverblue)
2. IF an image is selected THEN the system SHALL display detailed information about that variant
3. WHEN hovering over an image THEN the system SHALL show a tooltip with key features
4. IF the user is already on a selected variant THEN the system SHALL indicate this visually

### Requirement 3: Rebase Execution with Confirmation
**User Story:** As a Universal Blue user, I want to select from the image list that has been provided to me and have the system execute the commands on my behalf with a confirmation prompt prior.

#### Acceptance Criteria
1. WHEN a user selects a different image variant THEN the system SHALL display a confirmation dialog with the exact commands to be executed
2. IF the user confirms the operation THEN the system SHALL execute the rpm-ostree rebase commands directly
3. WHEN the confirmation dialog is shown THEN it SHALL include safety warnings for data backup and system restart requirements
4. IF the current system is not rpm-ostree based THEN the system SHALL disable the execution option and show an informational message
5. WHEN executing commands THEN the system SHALL show real-time progress and output
6. IF the operation requires elevated privileges THEN the system SHALL use the appropriate portal or polkit authentication

### Requirement 4: Command History Tracking
**User Story:** As a Universal Blue user, I want to view my command history, so that I can reference previous operations and learn from them.

#### Acceptance Criteria
1. WHEN a command is generated THEN the system SHALL store it in a local history
2. IF viewing history THEN the system SHALL display commands with timestamps
3. WHEN selecting a historical command THEN the system SHALL allow copying to clipboard
4. IF history exceeds 50 entries THEN the system SHALL automatically prune oldest entries

### Requirement 5: Portal-Based Clipboard Integration
**User Story:** As a Universal Blue user, I want to easily copy generated commands to my clipboard, so that I can paste them into a terminal.

#### Acceptance Criteria
1. WHEN clicking a copy button THEN the system SHALL use XDG Desktop Portal for clipboard access
2. IF clipboard access is denied THEN the system SHALL show an error toast
3. WHEN a command is copied THEN the system SHALL display a success toast notification
4. IF the portal is unavailable THEN the system SHALL fallback to displaying a dialog with the command

### Requirement 6: System Compatibility Checking
**User Story:** As a Universal Blue user, I want the application to verify my system compatibility, so that I only see relevant options.

#### Acceptance Criteria
1. WHEN the application starts THEN it SHALL check for rpm-ostree availability
2. IF rpm-ostree is not available THEN the system SHALL operate in demo/educational mode
3. WHEN in demo mode THEN all operations SHALL be clearly marked as simulated
4. IF running on a Universal Blue system THEN the system SHALL enable advanced features

### Requirement 7: Responsive Adaptive UI
**User Story:** As a Universal Blue user, I want the application to adapt to different screen sizes, so that I can use it on various devices.

#### Acceptance Criteria
1. WHEN the window is resized THEN the UI SHALL adapt using libadwaita responsive patterns
2. IF the window width is below 600px THEN the system SHALL switch to mobile layout
3. WHEN in mobile layout THEN all functionality SHALL remain accessible
4. IF screen reader is detected THEN the system SHALL provide appropriate accessibility labels

### Requirement 8: Deployment Rollback Management
**User Story:** As a Universal Blue user, I want to be able to view all the rollback options available to me in my current image and select from the list to have the system execute on my behalf with the confirmation prompt prior.

#### Acceptance Criteria
1. WHEN viewing system status THEN the system SHALL display all available deployments from rpm-ostree status
2. IF multiple deployments exist THEN the system SHALL show them in a list with version, date, and pinned status
3. WHEN a user selects a previous deployment THEN the system SHALL display a confirmation dialog with the rollback command
4. IF the user confirms the rollback THEN the system SHALL execute the rpm-ostree rollback or deployment selection command
5. WHEN showing deployments THEN the system SHALL clearly mark the current booted deployment
6. IF a deployment is pinned THEN the system SHALL indicate this with a visual indicator
7. WHEN executing rollback THEN the system SHALL show real-time progress and inform about required system restart

## Technical Constraints
- Must run within Flatpak sandbox with minimal permissions
- Must follow Universal Blue guidance pattern (no direct system modification)
- Must use existing GTK4/libadwaita/WebKit stack
- Must maintain compatibility with GNOME Platform 46
- Must support both real rpm-ostree systems and demo mode

## Security Requirements
- All system operations must go through XDG Desktop Portals
- No direct filesystem writes outside of application data directory
- Read-only access to system configuration
- User must explicitly copy and execute commands in their own terminal

