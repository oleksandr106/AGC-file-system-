with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Restore original dark mode colors with transparency
css = css.replace('--bg-primary: rgba(15, 23, 42, 0.85);', '--bg-primary: rgba(10, 14, 26, 0.85);')
css = css.replace('--bg-secondary: rgba(30, 41, 59, 0.95);', '--bg-secondary: rgba(17, 24, 39, 0.95);')
css = css.replace('--bg-card: rgba(30, 41, 59, 0.95);', '--bg-card: rgba(17, 24, 39, 0.85);')
css = css.replace('--bg-sidebar: rgba(15, 23, 42, 0.98);', '--bg-sidebar: rgba(6, 10, 23, 0.95);')
css = css.replace('--gradient-sidebar: rgba(15, 23, 42, 0.95);', '--gradient-sidebar: rgba(6, 10, 23, 0.95);')

# html background
css = css.replace('background-color: #050505;', 'background-color: #030408;')

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("Colors fixed")
