"""Genera modules/sync/_semilla.py desde semilla.key antes de compilar.

Falla ruidosamente si el archivo no existe: un .exe sin semilla real usaria
la semilla de desarrollo y el candado quedaria debil. _semilla.py esta en
.gitignore y jamas llega a git.
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SEMILLA_PATH = os.path.join(ROOT, "semilla.key")
DESTINO = os.path.join(ROOT, "MobilDesk POS", "modules", "sync", "_semilla.py")

if not os.path.exists(SEMILLA_PATH):
    print("ERROR: no existe semilla.key. El build de release queda ABORTADO.")
    print("Sin semilla real el .exe usaria la de desarrollo y el candado no sirve.")
    sys.exit(1)

with open(SEMILLA_PATH, "r", encoding="ascii") as f:
    semilla = f.read().strip()

if len(semilla) < 32 or any(c not in "0123456789abcdefABCDEF" for c in semilla):
    print("ERROR: semilla.key con formato invalido. Build ABORTADO.")
    sys.exit(1)

with open(DESTINO, "w", encoding="ascii", newline="") as f:
    f.write('"""Semilla generada en build. NO editar a mano, NO commitear."""\n')
    f.write(f'SEMILLA = "{semilla}"\n')

print(f"_semilla.py generado ({len(semilla)} caracteres).")

# Verificacion: la llave resultante debe coincidir con la esperada
sys.path.insert(0, os.path.join(ROOT, "MobilDesk POS"))
from modules.sync.sync_service import derivar_llave
print("derivar_llave('mobil-6541') =", derivar_llave("mobil-6541"))