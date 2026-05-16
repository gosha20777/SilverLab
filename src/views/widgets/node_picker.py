from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QListWidget, QPushButton, QHBoxLayout, 
    QLabel, QLineEdit, QSplitter, QWidget, QListWidgetItem, QFrame,
    QTextBrowser, QComboBox
)
from PySide6.QtCore import Qt, QSettings, QUrl
from PySide6.QtGui import QIcon, QFont, QDesktopServices
from src.core.isp.plugin_manager import plugin_manager

class NodeCardWidget(QWidget):
    """Custom widget for a node item in the list."""
    def __init__(self, node_type: str, info: dict, is_favorite: bool, toggle_fav_cb):
        super().__init__()
        self.node_type = node_type
        self.info = info
        self.is_favorite = is_favorite
        self.toggle_fav_cb = toggle_fav_cb
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Left side: Text info
        text_layout = QVBoxLayout()
        title_label = QLabel(info.get("title", node_type))
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        
        desc_label = QLabel(info.get("description_short", ""))
        desc_label.setStyleSheet("color: #888; font-size: 11px;")
        desc_label.setWordWrap(True)
        
        tags = info.get("tags", [])
        tags_str = ", ".join(tags) if tags else ""
        tags_label = QLabel(tags_str)
        tags_label.setStyleSheet("color: #0078D7; font-size: 10px; font-weight: bold;")
        
        text_layout.addWidget(title_label)
        text_layout.addWidget(desc_label)
        text_layout.addWidget(tags_label)
        
        layout.addLayout(text_layout, stretch=1)
        
        # Right side: Favorite button
        self.fav_btn = QPushButton("★" if is_favorite else "☆")
        self.fav_btn.setFixedSize(30, 30)
        self.fav_btn.setStyleSheet(
            "QPushButton { font-size: 20px; color: gold; border: none; background: transparent; }"
            "QPushButton:hover { background: #333; border-radius: 15px; }"
        )
        self.fav_btn.clicked.connect(self._on_fav_clicked)
        layout.addWidget(self.fav_btn, alignment=Qt.AlignTop)

    def _on_fav_clicked(self):
        self.is_favorite = not self.is_favorite
        self.fav_btn.setText("★" if self.is_favorite else "☆")
        self.toggle_fav_cb(self.node_type, self.is_favorite)


class NodePickerDialog(QDialog):
    """
    Dialog window allowing the user to select a new ISP node to append to the pipeline.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить фильтр (Node Picker)")
        self.resize(800, 500)
        
        self.settings = QSettings("SilverLab", "Preferences")
        favs = self.settings.value("favorite_nodes", [])
        if isinstance(favs, str):
            self.favorites = [favs]
        else:
            self.favorites = list(favs)
            
        self.available_nodes = [] # List of tuples: (node_type, info_dict, config_cls)
        for node_type in plugin_manager.get_all_node_types():
            config_cls = plugin_manager.get_config_class(node_type)
            if config_cls:
                if hasattr(config_cls, 'get_node_info'):
                    info = config_cls.get_node_info()
                else:
                    info = {"title": node_type, "description_short": "", "group": "Разное"}
                self.available_nodes.append((node_type, info, config_cls))
                
        self.selected_config_cls = None
        self._build_ui()
        self._populate_list()
        
    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Top filters
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск фильтров...")
        self.search_input.textChanged.connect(self._populate_list)
        
        self.group_combo = QComboBox()
        self.group_combo.addItem("Все группы")
        self.group_combo.addItem("Избранные ★")
        groups = set(info.get("group", "Разное") for _, info, _ in self.available_nodes)
        for g in sorted(groups):
            self.group_combo.addItem(g)
        self.group_combo.currentTextChanged.connect(self._populate_list)
        
        filter_layout.addWidget(self.search_input, stretch=2)
        filter_layout.addWidget(self.group_combo, stretch=1)
        main_layout.addLayout(filter_layout)
        
        # Splitter for left/right panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left Panel: List
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        splitter.addWidget(self.list_widget)
        
        # Right Panel: Details
        self.details_panel = QWidget()
        details_layout = QVBoxLayout(self.details_panel)
        
        self.detail_title = QLabel("Выберите фильтр")
        font = self.detail_title.font()
        font.setPointSize(16)
        font.setBold(True)
        self.detail_title.setFont(font)
        
        self.detail_author = QLabel("")
        self.detail_author.setStyleSheet("color: #888;")
        
        self.detail_desc = QTextBrowser()
        self.detail_desc.setOpenExternalLinks(True)
        self.detail_desc.setStyleSheet("background: transparent; border: none;")
        
        self.add_btn = QPushButton("Добавить в пайплайн")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.add_btn.setEnabled(False)
        self.add_btn.clicked.connect(self.accept)
        
        details_layout.addWidget(self.detail_title)
        details_layout.addWidget(self.detail_author)
        details_layout.addWidget(self.detail_desc)
        details_layout.addWidget(self.add_btn)
        
        splitter.addWidget(self.details_panel)
        splitter.setSizes([350, 450])
        
        main_layout.addWidget(splitter)
        
    def _toggle_favorite(self, node_type: str, is_fav: bool):
        if is_fav and node_type not in self.favorites:
            self.favorites.append(node_type)
        elif not is_fav and node_type in self.favorites:
            self.favorites.remove(node_type)
        self.settings.setValue("favorite_nodes", self.favorites)
        
        # If we are viewing "Favorites Only", refresh the list
        if self.group_combo.currentText() == "Избранные ★":
            self._populate_list()

    def _populate_list(self):
        self.list_widget.clear()
        search_text = self.search_input.text().lower()
        selected_group = self.group_combo.currentText()
        
        # Sort nodes: Favorites first, then alphabetical by group, then title
        def sort_key(item):
            ntype, info, _ = item
            is_fav = 0 if ntype in self.favorites else 1
            return (is_fav, info.get("group", ""), info.get("title", ""))
            
        sorted_nodes = sorted(self.available_nodes, key=sort_key)
        
        for node_type, info, config_cls in sorted_nodes:
            # Filter by Search
            title = info.get("title", node_type).lower()
            desc = info.get("description_short", "").lower()
            tags = " ".join(info.get("tags", [])).lower()
            if search_text and search_text not in title and search_text not in desc and search_text not in tags:
                continue
                
            # Filter by Group
            if selected_group == "Избранные ★":
                if node_type not in self.favorites:
                    continue
            elif selected_group != "Все группы":
                if info.get("group", "Разное") != selected_group:
                    continue
                    
            item = QListWidgetItem(self.list_widget)
            is_fav = node_type in self.favorites
            widget = NodeCardWidget(node_type, info, is_fav, self._toggle_favorite)
            
            # Save data to item for selection handling
            item.setData(Qt.UserRole, (node_type, info, config_cls))
            item.setSizeHint(widget.sizeHint())
            
            self.list_widget.setItemWidget(item, widget)
            
        self._on_selection_changed()

    def _on_selection_changed(self):
        items = self.list_widget.selectedItems()
        if not items:
            self.detail_title.setText("Выберите фильтр")
            self.detail_author.setText("")
            self.detail_desc.setHtml("")
            self.add_btn.setEnabled(False)
            self.selected_config_cls = None
            return
            
        node_type, info, config_cls = items[0].data(Qt.UserRole)
        self.selected_config_cls = config_cls
        
        self.detail_title.setText(info.get("title", node_type))
        
        author = info.get("author", "")
        group = info.get("group", "")
        self.detail_author.setText(f"Автор: {author} | Категория: {group}")
        
        desc_long = info.get("description_long", info.get("description_short", ""))
        url = info.get("url", "")
        
        html = f"<p style='font-size: 13px; line-height: 1.4;'>{desc_long}</p>"
        
        tags = info.get("tags", [])
        if tags:
            html += f"<p><b>Теги:</b> {', '.join(tags)}</p>"
            
        if url:
            html += f"<p><a href='{url}'>Подробнее (ссылка)</a></p>"
            
        self.detail_desc.setHtml(html)
        self.add_btn.setEnabled(True)
        
    def get_selected_config(self):
        """
        Returns a new instance of the selected Pydantic node config.
        """
        if self.selected_config_cls:
            return self.selected_config_cls()
        return None
