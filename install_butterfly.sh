#!/bin/bash
# ============================================
# SYNAPSE AI - BUTTERFLY LOGO INSTALLER
# All-in-one script - no external files needed!
# ============================================

set -e

echo "🦋 SYNAPSE AI - Butterfly Logo Installer"
echo "========================================"
echo ""

PROJECT_DIR="/root/python-debug-tutor-mcp/python-debug-tutor-mcp"
BACKUP_DIR="$PROJECT_DIR/backup_$(date +%Y%m%d_%H%M%S)"

# Create directories
echo "📁 Creating directories..."
mkdir -p "$PROJECT_DIR/icons"
mkdir -p "$PROJECT_DIR/static"
mkdir -p "$BACKUP_DIR"

# Create butterfly SVG logo
echo "🦋 Creating butterfly logo SVG..."
cat > "$PROJECT_DIR/icons/butterfly_logo_bright.svg" << 'EOFSVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <radialGradient id="wingGlow1">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.9" />
      <stop offset="40%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#764ba2;stop-opacity:1" />
    </radialGradient>
    <radialGradient id="wingGlow2">
      <stop offset="0%" style="stop-color:#ffffff;stop-opacity:0.9" />
      <stop offset="40%" style="stop-color:#4facfe;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#00f2fe;stop-opacity:1" />
    </radialGradient>
    <filter id="brightGlow">
      <feGaussianBlur in="SourceGraphic" stdDeviation="4"/>
      <feComponentTransfer>
        <feFuncA type="discrete" tableValues="1 1"/>
      </feComponentTransfer>
      <feMerge>
        <feMergeNode/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>
  </defs>
  
  <ellipse cx="60" cy="60" rx="50" ry="60" fill="#667eea" opacity="0.3" filter="url(#brightGlow)" transform="rotate(-25 60 60)"/>
  <ellipse cx="140" cy="60" rx="50" ry="60" fill="#4facfe" opacity="0.3" filter="url(#brightGlow)" transform="rotate(25 140 60)"/>
  <ellipse cx="65" cy="140" rx="45" ry="55" fill="#00f2fe" opacity="0.3" filter="url(#brightGlow)" transform="rotate(-40 65 140)"/>
  <ellipse cx="135" cy="140" rx="45" ry="55" fill="#764ba2" opacity="0.3" filter="url(#brightGlow)" transform="rotate(40 135 140)"/>
  
  <ellipse cx="60" cy="60" rx="48" ry="58" fill="url(#wingGlow1)" transform="rotate(-25 60 60)"/>
  <ellipse cx="140" cy="60" rx="48" ry="58" fill="url(#wingGlow2)" transform="rotate(25 140 60)"/>
  <ellipse cx="65" cy="140" rx="43" ry="53" fill="url(#wingGlow2)" transform="rotate(-40 65 140)"/>
  <ellipse cx="135" cy="140" rx="43" ry="53" fill="url(#wingGlow1)" transform="rotate(40 135 140)"/>
  
  <ellipse cx="65" cy="65" rx="25" ry="35" fill="#ffffff" opacity="0.5" transform="rotate(-25 65 65)"/>
  <ellipse cx="135" cy="65" rx="25" ry="35" fill="#ffffff" opacity="0.5" transform="rotate(25 135 65)"/>
  <ellipse cx="70" cy="135" rx="20" ry="30" fill="#ffffff" opacity="0.4" transform="rotate(-40 70 135)"/>
  <ellipse cx="130" cy="135" rx="20" ry="30" fill="#ffffff" opacity="0.4" transform="rotate(40 130 135)"/>
  
  <ellipse cx="100" cy="100" rx="18" ry="75" fill="#2d3748"/>
  <ellipse cx="100" cy="100" rx="14" ry="70" fill="#667eea"/>
  <ellipse cx="100" cy="100" rx="10" ry="65" fill="url(#wingGlow1)"/>
  
  <circle cx="100" cy="35" r="18" fill="#2d3748"/>
  <circle cx="100" cy="35" r="15" fill="#667eea"/>
  <circle cx="95" cy="32" r="3" fill="#ffffff"/>
  <circle cx="105" cy="32" r="3" fill="#ffffff"/>
  
  <path d="M 100 20 Q 85 10 80 0" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.6"/>
  <path d="M 100 20 Q 115 10 120 0" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" opacity="0.6"/>
  <path d="M 100 20 Q 85 10 80 0" stroke="#667eea" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <path d="M 100 20 Q 115 10 120 0" stroke="#4facfe" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <circle cx="80" cy="0" r="5" fill="#667eea" filter="url(#brightGlow)"/>
  <circle cx="120" cy="0" r="5" fill="#4facfe" filter="url(#brightGlow)"/>
</svg>
EOFSVG

# Create CSS file
echo "🎨 Creating CSS file..."
cat > "$PROJECT_DIR/static/butterfly_logo.css" << 'EOFCSS'
/* Synapse AI - Global Butterfly Logo Styles */
.header img[src*="butterfly"],
.navbar img[src*="butterfly"],
.logo img,
.logo-container img,
img[alt*="Synapse"] {
    width: 140px !important;
    height: 140px !important;
    object-fit: contain;
    vertical-align: middle;
    filter: drop-shadow(0 4px 12px rgba(255, 255, 255, 0.4));
    background: transparent !important;
    transition: all 0.3s ease;
}

@media (max-width: 768px) {
    .header img[src*="butterfly"],
    .navbar img[src*="butterfly"],
    .logo img {
        width: 80px !important;
        height: 80px !important;
    }
}

.header img[src*="butterfly"]:hover,
.navbar img[src*="butterfly"]:hover {
    transform: scale(1.05);
    filter: drop-shadow(0 6px 16px rgba(255, 255, 255, 0.6));
}

.header,
.main-header {
    padding: 5px 20px 0px 20px !important;
    margin-bottom: 0px !important;
}

.header h1 {
    display: flex;
    align-items: center;
    gap: 15px;
    font-size: 48px;
    margin: 0;
}
EOFCSS

echo "✅ Files created"
echo ""

# Backup HTML files
echo "💾 Creating backup..."
find "$PROJECT_DIR" -name "*.html" -type f -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true
echo "✅ Backup created in: $BACKUP_DIR"
echo ""

# Replace logos in HTML files
echo "🔄 Replacing logos in HTML files..."
MODIFIED=0

for file in $(find "$PROJECT_DIR" -name "*.html" -type f); do
    filename=$(basename "$file")
    
    if grep -q -E "(brain\.png|sinapse.*\.png)" "$file" 2>/dev/null; then
        # Replace logo paths
        sed -i 's|/icons/brain\.png|/icons/butterfly_logo_bright.svg|g' "$file"
        sed -i 's|/icons/sinapse_transparent\.png|/icons/butterfly_logo_bright.svg|g' "$file"
        sed -i 's|/icons/sinapse\.png|/icons/butterfly_logo_bright.svg|g' "$file"
        sed -i 's|src="brain\.png"|src="/icons/butterfly_logo_bright.svg"|g' "$file"
        
        # Add alt text
        sed -i 's|<img src="/icons/butterfly_logo_bright\.svg">|<img src="/icons/butterfly_logo_bright.svg" alt="Synapse AI">|g' "$file"
        
        # Add CSS if not present
        if ! grep -q "butterfly_logo.css" "$file"; then
            sed -i 's|</head>|    <link rel="stylesheet" href="/static/butterfly_logo.css">\n</head>|' "$file"
        fi
        
        echo "   ✓ $filename"
        ((MODIFIED++))
    fi
done

echo ""
echo "✅ Modified $MODIFIED HTML files"
echo ""

# Set permissions
chmod 644 "$PROJECT_DIR/icons/butterfly_logo_bright.svg"
chmod 644 "$PROJECT_DIR/static/butterfly_logo.css"

# Summary
echo "════════════════════════════════════════"
echo "✅ INSTALLATION COMPLETE!"
echo "════════════════════════════════════════"
echo "📊 Files modified: $MODIFIED"
echo "💾 Backup: $BACKUP_DIR"
echo ""
echo "📋 Next steps:"
echo "1. Test the pages in your browser"
echo "2. If needed, restart server:"
echo "   systemctl restart synapse-ai"
echo ""
echo "🦋 Your platform now has a beautiful butterfly logo!"
echo "════════════════════════════════════════"
