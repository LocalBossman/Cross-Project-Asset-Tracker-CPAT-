#/---Cross-Project-Asset-Tracker-CPAT---/

"""
This simplified version demonstrates:
- Scanning Unreal project assets or external folders
- Detecting duplicate assets and unused assets
- Displaying asset info in a table
- A placeholder "Remove" button
"""

import os
import re
import sys
import unreal  # Unreal Python API
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# ------------------------Class ------------------------ #
class CPAT(QMainWindow):

    def __init__(self):
        super().__init__()
        #Main Window
        self.setWindowTitle("CPAT")
        self.setFixedSize(800, 550)

        # Default folder is the current Unreal project Content folder
        self.selected_project_dir = unreal.Paths.project_content_dir()

        self.UI()

# ---------------------------UI--------------------------- #
    def UI(self):

        central = QWidget()
        self.setCentralWidget(central)

        # --- Title ---
        title = QLabel("Simple Cross Project Asset Tracker")
        title.setFont(QFont("Arial", 14))
        title.setAlignment(Qt.AlignCenter)  # Center the title text

        # --- Top Buttons ---
        # Button to select a folder to scan
        self.select_button = QPushButton("Select Folder")
        # Button to start scanning
        self.scan_button = QPushButton("Scan")
        # Connect buttons to their actions
        self.select_button.clicked.connect(self.select_folder)
        self.scan_button.clicked.connect(self.on_scan_clicked)

        # Layout to arrange buttons horizontally
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.scan_button)

        # --- Summary Labels ---
        # Labels to show total assets, duplicates, and unused assets
        self.total_label = QLabel("Total: 0")
        self.dup_label = QLabel("Duplicates: 0")
        self.unused_label = QLabel("Unused: 0")
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(self.total_label)
        summary_layout.addWidget(self.dup_label)
        summary_layout.addWidget(self.unused_label)

        # --- Asset Table ---
        # Table to display asset info: Name, Status, Size, Path
        self.asset_table = QTableWidget()
        self.asset_table.setColumnCount(4)
        self.asset_table.setHorizontalHeaderLabels(["Name", "Status", "Size MB", "Path"])
        self.asset_table.horizontalHeader().setStretchLastSection(True)
        self.asset_table.setFixedHeight(250)  # Fix height for layout simplicity

        # --- Output Log ---
        # Text box to display messages/logs
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(100)

        # --- Remove Button (Placeholder) ---
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self.remove_function)

        # --- Layout Assembly ---
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addLayout(summary_layout)
        layout.addWidget(self.asset_table)
        layout.addWidget(self.remove_button)  # Add the remove button below the table
        layout.addWidget(self.output_box)
        central.setLayout(layout)

# ------------------------Folder Select------------------------ #
    def select_folder(self):
        """
        Open a folder dialog to select a folder to scan.
        Updates self.selected_project_dir and logs the selection.
        """
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.selected_project_dir = folder
            self.output_box.append(f"Selected folder: {folder}")

    # ------------------------ EXTERNAL FOLDER SCAN ------------------------ #
    def scan_external_folder(self, folder):
        """
        Scan a folder on disk for .uasset files.
        Does NOT detect unused assets because references require Unreal AssetRegistry.
        """
        assets = []
        for root, _, files in os.walk(folder):  # Walk through folder recursively
            for f in files:
                if f.endswith(".uasset"):  # Only consider Unreal asset files
                    path = os.path.join(root, f)
                    size_mb = round(os.path.getsize(path) / (1024*1024), 2)  # Convert bytes to MB
                    assets.append({"name": f, "path": path, "size_mb": size_mb})

        # --- Duplicate detection ---
        # Remove common suffixes like "_1", "_Copy" for duplicate comparison
        base_groups = {}
        for a in assets:
            base = re.sub(r'(_\d+|_Copy.*)$', '', a["name"]).lower()
            base_groups.setdefault(base, []).append(a)

        duplicates = []
        for group in base_groups.values():
            if len(group) > 1:  # More than one asset with same base name
                duplicates.extend([g["name"] for g in group])

        unused = []  # Cannot detect without AssetRegistry
        return assets, duplicates, unused

# ------------------------Scan Unreal Project------------------------ #
    def scan_unreal_project(self):
        """
        Scan the current Unreal project using AssetRegistry.
        Detects actual duplicates and unused assets.
        """
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        all_assets = registry.get_assets_by_path("/Game", recursive=True)

        assets = []
        name_map = {}

        for a in all_assets:
            name = str(a.asset_name)
            path = str(a.object_path)
            # Try to get real file size
            try:
                file_path = unreal.Paths.convert_relative_path_to_full(a.object_path_name)
                size_mb = round(os.path.getsize(file_path) / (1024*1024), 2)
            except Exception:
                size_mb = 0
            assets.append({"name": name, "path": path, "size_mb": size_mb})
            name_map.setdefault(name.lower(), []).append(a)

        # --- Duplicate detection ---
        base_groups = {}
        for n in name_map.keys():
            base = re.sub(r'(_\d+|_Copy.*|_C|_Inst)$', '', n.lower())
            base_groups.setdefault(base, []).extend(name_map[n])

        duplicates = []
        for group in base_groups.values():
            if len(group) > 1:
                duplicates.extend([str(a.asset_name) for a in group])

        # --- Unused detection ---
        # If an asset has no references (hard or soft), it is considered unused
        unused = []
        for a in all_assets:
            refs = registry.get_referencers(a.package_name, recursive=True)
            refs = [r for r in refs if r != a.package_name]
            soft_refs = registry.get_soft_referencers(a.package_name, recursive=True)
            refs.extend([r for r in soft_refs if r != a.package_name])
            if not refs:
                unused.append(a.object_path)  # Store full path

        return assets, duplicates, unused

    # ------------------------Scan Button------------------------ #
    def on_scan_clicked(self):
        """
        Handle the Scan button click.
        Determines whether to scan the current Unreal project or an external folder.
        Updates the table and summary labels.
        """
        self.output_box.clear()
        self.output_box.append("Scanning...")

        # Decide scan mode
        if self.selected_project_dir == unreal.Paths.project_content_dir():
            assets, duplicates, unused = self.scan_unreal_project()
            mode = "Unreal Project"
        else:
            assets, duplicates, unused = self.scan_external_folder(self.selected_project_dir)
            mode = "External Folder"

        # Update summary labels
        self.total_label.setText(f"Total: {len(assets)}")
        self.dup_label.setText(f"Duplicates: {len(duplicates)}")
        self.unused_label.setText(f"Unused: {len(unused)}")

        # Fill the table
        self.asset_table.setRowCount(len(assets))
        duplicates_lower = [d.lower() for d in duplicates]  # Normalize for comparison

        for i, a in enumerate(assets):
            name_lower = a["name"].lower()
            if name_lower in duplicates_lower:
                status = "Duplicate"
            elif a["path"] in unused:
                status = "Unused"
            else:
                status = "OK"

            # Insert data into table cells
            self.asset_table.setItem(i, 0, QTableWidgetItem(a["name"]))
            self.asset_table.setItem(i, 1, QTableWidgetItem(status))
            self.asset_table.setItem(i, 2, QTableWidgetItem(str(a["size_mb"])))
            self.asset_table.setItem(i, 3, QTableWidgetItem(a["path"]))

        self.output_box.append(f"Scan complete ({mode})")

# ------------------------Remove Button------------------------ #

    #This is currently a place holder button it has no function
    def remove_function(self):

        selected = self.asset_table.currentRow()
        if selected >= 0:
            name_item = self.asset_table.item(selected, 0)
            if name_item:
                asset_name = name_item.text()
                self.output_box.append(f"Remove button clicked for: {asset_name}")
        else:
            self.output_box.append("No asset selected to remove.")

# ------------------------Run Code------------------------ #
def main():
    """Launch the CPAT application."""
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    window = CPAT()
    window.show()
    app.exec()

if __name__ == "__main__":
    main()
