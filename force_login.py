with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove login-hidden class from the login screen so it's always visible by default
html = html.replace('class="login-container login-hidden"', 'class="login-container"')

# Hide the click hint completely since we don't need it anymore if login is visible
html = html.replace('<div id="clickHint" class="click-hint">KLIKNI NA MODEL PRO VSTUP</div>', '<div id="clickHint" class="click-hint" style="display: none;">KLIKNI NA MODEL PRO VSTUP</div>')

# Bump version to 10.0
import re
html = re.sub(r'style\.css\?v=[0-9.]+', 'style.css?v=10.0', html)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Forced login screen visibility")
