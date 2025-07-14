#!/bin/bash

echo "🧪 Testing Universal Blue Rebase Tool..."

# Test Python dependencies
echo "Testing Python dependencies..."
python3 -c "import webview; print('✅ webview module available')" 2>/dev/null || echo "❌ webview module missing"

# Test file structure
echo "Testing file structure..."
[ -f "ublue-rebase-tool.py" ] && echo "✅ Python wrapper found" || echo "❌ Python wrapper missing"
[ -f "web/index.html" ] && echo "✅ Web interface found" || echo "❌ Web interface missing"
[ -f "io.github.ublue.RebaseTool.json" ] && echo "✅ Flatpak manifest found" || echo "❌ Flatpak manifest missing"

# Test local execution
echo "Testing local execution..."
if python3 ublue-rebase-tool.py --help 2>/dev/null; then
    echo "✅ Application can start"
else
    echo "❌ Application startup failed"
fi

echo "🎉 Testing complete!"
