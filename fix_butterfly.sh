#!/bin/bash
# Fix butterfly logo - Make it SHARP and CLEAN

echo "🦋 Fixing butterfly logo for SHARP, CLEAN contours..."
echo ""

PROJECT_DIR="/root/python-debug-tutor-mcp/python-debug-tutor-mcp"

# Backup
echo "💾 Creating backup..."
cp "$PROJECT_DIR/icons/butterfly_logo_bright.svg" "$PROJECT_DIR/icons/butterfly_logo_OLD.svg" 2>/dev/null || true
cp "$PROJECT_DIR/static/butterfly_logo.css" "$PROJECT_DIR/static/butterfly_logo_OLD.css" 2>/dev/null || true

# Update SVG with clean version (8° rotation, no blur)
echo "🎨 Installing CLEAN butterfly SVG..."
cat > "$PROJECT_DIR/icons/butterfly_logo_bright.svg" << EOFSVG
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="wingLeft" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="wingRight" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#00f2fe;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#43e97b;stop-opacity:1" />
    </linearGradient>
  </defs>
  <g transform="rotate(8 100 100)">
    <ellipse cx="55" cy="65" rx="48" ry="60" fill="url(#wingLeft)" transform="rotate(-28 55 65)"/>
    <ellipse cx="60" cy="70" rx="28" ry="38" fill="#ffffff" opacity="0.4" transform="rotate(-28 60 70)"/>
    <ellipse cx="58" cy="72" rx="18" ry="25" fill="#ffffff" opacity="0.25" transform="rotate(-28 58 72)"/>
    <ellipse cx="145" cy="65" rx="48" ry="60" fill="url(#wingRight)" transform="rotate(28 145 65)"/>
    <ellipse cx="140" cy="70" rx="28" ry="38" fill="#ffffff" opacity="0.4" transform="rotate(28 140 70)"/>
    <ellipse cx="142" cy="72" rx="18" ry="25" fill="#ffffff" opacity="0.25" transform="rotate(28 142 72)"/>
    <ellipse cx="62" cy="138" rx="42" ry="52" fill="url(#wingRight)" transform="rotate(-45 62 138)"/>
    <ellipse cx="67" cy="135" rx="24" ry="32" fill="#ffffff" opacity="0.35" transform="rotate(-45 67 135)"/>
    <ellipse cx="138" cy="138" rx="42" ry="52" fill="url(#wingLeft)" transform="rotate(45 138 138)"/>
    <ellipse cx="133" cy="135" rx="24" ry="32" fill="#ffffff" opacity="0.35" transform="rotate(45 133 135)"/>
    <ellipse cx="100" cy="102" rx="16" ry="72" fill="#1a202c" opacity="0.3"/>
    <ellipse cx="100" cy="100" rx="14" ry="70" fill="#2d3748"/>
    <ellipse cx="100" cy="100" rx="12" ry="68" fill="url(#wingLeft)"/>
    <ellipse cx="97" cy="95" rx="6" ry="60" fill="#ffffff" opacity="0.3"/>
    <circle cx="100" cy="32" r="16" fill="#2d3748"/>
    <circle cx="100" cy="32" r="14" fill="#667eea"/>
    <circle cx="95" cy="30" r="3" fill="#ffffff" opacity="0.9"/>
    <circle cx="105" cy="30" r="3" fill="#ffffff" opacity="0.9"/>
    <circle cx="96" cy="29" r="1.5" fill="#2d3748"/>
    <circle cx="106" cy="29" r="1.5" fill="#2d3748"/>
    <path d="M 100 18 Q 88 8 82 0" stroke="#667eea" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="82" cy="0" r="5" fill="#667eea"/>
    <circle cx="82" cy="0" r="3" fill="#ffffff" opacity="0.6"/>
    <path d="M 100 18 Q 112 8 118 0" stroke="#4facfe" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="118" cy="0" r="5" fill="#4facfe"/>
    <circle cx="118" cy="0" r="3" fill="#ffffff" opacity="0.6"/>
    <circle cx="38" cy="55" r="4" fill="#ffffff" opacity="0.5"/>
    <circle cx="45" cy="75" r="3" fill="#ffffff" opacity="0.4"/>
    <circle cx="162" cy="55" r="4" fill="#ffffff" opacity="0.5"/>
    <circle cx="155" cy="75" r="3" fill="#ffffff" opacity="0.4"/>
  </g>
</svg>
EOFSVG

# Update CSS for sharp rendering
echo "✨ Installing CLEAN CSS..."
cat > "$PROJECT_DIR/static/butterfly_logo.css" << EOFCSS
/* Synapse AI - Butterfly Logo CSS (CLEAN SHARP VERSION) */
.header img[src*="butterfly"],
.navbar img[src*="butterfly"],
.logo img,
.logo-container img,
img[alt*="Synapse"] {
    width: 140px !important;
    height: 140px !important;
    object-fit: contain;
    vertical-align: middle;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
    background: transparent !important;
    transition: all 0.3s ease;
    shape-rendering: geometricPrecision;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
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
    transform: scale(1.05) rotate(2deg);
    filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.4));
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
    font-weight: 800;
    color: white;
    text-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

body.dark-mode .header img[src*="butterfly"] {
    filter: drop-shadow(0 2px 8px rgba(255, 255, 255, 0.2)) brightness(1.05);
}

.header img[src*="butterfly"]:focus {
    outline: 3px solid #667eea;
    outline-offset: 4px;
    border-radius: 10px;
}
EOFCSS

echo ""
echo "✅ DONE! Butterfly logo now has:"
echo "   • Sharp, clean contours (no blur)"
echo "   • 8° rotation for elegance"
echo "   • Crisp edges rendering"
echo "   • Smooth gradients"
echo ""
echo "🔄 Reload browser with Ctrl+F5 to see changes"
echo "💾 Old files backed up as *_OLD.*"#!/bin/bash
# Fix butterfly logo - Make it SHARP and CLEAN

echo "🦋 Fixing butterfly logo for SHARP, CLEAN contours..."
echo ""

PROJECT_DIR="/root/python-debug-tutor-mcp/python-debug-tutor-mcp"

# Backup
echo "💾 Creating backup..."
cp "$PROJECT_DIR/icons/butterfly_logo_bright.svg" "$PROJECT_DIR/icons/butterfly_logo_OLD.svg" 2>/dev/null || true
cp "$PROJECT_DIR/static/butterfly_logo.css" "$PROJECT_DIR/static/butterfly_logo_OLD.css" 2>/dev/null || true

# Update SVG with clean version (8° rotation, no blur)
echo "🎨 Installing CLEAN butterfly SVG..."
cat > "$PROJECT_DIR/icons/butterfly_logo_bright.svg" << EOFSVG
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <defs>
    <linearGradient id="wingLeft" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#667eea;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#764ba2;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#f093fb;stop-opacity:1" />
    </linearGradient>
    <linearGradient id="wingRight" x1="100%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#4facfe;stop-opacity:1" />
      <stop offset="50%" style="stop-color:#00f2fe;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#43e97b;stop-opacity:1" />
    </linearGradient>
  </defs>
  <g transform="rotate(8 100 100)">
    <ellipse cx="55" cy="65" rx="48" ry="60" fill="url(#wingLeft)" transform="rotate(-28 55 65)"/>
    <ellipse cx="60" cy="70" rx="28" ry="38" fill="#ffffff" opacity="0.4" transform="rotate(-28 60 70)"/>
    <ellipse cx="58" cy="72" rx="18" ry="25" fill="#ffffff" opacity="0.25" transform="rotate(-28 58 72)"/>
    <ellipse cx="145" cy="65" rx="48" ry="60" fill="url(#wingRight)" transform="rotate(28 145 65)"/>
    <ellipse cx="140" cy="70" rx="28" ry="38" fill="#ffffff" opacity="0.4" transform="rotate(28 140 70)"/>
    <ellipse cx="142" cy="72" rx="18" ry="25" fill="#ffffff" opacity="0.25" transform="rotate(28 142 72)"/>
    <ellipse cx="62" cy="138" rx="42" ry="52" fill="url(#wingRight)" transform="rotate(-45 62 138)"/>
    <ellipse cx="67" cy="135" rx="24" ry="32" fill="#ffffff" opacity="0.35" transform="rotate(-45 67 135)"/>
    <ellipse cx="138" cy="138" rx="42" ry="52" fill="url(#wingLeft)" transform="rotate(45 138 138)"/>
    <ellipse cx="133" cy="135" rx="24" ry="32" fill="#ffffff" opacity="0.35" transform="rotate(45 133 135)"/>
    <ellipse cx="100" cy="102" rx="16" ry="72" fill="#1a202c" opacity="0.3"/>
    <ellipse cx="100" cy="100" rx="14" ry="70" fill="#2d3748"/>
    <ellipse cx="100" cy="100" rx="12" ry="68" fill="url(#wingLeft)"/>
    <ellipse cx="97" cy="95" rx="6" ry="60" fill="#ffffff" opacity="0.3"/>
    <circle cx="100" cy="32" r="16" fill="#2d3748"/>
    <circle cx="100" cy="32" r="14" fill="#667eea"/>
    <circle cx="95" cy="30" r="3" fill="#ffffff" opacity="0.9"/>
    <circle cx="105" cy="30" r="3" fill="#ffffff" opacity="0.9"/>
    <circle cx="96" cy="29" r="1.5" fill="#2d3748"/>
    <circle cx="106" cy="29" r="1.5" fill="#2d3748"/>
    <path d="M 100 18 Q 88 8 82 0" stroke="#667eea" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="82" cy="0" r="5" fill="#667eea"/>
    <circle cx="82" cy="0" r="3" fill="#ffffff" opacity="0.6"/>
    <path d="M 100 18 Q 112 8 118 0" stroke="#4facfe" stroke-width="3" fill="none" stroke-linecap="round"/>
    <circle cx="118" cy="0" r="5" fill="#4facfe"/>
    <circle cx="118" cy="0" r="3" fill="#ffffff" opacity="0.6"/>
    <circle cx="38" cy="55" r="4" fill="#ffffff" opacity="0.5"/>
    <circle cx="45" cy="75" r="3" fill="#ffffff" opacity="0.4"/>
    <circle cx="162" cy="55" r="4" fill="#ffffff" opacity="0.5"/>
    <circle cx="155" cy="75" r="3" fill="#ffffff" opacity="0.4"/>
  </g>
</svg>
EOFSVG

# Update CSS for sharp rendering
echo "✨ Installing CLEAN CSS..."
cat > "$PROJECT_DIR/static/butterfly_logo.css" << EOFCSS
/* Synapse AI - Butterfly Logo CSS (CLEAN SHARP VERSION) */
.header img[src*="butterfly"],
.navbar img[src*="butterfly"],
.logo img,
.logo-container img,
img[alt*="Synapse"] {
    width: 140px !important;
    height: 140px !important;
    object-fit: contain;
    vertical-align: middle;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.15));
    background: transparent !important;
    transition: all 0.3s ease;
    shape-rendering: geometricPrecision;
    image-rendering: -webkit-optimize-contrast;
    image-rendering: crisp-edges;
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
    transform: scale(1.05) rotate(2deg);
    filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.4));
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
    font-weight: 800;
    color: white;
    text-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
}

body.dark-mode .header img[src*="butterfly"] {
    filter: drop-shadow(0 2px 8px rgba(255, 255, 255, 0.2)) brightness(1.05);
}

.header img[src*="butterfly"]:focus {
    outline: 3px solid #667eea;
    outline-offset: 4px;
    border-radius: 10px;
}
EOFCSS

echo ""
echo "✅ DONE! Butterfly logo now has:"
echo "   • Sharp, clean contours (no blur)"
echo "   • 8° rotation for elegance"
echo "   • Crisp edges rendering"
echo "   • Smooth gradients"
echo ""
echo "🔄 Reload browser with Ctrl+F5 to see changes"
echo "💾 Old files backed up as *_OLD.*"
