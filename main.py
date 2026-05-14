import sys
from PySide6.QtWidgets import QApplication
from src.controllers.main_controller import MainController
from src.views.main_window import MainWindow


def main() -> None:
    """
    Entry point for the SilverLab application.
    Initializes the dependency injection container and starts the UI.
    """
    app = QApplication(sys.argv)
    
    # Initialize Core/Controller
    controller = MainController()
    
    # Initialize View and inject controller
    window = MainWindow(controller)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
