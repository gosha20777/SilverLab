import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QSplitter, 
    QListWidget, QPushButton, QSlider, QLabel, QFileDialog,
    QGraphicsView, QGraphicsScene, QListWidgetItem, QMenuBar, QMenu
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from src.controllers.main_controller import MainController
from src.models.frame_container import FrameContainer
from src.utils.converters import numpy_to_qpixmap


class MainWindow(QMainWindow):
    """
    Main Application Window providing the 3-column UI layout and Main Menu.
    """
    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SilverLab MVP v0.2")
        self.resize(1200, 800)

        self._setup_menu()
        self._setup_ui()
        self._connect_signals()

    def _setup_menu(self) -> None:
        menu_bar = self.menuBar()
        
        # 1. File Menu
        file_menu = menu_bar.addMenu("Файл (File)")
        
        open_image_action = file_menu.addAction("Открыть скан (Open Image)...")
        open_image_action.triggered.connect(self._on_load_clicked)
        
        open_folder_action = file_menu.addAction("Открыть папку (Open Folder)...")
        open_folder_action.triggered.connect(self._on_load_folder_clicked)
        
        save_current_action = file_menu.addAction("Сохранить текущий (Save Current)...")
        save_current_action.triggered.connect(self._on_save_current_clicked)
        
        file_menu.addSeparator()
        
        batch_export_action = file_menu.addAction("Пакетный экспорт (Batch Export)...")
        batch_export_action.triggered.connect(lambda: print("Batch export not implemented"))
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Выход (Exit)")
        exit_action.triggered.connect(self.close)

        # 2. Image Menu
        image_menu = menu_bar.addMenu("Изображение (Image)")
        
        tools_menu = image_menu.addMenu("Инструменты (Tools)")
        tools_menu.addAction("Кадрирование (Crop)").triggered.connect(lambda: print("Crop mock"))
        tools_menu.addAction("Баланс белого (White Balance)").triggered.connect(lambda: print("WB mock"))
        
        geometry_menu = image_menu.addMenu("Геометрия (Geometry)")
        geometry_menu.addAction("Поворот на 90° по ч.с.").triggered.connect(lambda: print("Rotate CW mock"))
        geometry_menu.addAction("Поворот на 90° против ч.с.").triggered.connect(lambda: print("Rotate CCW mock"))
        geometry_menu.addAction("Авто-выравнивание").triggered.connect(lambda: print("Auto-straighten mock"))
        
        image_menu.addSeparator()
        image_menu.addAction("Сбросить настройки (Reset Settings)").triggered.connect(lambda: print("Reset mock"))

        # 3. Pipeline Menu
        pipeline_menu = menu_bar.addMenu("Конвейер (Pipeline)")
        pipeline_menu.addAction("Управление узлами (Manage Nodes)").triggered.connect(lambda: print("Manage nodes mock"))
        pipeline_menu.addAction("Загрузить пресет (Load Preset)").triggered.connect(lambda: print("Load preset mock"))
        pipeline_menu.addAction("Сохранить пресет (Save Preset)").triggered.connect(lambda: print("Save preset mock"))

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
        # Set IconMode for thumbnail gallery
        self.gallery_list.setViewMode(QListWidget.IconMode)
        self.gallery_list.setIconSize(QSize(120, 120))
        self.gallery_list.setResizeMode(QListWidget.Adjust)
        self.gallery_list.setSpacing(10)
        
        splitter.addWidget(self.gallery_list)

        # 2. Central Panel (Canvas)
        self.scene = QGraphicsScene()
        self.canvas_view = QGraphicsView(self.scene)
        self.canvas_view.setStyleSheet("background-color: #2b2b2b;")
        splitter.addWidget(self.canvas_view)

        # 3. Right Panel (Inspector)
        inspector_widget = QWidget()
        inspector_layout = QVBoxLayout(inspector_widget)
        
        self.load_button = QPushButton("Загрузить папку (Load Folder)")
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
        self.load_button.clicked.connect(self._on_load_folder_clicked)
        self.exposure_slider.valueChanged.connect(self._on_slider_changed)
        
        self.align_button.clicked.connect(lambda: print("Auto-align not implemented yet."))
        self.split_button.clicked.connect(lambda: print("Split diptych not implemented yet."))

        # Connect controller signals
        self.controller.image_loaded.connect(self._render_container)
        self.controller.image_processed.connect(self._render_container)
        self.controller.folder_loaded.connect(self._on_folder_loaded)
        self.controller.thumbnail_ready.connect(self._add_thumbnail_to_gallery)
        
        # Gallery clicks
        self.gallery_list.itemClicked.connect(self._on_gallery_item_clicked)

    def _on_load_clicked(self) -> None:
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Open Image(s)", "", "Images (*.tiff *.tif *.jpg *.jpeg *.png)"
        )
        if file_paths:
            self.controller.load_files(file_paths)

    def _on_load_folder_clicked(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            self.controller.load_folder(folder_path)

    def _on_save_current_clicked(self) -> None:
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "JPEG (*.jpg);;TIFF (*.tiff);;PNG (*.png)"
        )
        if save_path:
            success = self.controller.save_current_image(save_path)
            if success:
                print(f"Saved successfully to {save_path}")
            else:
                print(f"Failed to save {save_path}")

    def _on_folder_loaded(self) -> None:
        self.gallery_list.clear()

    def _add_thumbnail_to_gallery(self, file_path: str, thumbnail_data: object) -> None:
        pixmap = numpy_to_qpixmap(thumbnail_data)
        icon = QIcon(pixmap)
        
        item = QListWidgetItem(icon, os.path.basename(file_path))
        # Store full path in data for easy retrieval
        item.setData(Qt.UserRole, file_path) 
        self.gallery_list.addItem(item)

    def _on_gallery_item_clicked(self, item: QListWidgetItem) -> None:
        file_path = item.data(Qt.UserRole)
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
