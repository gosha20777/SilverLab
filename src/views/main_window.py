from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QListWidget, QPushButton, QSlider, QLabel, QFileDialog,
    QGraphicsView, QGraphicsScene
)
from PySide6.QtCore import Qt
from src.controllers.main_controller import MainController
from src.models.frame_container import FrameContainer
from src.utils.converters import numpy_to_qpixmap


class MainWindow(QMainWindow):
    """
    Main Application Window providing the 3-column UI layout.
    """
    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SilverLab MVP v0.1")
        self.resize(1200, 800)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        # Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Splitter for 3 columns
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # 1. Left Panel (Gallery)
        self.gallery_list = QListWidget()
        self.gallery_list.addItem("Здесь будут миниатюры файлов")
        splitter.addWidget(self.gallery_list)

        # 2. Central Panel (Canvas)
        self.scene = QGraphicsScene()
        self.canvas_view = QGraphicsView(self.scene)
        self.canvas_view.setStyleSheet("background-color: #2b2b2b;")
        splitter.addWidget(self.canvas_view)

        # 3. Right Panel (Inspector)
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        
        self.load_button = QPushButton("Загрузить скан (Load Image)")
        inspector_layout.addWidget(self.load_button)
        
        inspector_layout.addSpacing(20)
        inspector_layout.addWidget(QLabel("Цветокоррекция:"))
        
        self.exposure_label = QLabel("Экспозиция: 0.0")
        inspector_layout.addWidget(self.exposure_label)
        
        self.exposure_slider = QSlider(Qt.Horizontal)
        self.exposure_slider.setMinimum(-20)  # -2.0
        self.exposure_slider.setMaximum(20)   # +2.0
        self.exposure_slider.setValue(0)
        inspector_layout.addWidget(self.exposure_slider)
        
        inspector_layout.addSpacing(20)
        self.align_button = QPushButton("Авто-выравнивание (Mock)")
        self.split_button = QPushButton("Разрезать диптих (Mock)")
        inspector_layout.addWidget(self.align_button)
        inspector_layout.addWidget(self.split_button)
        
        inspector_layout.addStretch()
        splitter.addWidget(inspector_widget)

        # Set initial splitter sizes
        splitter.setSizes([200, 700, 300])
        
        # Override wheel event for zoom
        self.canvas_view.wheelEvent = self._on_canvas_wheel_event

    def _connect_signals(self) -> None:
        self.load_button.clicked.connect(self._on_load_clicked)
        self.exposure_slider.valueChanged.connect(self._on_slider_changed)
        
        self.align_button.clicked.connect(lambda: print("Auto-align not implemented yet."))
        self.split_button.clicked.connect(lambda: print("Split diptych not implemented yet."))

        # Connect controller signals
        self.controller.image_loaded.connect(self._render_container)
        self.controller.image_processed.connect(self._render_container)

    def _on_load_clicked(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "", "Images (*.tiff *.tif *.jpg *.jpeg *.png)"
        )
        if file_path:
            self.controller.load_image(file_path)

    def _on_slider_changed(self, value: int) -> None:
        real_value = value / 10.0
        self.exposure_label.setText(f"Экспозиция: {real_value:.1f}")
        self.controller.on_exposure_value_changed(real_value)

    def _render_container(self, container: FrameContainer) -> None:
        """
        Takes the container and displays its cached image on the scene.
        """
        display_array = container.get_display_image()
        pixmap = numpy_to_qpixmap(display_array)
        
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        
        # We can center the scene items if we want, or just let scrollbars handle it
        self.canvas_view.setSceneRect(self.scene.itemsBoundingRect())

    def _on_canvas_wheel_event(self, event) -> None:
        """
        Basic zoom with mouse wheel.
        """
        zoom_in_factor = 1.15
        zoom_out_factor = 1.0 / zoom_in_factor
        
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
            
        self.canvas_view.scale(zoom_factor, zoom_factor)
