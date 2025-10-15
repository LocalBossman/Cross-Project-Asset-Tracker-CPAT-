#/---Cross-Project-Asset-Tracker-CPAT---/

"""
This is a standalone PySide6 application that connects with Unreal Engine to scan project assets.
It uses QWidget layouts (QVBoxLayout, QHBoxLayout, etc.) to control positioning and color styling.
Each part of the UI corresponds to the diagram you provided.
"""

import unreal
import os
import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QMainWindow, QTextEdit, QTableWidget, QTableWidgetItem
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor, QFont


class CPAT(QMainWindow):
    """
    CPAT (Cross Project Asset Tracker)
    - QMainWindow: provides menu bars, title bar, and a central area
    """

    #---------------------------------- Backend Logic ----------------------------------#
    def scan(self, content_dir):
        """
        Scans the Unreal Content folder for .uasset files.
        Returns a list of dictionaries with name, path, and size.
        """
        asset_data = []
        total_size = 0

        for root, dirs, files in os.walk(content_dir):
            for file in files:
                if file.endswith(".uasset"):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    total_size += size
                    asset_data.append({
                        "name": file,
                        "path": file_path,
                        "size_mb": round(size / (1024 * 1024), 2)
                    })

        unreal.log(f"Scanned {len(asset_data)} assets. "
                   f"Total size: {round(total_size / (1024*1024), 2)} MB")

        return asset_data

    #---------------------------------- UI Setup ----------------------------------#
    def __init__(self, parent=None):
        """
        Initializes the QMainWindow, sets up colors, fonts, and layout structure.
        """
        super(CPAT, self).__init__(parent)
        self.setWindowTitle("Cross Project Asset Tracker (CPAT)")
        self.setFixedSize(QSize(900, 550))

        # Get Unreal's project content folder
        self.project_content_dir = unreal.Paths.project_content_dir()

        # Apply a dark theme palette
        self.set_dark_theme()

        # Build all UI widgets and layouts
        self.init_ui()

    def set_dark_theme(self):
        """Applies a dark theme to the entire window."""
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(20, 20, 20))        # background
        palette.setColor(QPalette.WindowText, Qt.white)              # text
        palette.setColor(QPalette.Button, QColor(60, 60, 60))        # buttons
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))          # text areas
        palette.setColor(QPalette.Text, Qt.white)
        self.setPalette(palette)

    def init_ui(self):
        """
        Constructs all visual elements and arranges them using Qt layouts.
        """

        # Main container widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Top layout (Title bar)
        title_label = QLabel("Cross Project Asset Tracker (CPAT)")
        title_label.setFont(QFont("Arial", 14, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)

        # --- Project selection and scan buttons ---
        button_layout = QHBoxLayout()
        self.select_button = QPushButton("Select Projects")
        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.on_scan_clicked)
        self.set_button_style(self.select_button)
        self.set_button_style(self.scan_button)
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.scan_button)

        # --- Summary display section (Total, Duplicates, etc.) ---
        summary_layout = QHBoxLayout()
        self.total_label = QLabel("Total Assets: 0")
        self.dup_label = QLabel("Duplicates: 0")
        self.unused_label = QLabel("Unused: 0")
        self.shared_label = QLabel("Shared: 0")

        for lbl in [self.total_label, self.dup_label, self.unused_label, self.shared_label]:
            lbl.setFont(QFont("Consolas", 11))
            summary_layout.addWidget(lbl)

        # --- Asset Table (name, project, size, status, path) ---
        self.asset_table = QTableWidget()
        self.asset_table.setColumnCount(5)
        self.asset_table.setHorizontalHeaderLabels(["Asset Name", "Project", "Size", "Status", "Path"])
        self.asset_table.horizontalHeader().setStretchLastSection(True)
        self.asset_table.setFixedHeight(250)
        self.asset_table.setStyleSheet("""
            QTableWidget {
                background-color: #2b2b2b;
                color: white;
                gridline-color: gray;
                border: 1px solid gray;
            }
            QHeaderView::section {
                background-color: #444;
                color: white;
            }
        """)

        # --- Bottom buttons ---
        bottom_layout = QHBoxLayout()
        self.remove_button = QPushButton("Remove")
        self.ignore_button = QPushButton("Marked Read")
        self.move_button = QPushButton("Move to Safe Folder")

        for btn in [self.remove_button, self.ignore_button, self.move_button]:
            self.set_button_style(btn)
            bottom_layout.addWidget(btn)

        # --- Output Log Box ---
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(100)

        # --- Main Layout Assembly (vertical stacking) ---
        main_layout = QVBoxLayout()
        main_layout.addWidget(title_label)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(summary_layout)
        main_layout.addWidget(self.asset_table)
        main_layout.addLayout(bottom_layout)
        main_layout.addWidget(self.output_box)

        # Apply the layout to the central widget
        central_widget.setLayout(main_layout)

    def set_button_style(self, button):
        """Applies consistent dark styling and fixed size to buttons."""
        button.setFixedSize(150, 40)
        button.setStyleSheet("""
            QPushButton {
                background-color: #3a3a3a;
                color: white;
                border-radius: 8px;
                border: 1px solid gray;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #282828;
            }
        """)

    #---------------------------------- Button Actions ----------------------------------#
    def on_scan_clicked(self):
        """
        Runs when 'Scan' is clicked. Scans project assets, updates labels, and populates the table.
        """
        self.output_box.clear()
        assets = self.scan(self.project_content_dir)

        # Update summary
        self.total_label.setText(f"Total Assets: {len(assets)}")
        self.dup_label.setText("Duplicates: 0")  # placeholder for future detection
        self.unused_label.setText("Unused: 0")
        self.shared_label.setText("Shared: 0")

        # Populate table with first few assets
        self.asset_table.setRowCount(len(assets))
        for row, a in enumerate(assets[:len(assets)]):
            self.asset_table.setItem(row, 0, QTableWidgetItem(a['name']))
            self.asset_table.setItem(row, 1, QTableWidgetItem("Current Project"))
            self.asset_table.setItem(row, 2, QTableWidgetItem(f"{a['size_mb']} MB"))
            self.asset_table.setItem(row, 3, QTableWidgetItem("OK"))
            self.asset_table.setItem(row, 4, QTableWidgetItem(a['path']))

        # Output log
        summary = f"Scanned {len(assets)} assets.\n"
        self.output_box.append(summary)


#---------------------------------- Run Code ----------------------------------#
def main():
    """
    Ensures there is only one QApplication instance and launches the CPAT window.
    """
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = CPAT()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()

