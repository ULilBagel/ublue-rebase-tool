# Integration Testing Guide - UUPD Integration

## Overview
This guide provides step-by-step instructions for manually testing the uupd integration in the OS Manager tool.

## Prerequisites
- OS Manager application installed or running from source
- At least one update tool available (uupd, ujust, or ublue-update)
- System with pending updates (optional but recommended)

## Test Scenarios

### Test 1: Primary Tool Selection (uupd)
**Objective:** Verify uupd is selected as the primary update tool when available

1. **Setup:**
   - Ensure uupd is installed: `which uupd`
   - Launch OS Manager

2. **Steps:**
   - Click "Check for Updates" button
   - Observe the log output

3. **Expected Results:**
   - Log shows: "Found uupd"
   - Log shows: "Using uupd for system update..."
   - Update process begins with uupd

### Test 2: Fallback to ujust
**Objective:** Verify fallback to ujust when uupd is not available

1. **Setup:**
   - Temporarily rename uupd: `sudo mv /usr/sbin/uupd /usr/sbin/uupd.bak`
   - Ensure ujust is available: `which ujust`
   - Launch OS Manager

2. **Steps:**
   - Click "Check for Updates" button
   - Observe the log output

3. **Expected Results:**
   - Log shows: "uupd not found, checking next tool..."
   - Log shows: "Found ujust update"
   - Log shows: "Using ujust update for system update..."

4. **Cleanup:**
   - Restore uupd: `sudo mv /usr/sbin/uupd.bak /usr/sbin/uupd`

### Test 3: Fallback to ublue-update
**Objective:** Verify fallback to ublue-update when neither uupd nor ujust available

1. **Setup:**
   - Temporarily disable both tools (if present)
   - Ensure ublue-update is available
   - Launch OS Manager

2. **Steps:**
   - Click "Check for Updates" button
   - Observe the log output

3. **Expected Results:**
   - Log shows checking and not finding uupd and ujust
   - Log shows: "Found ublue-update"
   - Log shows: "Using ublue-update for system update..."

### Test 4: No Tools Available
**Objective:** Verify proper error handling when no update tools are available

1. **Setup:**
   - Temporarily disable all update tools
   - Launch OS Manager

2. **Steps:**
   - Click "Check for Updates" button
   - Observe the log output and UI

3. **Expected Results:**
   - Log shows all tools not found
   - Log shows: "✗ No update tool found (uupd, ujust, or ublue-update)"
   - Log shows: "Please ensure at least one update tool is installed on your system."
   - UI shows: "No update tool available"
   - Update button re-enables

### Test 5: Progress Tracking
**Objective:** Verify progress updates are displayed correctly

1. **Steps:**
   - Run update with any available tool
   - Observe progress bar and status messages

2. **Expected Results:**
   - Progress bar updates during download
   - Status messages reflect current operation:
     - "Checking for updates..."
     - "Downloading updates..."
     - "Installing updates..."
     - "Updating Flatpak applications..."
     - etc.

### Test 6: Reboot Prompt Detection
**Objective:** Verify reboot prompts are detected correctly

1. **Steps:**
   - Run update that stages changes
   - Wait for completion

2. **Expected Results:**
   - When reboot is required, log shows: "[Reboot prompt detected: '...' - showing action buttons]"
   - UI shows Reboot/Close/Back buttons
   - Cancel button is hidden

### Test 7: Cancellation
**Objective:** Verify update can be cancelled properly

1. **Steps:**
   - Start an update
   - Click Cancel button during the update

2. **Expected Results:**
   - Log shows: "⚠️ Cancelling operation..."
   - Update process terminates
   - UI shows: "Update cancelled"
   - Back button becomes visible

### Test 8: Full Update Flow
**Objective:** End-to-end test of complete update process

1. **Steps:**
   - Click "Check for Updates"
   - Let update run to completion
   - If updates staged, click "Reboot Now"

2. **Expected Results:**
   - Update completes successfully
   - Appropriate buttons shown based on update result
   - System reboots if requested

## Logging Test Results

For each test, record:
- Test scenario name
- Date/time of test
- System configuration (which tools installed)
- Pass/Fail status
- Any unexpected behavior
- Screenshots of key states (optional)

## Performance Observations

Note any performance characteristics:
- Update tool selection speed
- Progress update frequency
- UI responsiveness during updates
- Memory usage (if monitoring)

## Edge Cases to Test

1. **Interrupted Network:**
   - Start update, disconnect network
   - Verify error handling

2. **Tool Crashes:**
   - If update tool crashes, verify cleanup

3. **Rapid Button Clicks:**
   - Click Update multiple times quickly
   - Verify no duplicate processes

4. **View Switching:**
   - Switch views during update
   - Return to progress view
   - Verify state consistency

## Regression Testing

After all tests pass, verify existing functionality still works:
- Configuration changes (GPU, branch, etc.)
- Rebase operations
- UI elements respond correctly
- No visual glitches or layout issues

## Test Completion Checklist

- [ ] All primary test scenarios pass
- [ ] Fallback behavior works correctly
- [ ] Error messages are clear and helpful
- [ ] Progress tracking is accurate
- [ ] Cancellation works properly
- [ ] No regressions in existing features
- [ ] Performance is acceptable
- [ ] UI remains responsive

## Notes
- Always backup your system before testing system updates
- Test in a VM or non-critical system when possible
- Document any issues found for debugging