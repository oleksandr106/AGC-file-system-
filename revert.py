import shutil

shutil.copyfile('recovered_style.css', 'style.css')

html_path = 'index.html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('"ph-fill ', '"ph-duotone ')
html = html.replace('ph ', 'ph-duotone ')
html = html.replace('/style.css?v=4.0', '/style.css')
html = html.replace('/style.css?v=3.0', '/style.css')
html = html.replace('/style.css?v=2.0', '/style.css')

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

js_path = 'app.js'
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

js = js.replace('"ph-fill ', '"ph-duotone ')
js = js.replace('ph ', 'ph-duotone ')

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Reverted successfully.")
