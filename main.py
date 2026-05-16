import sys
from PySide6.QtWidgets import QApplication
from src.controllers.main_controller import MainController
from src.views.main_window import MainWindow
from src.core.isp.plugin_manager import plugin_manager



def main() -> None:
    """
    Entry point for the SilverLab application.
    Initializes the dependency injection container and starts the UI.
    """
    app = QApplication(sys.argv)
    
    # Load ISP Plugins
    plugin_manager.load_plugins()
    
    # Initialize Core/Controller
    controller = MainController()
    
    # Initialize View and inject controller
    window = MainWindow(controller)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
