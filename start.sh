#!/bin/bash
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║           🚩 CTF ARENA — Easy Level Setup            ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# Check python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt --break-system-packages -q 2>/dev/null || pip install -r requirements.txt -q
echo "✅ Dependencies ready"

# Generate stego image if not exists
if [ ! -f "static/files/cat.jpg" ]; then
    echo "🖼  Generating steganography image..."
    python3 make_stego.py
fi

echo ""
echo "═══════════════════════════════════════════════"
echo "  🌐  Server starting at: http://localhost:5000"
echo "  📋  5 Challenges | 350 Total Points"
echo "  ⛳  Flag format: FLAG{...}"
echo "═══════════════════════════════════════════════"
echo ""
echo "  Challenges:"
echo "   CH-01 🔐 Caesar's Secret      [50 pts]  Cryptography"
echo "   CH-02 🍪 Cookie Monster       [75 pts]  Web"
echo "   CH-03 🖼️  Hidden in Sight      [75 pts]  Steganography"
echo "   CH-04 💻 Base Jumping         [50 pts]  Encoding"
echo "   CH-05 🔎 GitLeaks            [100 pts]  OSINT"
echo ""
echo "  Press Ctrl+C to stop"
echo "═══════════════════════════════════════════════"
echo ""

python3 app.py
