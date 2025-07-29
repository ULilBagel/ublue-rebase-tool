# Flatpak Build Instructions

This document provides instructions for building and distributing the Universal Blue Rebase Tool as a Flatpak.

## Prerequisites

Install the required tools:

```bash
# Fedora/Universal Blue
sudo dnf install flatpak flatpak-builder

# Ubuntu/Debian
sudo apt install flatpak flatpak-builder
```

## Building Locally

1. Run the build script:
   ```bash
   ./build-flatpak.sh
   ```

2. Install the built Flatpak:
   ```bash
   flatpak install --user ublue-rebase-tool.flatpak
   ```

3. Run the application:
   ```bash
   flatpak run io.github.ublue.RebaseTool
   ```

## Manifest Details

The Flatpak manifest (`io.github.ublue.RebaseTool.json`) includes:

- **Runtime**: GNOME 46 Platform
- **Permissions**:
  - Read-only access to host OS files (`/etc`, `/var/log`, `/proc`, `/sys`)
  - D-Bus access to rpm-ostree for system operations
  - PolicyKit access for elevated privileges
  - Wayland and X11 support
  - Portal access for desktop integration

## Testing

Before submitting to Flathub:

1. Test all functionality works in the Flatpak sandbox
2. Verify rpm-ostree operations work correctly
3. Check that dialogs and UI elements display properly
4. Ensure web content loads correctly

## Flathub Submission

To submit to Flathub:

1. **Prepare the source**:
   - Push code to a public git repository (GitHub/GitLab)
   - Create a release tag (e.g., `v1.0.0`)
   - Generate a source archive

2. **Update the manifest**:
   ```json
   "sources": [
     {
       "type": "archive",
       "url": "https://github.com/ublue-os/ublue-rebase-tool/archive/v1.0.0.tar.gz",
       "sha256": "YOUR_SHA256_HASH_HERE"
     }
   ]
   ```

3. **Submit to Flathub**:
   - Fork https://github.com/flathub/flathub
   - Create directory: `io.github.ublue.RebaseTool/`
   - Add your updated manifest
   - Submit pull request

4. **Review process**:
   - Flathub reviewers will check the manifest
   - Address any feedback or requested changes
   - Once approved, your app will be available on Flathub

## Security Considerations

The app requires elevated privileges to perform system operations:
- Uses PolicyKit for authentication
- Communicates with rpm-ostree D-Bus service
- All filesystem access is read-only except for app data

## Troubleshooting

### Common Issues

1. **D-Bus access denied**: Ensure the manifest includes all required D-Bus permissions
2. **rpm-ostree not found**: The app detects and handles non-ostree systems gracefully
3. **Web content not loading**: Check that web assets are correctly installed to `/app/share/ublue-image-manager/`

### Debug Commands

```bash
# Run with debug output
flatpak run --verbose --log-session-bus io.github.ublue.RebaseTool

# Check installed files
flatpak run --command=bash io.github.ublue.RebaseTool
ls -la /app/share/ublue-image-manager/

# Test D-Bus access
flatpak run --command=bash io.github.ublue.RebaseTool
busctl --user introspect org.projectatomic.rpmostree1
```

## Maintenance

When updating the application:
1. Update version in metainfo.xml
2. Add release notes to metainfo.xml
3. Update the manifest with new source URL/hash
4. Test thoroughly before release