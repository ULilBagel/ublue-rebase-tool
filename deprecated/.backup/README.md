# Universal Blue Image Manager

A modern GTK4/libadwaita application for managing Universal Blue custom images, built following Universal Blue development best practices and community standards.

## 🎯 Universal Blue Best Practices Implementation

This application demonstrates complete compliance with Universal Blue development standards:

### Architecture Compliance
- ✅ **Directory Structure**: Proper UB-compliant structure (`src/`, `data/`, `docs/`, `tests/`)
- ✅ **libadwaita Integration**: Modern GTK4/libadwaita widgets (AdwApplicationWindow, AdwHeaderBar, AdwToastOverlay)
- ✅ **Portal-First Security**: XDG Desktop Portal integration with minimal permissions
- ✅ **Guidance Pattern**: Follows UB guidance approach instead of direct system modification

### Security Model
- ✅ **Read-only Filesystem**: `--filesystem=host-os:ro` instead of full host access
- ✅ **Portal Integration**: Uses portals before requesting specific permissions  
- ✅ **No Direct Modification**: Provides instructions rather than direct rpm-ostree calls
- ✅ **Flatpak Sandbox**: Proper isolation with minimal privilege escalation

### Development Standards
- ✅ **GitHub Actions CI/CD**: Official flatpak-github-actions workflow
- ✅ **Comprehensive Testing**: Multi-level test suite validation
- ✅ **Community Standards**: Follows UB code style and practices
- ✅ **Container-First Development**: Supports Distrobox workflows

## 🚀 Features

- **Real System Integration** - Direct rpm-ostree status monitoring via D-Bus
- **Guidance-Based Operations** - Follows UB patterns for safe system management  
- **Modern libadwaita Interface** - Adaptive design with proper HIG compliance
- **Portal-Based Security** - Uses XDG Desktop Portals following UB standards
- **Universal Blue Optimized** - Built specifically for UB image variants
- **Hybrid GTK/WebKit UI** - Best of both native and web technologies

## 🛠️ Quick Start

### Prerequisites
```bash
# On Ubuntu/Debian
sudo apt install flatpak flatpak-builder python3-gi python3-gi-cairo \
                 gir1.2-gtk-4.0 gir1.2-adwaita-1 gir1.2-webkit-6.0

# Add Flathub
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo

# Install GNOME Platform 46
flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46
```

### Build and Install
```bash
# Run comprehensive tests
./test.sh

# Build Flatpak
./build.sh

# Run application
flatpak run io.github.ublue.RebaseTool
```

## 🏗️ Architecture

### Universal Blue Directory Structure
```
src/                    # Application source code
├── portal/            # XDG Desktop Portal integration
├── dbus/              # D-Bus service communication  
├── ui/                # GTK4/libadwaita interface components
├── monitoring/        # System monitoring and status display
├── config/            # Configuration management
└── utils/             # Utility functions and helpers

data/                  # Application data
├── web/               # Web interface for hybrid UI
├── icons/             # Application icons
└── metainfo/          # AppStream metadata

docs/                  # Documentation
tests/                 # Test suite
.github/workflows/     # CI/CD automation
```

### Technology Stack
- **GTK4 + libadwaita** - Modern GNOME application framework
- **WebKit** - Hybrid web interface (included in GNOME Platform)
- **Python 3** - Application logic and system integration
- **XDG Desktop Portals** - Secure system operation interfaces
- **rpm-ostree D-Bus** - System status monitoring
- **Flatpak** - Sandboxed application packaging

### Universal Blue Integration

#### Supported Image Variants
- **Bluefin** - Developer-focused GNOME desktop (`ghcr.io/ublue-os/bluefin:latest`)
- **Aurora** - Polished KDE Plasma experience (`ghcr.io/ublue-os/aurora:latest`)
- **Bazzite** - Gaming-optimized desktop (`ghcr.io/ublue-os/bazzite:latest`)
- **Silverblue** - Clean GNOME base (`ghcr.io/ublue-os/silverblue-main:latest`)

#### Guidance Pattern Implementation
Following Universal Blue best practices, this application provides guidance rather than direct system modification:

1. **System Status Monitoring** - Real-time rpm-ostree status via D-Bus
2. **Instruction Generation** - Provides step-by-step terminal commands
3. **Safety Validation** - Warns about operations requiring privileges
4. **User Empowerment** - Educates users about their system

## 🧪 Testing

The application includes comprehensive testing:

```bash
# Run full test suite
./test.sh

# Test specific components
python3 -c "
import sys
sys.path.insert(0, 'src')
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw
print('✅ GTK4/libadwaita integration working')
"

# Validate manifest
python3 -c "import json; print('✅ Manifest valid:', json.load(open('io.github.ublue.RebaseTool.json'))['app-id'])"
```

## 🤝 Contributing

This project follows Universal Blue community standards:

1. **Brutal Scope Management** - Reject unnecessary complexity
2. **Automation First** - Leverage GitHub Actions extensively  
3. **Long-term Sustainability** - Focus on maintainable solutions
4. **Community Integration** - Engage with Universal Blue maintainers

### Development Environment
```bash
# Create development container (recommended)
distrobox create --name gui-dev --image fedora:latest
distrobox enter gui-dev
sudo dnf install -y gtk4-devel libadwaita-devel meson ninja-build
```

## 📋 Implementation Details

### Flatpak Permissions (UB-Compliant)
```json
{
  "finish-args": [
    "--filesystem=host-os:ro",           // Read-only OS access
    "--filesystem=host-etc:ro",          // Read-only config access
    "--talk-name=org.projectatomic.rpmostree1",  // rpm-ostree D-Bus
    "--talk-name=org.freedesktop.portal.Desktop" // Portal access
  ]
}
```

### Security Model
- **Flatpak Sandbox**: Base isolation layer
- **Portal Authentication**: Flows for system operations
- **Permission Validation**: Before executing system commands
- **User Confirmation**: For sensitive operations
- **Audit Logging**: For security-relevant actions

## 📚 Documentation

- [Universal Blue Development Guide](https://universal-blue.org/guide/)
- [GTK4 Documentation](https://docs.gtk.org/gtk4/)
- [libadwaita Documentation](https://gnome.pages.gitlab.gnome.org/libadwaita/)
- [Flatpak Documentation](https://docs.flatpak.org/)

## 📄 License

GPL-3.0+ - Following Universal Blue project standards

## 🔗 Links

- [Universal Blue](https://github.com/universal-blue)
- [Flatpak on Flathub](https://flathub.org/)
- [GNOME Development](https://developer.gnome.org/)

Built with ❤️ for the Universal Blue community.
