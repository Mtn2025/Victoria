import ast
import os
import pytest
from pathlib import Path

# Arquitectura Hexagonal - Test de Barreras de Importación
# Este test asegura programaaticamente que las capas no importen dependencias prohibidas.

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

def get_imports_for_file(filepath):
    """Extrae todos los imports de un archivo Python usando AST."""
    imports = set()
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(filepath))
            
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Guardamos el modulo completo y el paquete base
                    imports.add(node.module)
                    imports.add(node.module.split('.')[0])
    except SyntaxError:
        pass # Ignorar archivos no validos momentaneamente
    return imports

def get_python_files(directory):
    path = BACKEND_DIR / directory
    for root, _, files in os.walk(path):
        for file in files:
            if file.endswith(".py") and not file == "__init__.py":
                yield Path(root) / file

def test_domain_layer_is_pure():
    """LA LEY DE ORO: Domain no puede importar Infrastructure, Interfaces ni dependencias externas pesadas."""
    prohibited_internal_layers = ["backend.infrastructure", "backend.application", "backend.interfaces"]
    prohibited_external_libs = ["sqlalchemy", "fastapi", "pydantic", "httpx", "redis", "azure", "twilio", "groq"]
    
    for py_file in get_python_files("domain"):
        imports = get_imports_for_file(py_file)
        
        for imp in imports:
            # Check internal breaches
            for proh in prohibited_internal_layers:
                assert not imp.startswith(proh), f"VIOLACIÓN ARQUITECTÓNICA: El archivo de dominio {py_file.name} está importando de la capa {proh}."
            
            # Check external breaches
            assert imp not in prohibited_external_libs, f"VIOLACIÓN DE PUREZA: El archivo de dominio {py_file.name} está importando dependencias tecnológicas externas ({imp})."

def test_infrastructure_layer_dependencies():
    """Infraestructura no debe contener lógica de HTTP pública (Interfaces)."""
    for py_file in get_python_files("infrastructure"):
        imports = get_imports_for_file(py_file)
        for imp in imports:
            assert not imp.startswith("backend.interfaces"), f"VIOLACIÓN ARQUITECTÓNICA: Infraestructura ({py_file.name}) importando desde Interfaces (Rutas/HTTP). Inversión de control requerida."
