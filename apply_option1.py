import shutil

# Zalohujeme si soucasny styl, kdyby neco
shutil.copyfile('style.css', 'style.css.bak')

with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# 1. DARK MODE VARIABLES
css = css.replace('--bg-primary: #0a0e1a;', '--bg-primary: rgba(15, 23, 42, 0.85);')
css = css.replace('--bg-secondary: #111827;', '--bg-secondary: rgba(30, 41, 59, 0.95);')
css = css.replace('--bg-card: rgba(17, 24, 39, 0.7);', '--bg-card: rgba(30, 41, 59, 0.95);')
css = css.replace('--bg-sidebar: rgba(6, 10, 23, 0.95);', '--bg-sidebar: rgba(15, 23, 42, 0.98);')

css = css.replace('--gradient-primary: linear-gradient(135deg, #638fff 0%, #a78bfa 100%);', '--gradient-primary: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);')
css = css.replace('--gradient-sidebar: linear-gradient(180deg, #060a17 0%, #0d1321 100%);', '--gradient-sidebar: rgba(15, 23, 42, 0.95);')
css = css.replace('--gradient-login: linear-gradient(135deg, #060a17 0%, #0e1a38 50%, #1a0e2e 100%);', '--gradient-login: transparent;')
css = css.replace('--shadow-glow: 0 0 30px rgba(99, 143, 255, 0.1);', '--shadow-glow: 0 4px 15px rgba(0, 0, 0, 0.2);')

# 2. LIGHT MODE VARIABLES
css = css.replace('--bg-primary: #f8fafc;', '--bg-primary: rgba(241, 245, 249, 0.85);')
css = css.replace('--bg-secondary: #ffffff;', '--bg-secondary: rgba(255, 255, 255, 0.95);')
css = css.replace('--bg-card: rgba(255, 255, 255, 0.9);', '--bg-card: rgba(255, 255, 255, 0.95);')
css = css.replace('--bg-sidebar: rgba(255, 255, 255, 0.95);', '--bg-sidebar: rgba(255, 255, 255, 0.98);')

css = css.replace('--gradient-login: linear-gradient(135deg, #e0e7ff 0%, #f0e6ff 50%, #e0f2fe 100%);', '--gradient-login: transparent;')
css = css.replace('--shadow-glow: 0 0 30px rgba(99, 143, 255, 0.08);', '--shadow-glow: 0 4px 12px rgba(0, 0, 0, 0.08);')
css = css.replace('--gradient-sidebar: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);', '--gradient-sidebar: rgba(255, 255, 255, 0.95);')

# 3. SHARPER BORDERS (Corporate look)
css = css.replace('--radius-sm: 8px;', '--radius-sm: 4px;')
css = css.replace('--radius-md: 12px;', '--radius-md: 6px;')
css = css.replace('--radius-lg: 16px;', '--radius-lg: 8px;')
css = css.replace('--radius-xl: 20px;', '--radius-xl: 12px;')

# 4. REMOVE CLICK HINT OVERLAY DURING APP USAGE
# To do this safely, we add a new CSS rule at the end of the file.
new_rules = """

/* Corporate UI fixes - hide click hint when login is hidden */
.login-hidden ~ .app-container {
    display: block;
}
.login-hidden ~ #clickHint, #clickHint.login-hidden {
    display: none !important;
}

/* Ensure canvas is always in background */
.bg-canvas {
    z-index: -10;
}

/* Ensure body allows background canvas to be seen */
body {
    background-color: transparent !important;
}
"""

if "Corporate UI fixes" not in css:
    css += new_rules

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Corporate translucent styling applied successfully.")
