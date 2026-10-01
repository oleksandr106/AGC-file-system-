with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Make sure click hint is visible and has high z-index
if 'z-index: 1000;' not in css:
    css = css.replace('.click-hint {', '.click-hint {\n    z-index: 1000;\n    display: block !important;')
    css = css.replace('.login-container {', '.login-container {\n    z-index: 999;')

# Make login card definitely visible
css = css.replace('.login-card {', '.login-card {\n    z-index: 1000;\n    background: rgba(17, 24, 39, 0.9) !important;\n    border: 1px solid rgba(255, 255, 255, 0.1);')

# Also fix the background for body to make sure it covers properly but still lets canvas show
# If body bg is blocking canvas too much, let's make it slightly more transparent
css = css.replace('--bg-primary: rgba(10, 14, 26, 0.85);', '--bg-primary: rgba(10, 14, 26, 0.6);')

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

# Bump cache buster
import re
with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = re.sub(r'style\.css\?v=[0-9.]+', 'style.css?v=8.0', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Login screen fixed")
