import re

with open('routes/routes_directora.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Simple approach: replace .then(lambda X: joinedload(X.Y)) with .joinedload(Y)
# Do multiple passes for nested cases
for _ in range(20):
    old = content
    content = re.sub(
        r'\.then\(\s*lambda\s+\w+\s*:\s*joinedload\(\w+\.(\w+)\)\s*\)',
        r'.joinedload(\1)',
        content
    )
    if content == old:
        break

# Also handle: .then(lambda X: joinedload(X.Y).joinedload(Z)) cases
# These become .joinedload(Y).joinedload(Z) after the first pass

with open('routes/routes_directora.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Fix base.html sidebar links
with open('templates/base.html', 'r', encoding='utf-8') as f:
    base = f.read()

links_to_remove = [
    ("docente.horario", "Horario"),
    ("docente.comentarios", "Comentarios"),
    ("estudiante.horario", "Horario"),
]

for endpoint, label in links_to_remove:
    base = re.sub(
        r'<a href="\{\{ url_for\(\'' + endpoint + r'\'\) \}\}"[^>]*>.*?</a>',
        '<!-- {} {} -->'.format(endpoint, label),
        base
    )

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(base)

print("Fix completado")
verificar = "then(" in content
print(f"Quedan .then(): {verificar}")
if verificar:
    for i, line in enumerate(content.split('\n')):
        if 'then(' in line:
            print(f"  Linea {i+1}: {line.strip()[:80]}")
