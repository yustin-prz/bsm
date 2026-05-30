"""
Bedrock Server Manager — punto de entrada.

Este archivo es el "orquestador": arranca la aplicación Qt y abre la ventana
principal (definida en el paquete `bsm`). Toda la lógica vive en módulos dentro
de `bsm/` para mantener el código ordenado y modular.

Ejecutar en desarrollo:   python main.py
Empaquetar a .exe:        pyinstaller --onefile --windowed --name BedrockManager --collect-all PyQt6 main.py
"""
import sys
import traceback

from PyQt6.QtWidgets import QApplication, QMessageBox

from bsm.window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Bedrock Server Manager")

    # Evita que un error inesperado cierre el .exe en silencio (sin consola):
    # muestra el error y mantiene la app abierta.
    def _excepthook(exc_type, exc_value, exc_tb):
        msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        try:
            QMessageBox.critical(None, "Error inesperado",
                                 f"Ocurrió un error pero la aplicación sigue abierta:\n\n{msg}")
        except Exception:
            pass
    sys.excepthook = _excepthook

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
