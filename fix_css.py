with open('style.css', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

clean_lines = lines[:1734]

new_css = """
/* 3D Background */
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
    background: rgba(var(--surface-color-rgb, 255, 255, 255), 0.85);
    backdrop-filter: blur(10px);
}
[data-theme="dark"] .login-card {
    background: rgba(30, 41, 59, 0.85);
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
.click-hint {
    position: absolute;
    bottom: 20%;
    left: 50%;
    transform: translateX(-50%);
    color: white;
    font-size: 1.2rem;
    letter-spacing: 0.1em;
    opacity: 0.7;
    animation: pulseHint 2s infinite;
    pointer-events: none;
    transition: opacity 0.5s;
    font-family: "Outfit", sans-serif;
    text-shadow: 0 2px 10px rgba(0,0,0,0.5);
}
@keyframes pulseHint {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 0.9; }
}
.hint-hidden {
    opacity: 0 !important;
}
#loginScreen {
    transition: opacity 1s ease, visibility 1s ease;
}
"""

with open('style.css', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)
    f.write(new_css)
