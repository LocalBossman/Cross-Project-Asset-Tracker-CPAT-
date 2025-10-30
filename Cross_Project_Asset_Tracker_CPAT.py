#/---Cross-Project-Asset-Tracker-CPAT---/

#TODO 
#improve on gui
#Improve on Duplicate detection

import os
import re
import sys
import shutil
import unreal
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

#/------------------------Tool Menu---------------------------/#
class CPATMenu:
    def __init__(self):
        self.tool_menus = unreal.ToolMenus.get()
        self.menu_owner = "CPAT"
        self.menu_name = "LevelEditor.MainMenu.CPAT"
        self.cpat_menu = None

    def create_menu(self):
        unreal.log("Creating CPAT Menu...")
        main_menu = self.tool_menus.find_menu("LevelEditor.MainMenu")
        self.cpat_menu = main_menu.add_sub_menu(
            section_name="CPAT Tool",
            name=self.menu_owner,
            owner=self.menu_owner,
            label="CPAT"
        )
        self.cpat_menu = self.tool_menus.register_menu(
            self.menu_name, "", unreal.MultiBoxType.MENU, True
        )
        self.tool_menus.refresh_all_widgets()

    def create_menu_entry(self):
        unreal.log("Creating CPAT entry...")
        module_name = "Cross_Project_Asset_Tracker_CPAT"
        command = f"import {module_name}; {module_name}.main()"
        menu_entry = unreal.ToolMenuEntryExtensions.init_menu_entry(
            owner=self.menu_owner,
            name=self.menu_owner,
            label="CPAT",
            tool_tip="Run CPAT",
            command_type=unreal.ToolMenuStringCommandType.PYTHON,
            custom_command_type="",
            command_string=command
        )
        icon = "AnimEditor.FilterSearch"
        menu_entry.set_icon("EditorStyle", icon)
        self.cpat_menu.add_menu_entry("Utils", menu_entry)
        self.tool_menus.refresh_all_widgets()

#/------------------------UI Class---------------------------/#
class CPAT(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPAT")
        self.setFixedSize(800, 550)
        self.selected_project_dir = unreal.Paths.project_content_dir()
        self.setup_ui()

#/---------------------------UI---------------------------/#
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        title = QLabel("Cross Project Asset Tracker (CPAT)")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Arial", 19))

        self.select_button = QPushButton("Select Folder")
        self.scan_button = QPushButton("Scan")
        self.remove_button = QPushButton("Remove")
        self.move_button = QPushButton("Move to Safe Folder")

        self.select_button.clicked.connect(self.select_folder)
        self.scan_button.clicked.connect(self.on_scan_clicked)
        self.remove_button.clicked.connect(self.remove_asset)
        self.move_button.clicked.connect(self.move_to_safe_folder)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.scan_button)

        self.total_text = QLabel("Total: 0")
        self.duplicate_text = QLabel("Duplicates: 0")
        self.unused_text = QLabel("Unused: 0")
        self.oversized_text = QLabel("Oversized: 0")

        for label in [self.total_text, self.duplicate_text, self.unused_text, self.oversized_text]:
            label.setFont(QFont("Arial", 14))

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.total_text)
        summary_layout.addWidget(self.duplicate_text)
        summary_layout.addWidget(self.unused_text)
        summary_layout.addWidget(self.oversized_text)
        summary_layout.setSpacing(5)

        self.asset_table = QTableWidget(0, 4)
        self.asset_table.setHorizontalHeaderLabels(["Name", "Status", "Size MB", "Path"])
        self.asset_table.horizontalHeader().setStretchLastSection(True)
        self.asset_table.setFixedHeight(230)

        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(100)

        action_layout = QHBoxLayout()
        action_layout.addWidget(self.remove_button)
        action_layout.addWidget(self.move_button)

        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addLayout(summary_layout)
        layout.addWidget(self.asset_table)
        layout.addLayout(action_layout)
        layout.addWidget(self.output_box)

        central.setLayout(layout)

#/------------------------Folder Selection------------------------/#
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.selected_project_dir = folder
            self.output_box.append(f"Selected folder: {folder}")

#/------------------------Scan Unreal Project------------------------/#
    def scan_unreal_project(self):
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry.search_all_assets(True)
        all_assets = registry.get_assets_by_path("/Game", recursive=True)

        assets = []
        references = {}

        # Gather assets and their references
        for a in all_assets:
            name = str(a.asset_name)
            path = str(a.object_path)
            size_mb = 0
            try:
                file_path = unreal.Paths.convert_relative_path_to_full(a.package_name)
                size_mb = round(os.path.getsize(file_path + ".uasset") / (1024 * 1024), 2)
            except Exception:
                pass

            assets.append({"name": name, "path": path, "size_mb": size_mb})
            refs = unreal.EditorAssetLibrary.find_package_referencers_for_asset(path, True)
            references[path] = refs

        # --- Duplicate Detection ---
        base_groups = {}
        for a in assets:
            base = re.sub(r'(_\d+|_Copy.*|_C|_Inst)$', '', a["name"].lower())
            base_groups.setdefault(base, []).append(a)
        duplicates = [a["name"] for group in base_groups.values() if len(group) > 1 for a in group]

        # --- Unused Detection ---
        unused = [a["path"] for a in assets if not references.get(a["path"])]

        # --- Oversized Detection ---
        threshold = 10.0
        oversized = [a["name"] for a in assets if a["size_mb"] > threshold]

        return assets, duplicates, unused, oversized

#/------------------------Scan External Folder------------------------/#
    def scan_external_folder(self, folder):
        assets = []
        threshold = 10.0

        # Gather all assets
        for root, _, files in os.walk(folder):
            for f in files:
                if f.endswith(".uasset"):
                    path = os.path.join(root, f)
                    size = round(os.path.getsize(path) / (1024 * 1024), 2)
                    assets.append({"name": f, "path": path, "size_mb": size})

        # --- Duplicate Detection ---
        base_groups = {}
        for a in assets:
            base = re.sub(r'(_\d+|_Copy.*)$', '', a["name"]).lower()
            base_groups.setdefault(base, []).append(a)
        duplicates = [g["name"] for group in base_groups.values() if len(group) > 1 for g in group]

        # --- Oversized Detection ---
        oversized = [a["name"] for a in assets if a["size_mb"] > threshold]

        # --- Heuristic Unused Detection ---
        referenced_files = set()
        for a in assets:
            try:
                with open(a["path"], 'rb') as f:
                    content = f.read().decode(errors='ignore')
                    for other in assets:
                        if other["name"][:-7] in content and other["name"] != a["name"]:
                            referenced_files.add(other["name"])
            except Exception:
                continue

        unused = [a["name"] for a in assets if a["name"] not in referenced_files]

        return assets, duplicates, unused, oversized

#/------------------------Scan Button------------------------/#
    def on_scan_clicked(self):
        self.output_box.clear()
        self.output_box.append("Scanning...")

        if self.selected_project_dir == unreal.Paths.project_content_dir():
            assets, duplicates, unused, oversized = self.scan_unreal_project()
            mode = "Unreal Project"
        else:
            assets, duplicates, unused, oversized = self.scan_external_folder(self.selected_project_dir)
            mode = "External Folder"

        self.total_text.setText(f"Total: {len(assets)}")
        self.duplicate_text.setText(f"Duplicates: {len(duplicates)}")
        self.unused_text.setText(f"Unused: {len(unused)}")
        self.oversized_text.setText(f"Oversized: {len(oversized)}")

        self.asset_table.setRowCount(len(assets))
        for i, a in enumerate(assets):
            status = "Okay"
            name_lower = re.sub(r'(_\d+|_Copy.*|_C|_Inst)$', '', a["name"].lower())
            dup_norm = [re.sub(r'(_\d+|_Copy.*|_C|_Inst)$', '', d.lower()) for d in duplicates]

            if name_lower in dup_norm:
                status = "Duplicate"
            elif a["name"] in unused or a["path"] in unused:
                status = "Unused"
            elif a["name"] in oversized:
                status = "Oversized"

            row_items = [
                QTableWidgetItem(a["name"]),
                QTableWidgetItem(status),
                QTableWidgetItem(str(a["size_mb"])),
                QTableWidgetItem(a["path"])
            ]

            color_map = {
                "Duplicate": QColor(255, 150, 150),
                "Unused": QColor(255, 200, 100),
                "Oversized": QColor(255, 255, 120),
                "Okay": QColor(200, 255, 200)
            }
            row_items[1].setBackground(color_map[status])

            for col, item in enumerate(row_items):
                self.asset_table.setItem(i, col, item)

        self.output_box.append(f"Scan complete ({mode})")

#/------------------------Remove Button------------------------/#
    def remove_asset(self):
        row = self.asset_table.currentRow()
        if row < 0:
            self.output_box.append("No asset selected to remove.")
            return

        asset_name = self.asset_table.item(row, 0).text()
        asset_path = self.asset_table.item(row, 3).text()

        confirm = QMessageBox.question(
            self, "Confirm", f"Delete {asset_name}?", 
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.No:
            return

        if self.selected_project_dir != unreal.Paths.project_content_dir():
            try:
                os.remove(asset_path)
                self.output_box.append(f"Deleted file: {asset_path}")
                self.asset_table.removeRow(row)
            except Exception as e:
                self.output_box.append(f"Error deleting: {e}")
        else:
            try:
                if unreal.EditorAssetLibrary.delete_asset(asset_path):
                    self.output_box.append(f"Deleted Unreal asset: {asset_path}")
                    self.asset_table.removeRow(row)
                else:
                    self.output_box.append("Failed to delete Unreal asset.")
            except Exception as e:
                self.output_box.append(f"Error: {e}")

#/------------------------Move to Safe Folder Button------------------------/#
    def move_to_safe_folder(self):
        row = self.asset_table.currentRow()
        if row < 0:
            self.output_box.append("Nothing selected to move.")
            return

        asset_name = self.asset_table.item(row, 0).text()
        asset_path = self.asset_table.item(row, 3).text()
        safe_folder_path = os.path.join(unreal.Paths.project_content_dir(), "SafeFolder")
        os.makedirs(safe_folder_path, exist_ok=True)

        if self.selected_project_dir != unreal.Paths.project_content_dir():
            try:
                dest = os.path.join(safe_folder_path, os.path.basename(asset_path))
                shutil.move(asset_path, dest)
                self.output_box.append(f"Moved to SafeFolder: {dest}")
                self.asset_table.removeRow(row)
            except Exception as e:
                self.output_box.append(f"Error moving file: {e}")
        else:
            try:
                dest = "/Game/SafeFolder/" + asset_name
                unreal.EditorAssetLibrary.make_directory("/Game/SafeFolder")
                if unreal.EditorAssetLibrary.rename_asset(asset_path, dest):
                    self.output_box.append(f"Moved Unreal asset to SafeFolder: {dest}")
                    self.asset_table.removeRow(row)
                else:
                    self.output_box.append("Failed to move asset.")
            except Exception as e:
                self.output_box.append(f"Error moving Unreal asset: {e}")

#/------------------------Run Code------------------------/#
def main():
    menu = CPATMenu()
    menu.create_menu()
    menu.create_menu_entry()
    app = QApplication.instance() or QApplication(sys.argv)
    win = CPAT()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()