with open('style.css', 'r', encoding='utf-8') as f:
    css = f.read()

# Odstranime spatna pravidla
css = css.replace('''
/* Ensure canvas is always in background */
.bg-canvas {
    z-index: -10;
}

/* Ensure body allows background canvas to be seen */
body {
    background-color: transparent !important;
}
''', '')

# Pridame spravna pravidla
new_rules = '''
/* Ensure canvas is always in background */
.bg-canvas {
    z-index: -1;
}

/* Make html transparent so canvas shows through, body gets the semi-transparent overlay */
html {
    background-color: #050505;
}
body {
    background-color: var(--bg-primary) !important;
}
'''
if 'html {' not in css:
    css += new_rules

with open('style.css', 'w', encoding='utf-8') as f:
    f.write(css)

print("CSS fixed")
