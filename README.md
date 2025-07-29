# Atomic Tools Suite

A collection of specialized GTK4 applications for managing atomic/ostree systems. Each tool focuses on a specific aspect of system management with an intuitive, modern interface.

## 🛠️ The Tools

### 🔄 Atomic Rollback Tool
**Purpose**: Manage and restore system deployments with enhanced rollback capabilities

- View all system deployments with clear status indicators
- One-click rollback to any previous deployment
- Pin important deployments to prevent automatic cleanup
- Search and restore deployments from the last 90 days
- Similar functionality to bazzite-rollback-helper

### 🔀 Atomic Rebase Tool  
**Purpose**: Switch between different atomic OS images with ease

- Quick selection of popular images (Silverblue, Kinoite, Bazzite, Bluefin, Aurora)
- Support for all variants (NVIDIA, Developer editions, etc.)
- Custom image URL support for advanced users
- Automatic cleanup before rebasing to prevent errors
- Real-time progress tracking with detailed logs

### ⚙️ Atomic OS Manager
**Purpose**: Configure your system based on the current image with smart, contextual options

- Automatically detects your current OS image
- Provides image-specific configuration options:
  - **Bazzite**: Game mode toggle, GPU selection, branch selection
  - **Bluefin/Aurora**: Developer Experience (DX) mode, GPU options
  - **All Universal Blue**: System update integration with reboot prompts
- Single "Apply" button to execute all changes
- Smart UI that adapts to your system's capabilities

## 📥 Installation

### Download Release
```bash
# Download all three tools from the latest release
wget https://github.com/ULilBagel/ublue-rebase-tool/releases/latest/download/io.github.ublue.RollbackTool.flatpak
wget https://github.com/ULilBagel/ublue-rebase-tool/releases/latest/download/io.github.ublue.AtomicRebaseTool.flatpak
wget https://github.com/ULilBagel/ublue-rebase-tool/releases/latest/download/io.github.ublue.OSManager.flatpak

# Install the tools you need
flatpak install --user io.github.ublue.RollbackTool.flatpak
flatpak install --user io.github.ublue.AtomicRebaseTool.flatpak
flatpak install --user io.github.ublue.OSManager.flatpak
```

### Build from Source
```bash
# Prerequisites
flatpak install flathub org.gnome.Platform//47 org.gnome.Sdk//47

# Clone and build
git clone https://github.com/ULilBagel/ublue-rebase-tool.git
cd ublue-rebase-tool

# Build all tools
./build-all.sh

# Or build individually
./build-rollback.sh
./build-rebase.sh
./build-os-manager.sh
```

## 🚀 Usage

### Rollback Tool
```bash
flatpak run io.github.ublue.RollbackTool
```
Use when you need to revert system changes or restore a previous working state.

### Rebase Tool
```bash
flatpak run io.github.ublue.AtomicRebaseTool
```
Use when switching to a different atomic OS variant or distribution.

### OS Manager
```bash
flatpak run io.github.ublue.OSManager
```
Use to configure image-specific features and manage system updates.

## 📸 Screenshots

![Rollback Tool](screenshots/rollback-tool.png)
*Atomic Rollback Tool - Managing system deployments*

![Rebase Tool](screenshots/rebase-tool.png)
*Atomic Rebase Tool - Switching OS images*

![OS Manager](screenshots/os-manager.png)
*Atomic OS Manager - Image-specific configuration*

## 🔧 Requirements

- Atomic/ostree-based system:
  - Fedora Silverblue or Kinoite
  - Universal Blue variants (Bazzite, Bluefin, Aurora)
  - Any other ostree-based system
- Flatpak runtime
- GNOME 47 runtime

## 🔒 Security & Permissions

All tools run sandboxed with minimal required permissions:

- **Read-only access**: System information and configuration files
- **System operations**: Via D-Bus to rpm-ostree and systemd
- **No network access**: All operations are local
- **User confirmation**: All system modifications require explicit approval

## 📋 Supported Systems

### Fedora Atomic
- Silverblue (GNOME)
- Kinoite (KDE)
- Versions: 40, 41, Latest, Rawhide

### Universal Blue
- **Bazzite**: Gaming-focused with Steam Deck variants
- **Bluefin**: Developer-focused GNOME experience
- **Aurora**: Developer-focused KDE experience
- All variants: Standard, NVIDIA, Developer Experience (DX)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📄 License

GPL-3.0 - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- [Universal Blue](https://universal-blue.org/) team for the innovative OS images
- [Fedora Project](https://fedoraproject.org/) for Silverblue and Kinoite
- [GNOME](https://gnome.org/) project for GTK4 and libadwaita
- [Flatpak](https://flatpak.org/) team for the sandboxing technology