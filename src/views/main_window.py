import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QSplitter, 
    QListWidget, QFileDialog, QListWidgetItem, QLabel
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from src.controllers.main_controller import MainController
from src.utils.converters import numpy_to_qpixmap
from src.views.canvas.viewport import CanvasViewport
from src.views.panels.inspector import InspectorPanel
from src.views.panels.sequence_panel import SequencePanel


class MainWindow(QMainWindow):
    """
    Main Application Window providing the 3-column UI layout and Main Menu.
    """
    def __init__(self, controller: MainController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("SilverLab MVP v0.3")
        self.resize(1200, 800)

        self._setup_ui()
        self._setup_menu()
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
        batch_export_action.triggered.connect(self._on_batch_export_clicked)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Выход (Exit)")
        exit_action.triggered.connect(self.close)

        # 2. View/Tools Menu
        tools_menu = menu_bar.addMenu("Инструменты (Tools)")
        tools_menu.addAction("Перемещение (Pan)").triggered.connect(self.canvas_viewport._activate_pan_tool)
        tools_menu.addAction("Кадрирование (Crop)").triggered.connect(self.canvas_viewport._activate_crop_tool)
        tools_menu.addAction("Линейка (Straighten)").triggered.connect(self.canvas_viewport._activate_straighten_tool)
        tools_menu.addAction("Пипетка ББ (Picker)").triggered.connect(self.canvas_viewport._activate_picker_tool)
        
        # 3. Pipeline Menu
        pipeline_menu = menu_bar.addMenu("Конвейер (Pipeline)")
        pipeline_menu.addAction("Добавить фильтр... (Add Node)").triggered.connect(self.inspector_panel._show_node_picker)
        pipeline_menu.addAction("Сбросить все настройки (Reset All)").triggered.connect(lambda: print("Not implemented yet"))
        pipeline_menu.addAction("Применить ко всем файлам (Apply to all)").triggered.connect(self.controller.apply_to_all)
        pipeline_menu.addAction("Загрузить пресет (Load Preset)").triggered.connect(lambda: print("Load preset not implemented"))
        pipeline_menu.addAction("Сохранить пресет (Save Preset)").triggered.connect(lambda: print("Save preset not implemented"))

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
        self.sequence_panel = SequencePanel(self.controller)
        splitter.addWidget(self.sequence_panel)

        # 2. Central Panel (Canvas Viewport)
        self.canvas_viewport = CanvasViewport(self.controller)
        splitter.addWidget(self.canvas_viewport)

        # 3. Right Panel (Inspector)
        self.inspector_panel = InspectorPanel(self.controller)
        splitter.addWidget(self.inspector_panel)

        # Set initial splitter sizes
        splitter.setSizes([200, 700, 300])
        
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Готово")
        
        self.zoom_label = QLabel("Zoom: 100%")
        self.status_bar.addPermanentWidget(self.zoom_label)

    def _connect_signals(self) -> None:
        # Controller bindings
        self.controller.status_message_changed.connect(self.status_bar.showMessage)
        self.controller.tool_activation_requested.connect(self._on_tool_activation_requested)

    def _on_tool_activation_requested(self, tool_name: str) -> None:
        if tool_name == 'straighten':
            self.canvas_viewport._activate_straighten_tool()
        elif tool_name == 'picker':
            self.canvas_viewport._activate_picker_tool()

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
        default_name = ""
        active_item = self.controller.sequence.get_item_at(self.controller.sequence.active_index)
        if active_item and active_item.file_path:
            base = os.path.splitext(os.path.basename(active_item.file_path))[0]
            default_name = f"{base}.jpg"
            
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", default_name, "JPEG (*.jpg);;TIFF (*.tiff);;PNG (*.png)"
        )
        if save_path:
            success = self.controller.save_current_image(save_path)
            if success:
                self.status_bar.showMessage(f"Saved successfully to {save_path}", 3000)
            else:
                self.status_bar.showMessage(f"Failed to save {save_path}", 3000)
                
    def _on_batch_export_clicked(self) -> None:
        folder_path = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if folder_path:
            self.controller.batch_export(folder_path)
