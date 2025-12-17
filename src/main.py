"""
Punto de entrada de la aplicación.
"""
import sys
import os

# Configurar path para permitir imports relativos y absolutos correctamente
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, project_root)

from src.ui.app import App

def main():
    """Función principal."""
    try:
        app = App()
        app.mainloop()
    except Exception as e:
        print(f"Error fatal: {e}")
        input("Presione Enter para salir...")

if __name__ == "__main__":
    main()
