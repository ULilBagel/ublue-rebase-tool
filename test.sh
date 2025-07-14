#!/bin/bash
set -e

echo "🧪 Universal Blue Image Manager - Test Suite"
echo "Testing Universal Blue best practices implementation..."

# Test 1: Python imports
echo "1. Testing Python imports..."
python3 -c "
try:
    import gi
    gi.require_version('Gtk', '4.0')
    gi.require_version('Adw', '1')
    gi.require_version('WebKit', '6.0')
    from gi.repository import Gtk, Adw, WebKit, GLib, Gio
    print('✅ All GTK/libadwaita imports successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    exit(1)
"

# Test 2: Directory structure
echo "2. Testing Universal Blue directory structure..."
required_dirs=("src" "data/web" "data/icons" "data/metainfo" "docs" "tests" ".github/workflows")
for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir exists"
    else
        echo "❌ $dir missing"
        exit(1)
    fi
done

# Test 3: Required files
echo "3. Testing required files..."
required_files=("io.github.ublue.RebaseTool.json" "src/ublue-image-manager.py" "data/ublue-image-manager.desktop" "data/metainfo/io.github.ublue.RebaseTool.metainfo.xml" "data/icons/io.github.ublue.RebaseTool.svg" "data/web/index.html")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file exists"
    else
        echo "❌ $file missing"
        exit(1)
    fi
done

# Test 4: Flatpak manifest validation
echo "4. Testing Flatpak manifest..."
if python3 -c "import json; json.load(open('io.github.ublue.RebaseTool.json'))" 2>/dev/null; then
    echo "✅ Flatpak manifest is valid JSON"
else
    echo "❌ Flatpak manifest is invalid JSON"
    exit(1)
fi

# Check for UB-required permissions
ub_permissions=("--filesystem=host-os:ro" "--talk-name=org.projectatomic.rpmostree1" "--talk-name=org.freedesktop.portal.Desktop")
for perm in "${ub_permissions[@]}"; do
    if grep -q "$perm" io.github.ublue.RebaseTool.json; then
        echo "✅ Found required permission: $perm"
    else
        echo "❌ Missing required permission: $perm"
        exit(1)
    fi
done

# Test 5: Application syntax
echo "5. Testing Python application syntax..."
if python3 -m py_compile src/ublue-image-manager.py; then
    echo "✅ Python application syntax is valid"
else
    echo "❌ Python application has syntax errors"
    exit(1)
fi

echo ""
echo "🎉 All tests passed!"
echo "✅ Universal Blue best practices implementation validated"
