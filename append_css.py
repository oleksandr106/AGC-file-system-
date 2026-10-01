with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

new_css = """
/* =========================================
   ESSENTIAL RULES FOR 3D CANVAS & LOGIN
   ========================================= */
.bg-canvas {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: -1;
    pointer-events: none;
}

/* Semi-transparent backgrounds to let the 3D canvas show through */
.login-container, .app-container {
    background: transparent !important;
}

.login-card {
    background: rgba(17, 24, 39, 0.95);
    backdrop-filter: blur(10px);
}
[data-theme="light"] .login-card {
    background: rgba(255, 255, 255, 0.95);
}

/* Login screen transition */
.login-card {
    transition: opacity 1.2s cubic-bezier(0.16, 1, 0.3, 1), transform 1.2s cubic-bezier(0.16, 1, 0.3, 1);
}
.login-hidden .login-card {
    opacity: 0;
    transform: scale(0.8) translateY(20px);
    pointer-events: none;
}
.login-hidden {
    opacity: 0 !important;
    pointer-events: none !important;
    visibility: hidden;
}

/* Click Hint */
.click-hint {
    position: absolute;
    bottom: 20%;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    font-size: 1.2rem;
    letter-spacing: 0.1em;
    opacity: 0.8;
    animation: pulseHint 2s infinite;
    pointer-events: none;
    transition: opacity 0.5s;
    font-family: "Outfit", sans-serif;
    text-shadow: 0 2px 10px rgba(0,0,0,0.8);
    z-index: 1000;
}
@keyframes pulseHint {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}
.hint-hidden {
    opacity: 0 !important;
}
#loginScreen {
    transition: opacity 1s ease, visibility 1s ease;
    z-index: 999;
}

/* Base backgrounds */
html {
    background-color: #030408;
}
body {
    background-color: var(--bg-primary) !important;
}
"""

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css + new_css)

import re
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'style\.css\?v=[0-9.]+', 'style.css?v=9.0', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("CSS appended")
