import sys

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from app_paths import resource_path

from database.migrate import run_migrations
from modules.usuarios.user_service import has_users
from modules.usuarios.session import get_user
from ui.windows.login_window import LoginWindow
from ui.windows.dashboard_window import DashboardWindow
from ui.windows.initial_setup_window import InitialSetupWindow
from ui.theme import build_app_stylesheet

def main():
    run_migrations()

    app = QApplication(sys.argv)
    app.setApplicationName("MobilDesk POS")
    app.setWindowIcon(QIcon(resource_path("assets/kiosko_logo.svg")))
    app.setStyleSheet(build_app_stylesheet())

    if not has_users():
        setup_dlg = InitialSetupWindow()
        setup_dlg.exec()
        if not setup_dlg.configurado_exitosamente:
            sys.exit(0)
        ventana = DashboardWindow(mostrar_tour_inicial=True)
    else:
        ventana = LoginWindow()

    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
