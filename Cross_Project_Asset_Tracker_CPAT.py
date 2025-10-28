#/---Cross-Project-Asset-Tracker-CPAT---/

#TODO 
#improve on gui
#try get the detection system to detect unused and duplicates better
#function to detect oversized assets


import os 
import re
import sys
import shutil
import unreal
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QTableWidget, QTableWidgetItem, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor


#/------------------------Tool Menu---------------------------/#

class CPATmenu():
    def __init__(self):
        self.tool_menus = unreal.ToolMenus.get()
        self.menuOwner = "CPAT"
        self.tools_menu_name = "LevelEditor.MainMenu.CPAT"
        self.CPAT_menu = None

    def createMenu(self):
        unreal.log ("creating CPAT Menu...")

        mainMenu = self.tool_menus.find_menu("LevelEditor.MainMenu")
        self.CPAT_menu = mainMenu.add_sub_menu(section_name="CPAT Tool",
                                        name=self.menuOwner,
                                        owner=self.menuOwner,
                                        label="CPAT")
        self.CPAT_menu = self.tool_menus.register_menu(self.tools_menu_name, "",  unreal.MultiBoxType.MENU, True)
        
        self.tool_menus.refresh_all_widgets()

    def CreateMenuEntry(self):
        unreal.log("creating CPAT entry ...")

        module_name = "Cross_Project_Asset_Tracker_CPAT"
        command = f"import {module_name}; {module_name}.main()"

        menuEntry = unreal.ToolMenuEntryExtensions.init_menu_entry(
            owner=self.menuOwner,
            name =self.menuOwner,
            label="CPAT",
            tool_tip="Run CPAT",
            command_type= unreal.ToolMenuStringCommandType.PYTHON,
            custom_command_type= "",
            command_string= command
        )

        icon = "AnimEditor.FilterSearch"    
        menuEntry.set_icon("EditorStyle",icon)

        self.CPAT_menu.add_menu_entry("Utils", menuEntry)
        self.tool_menus.refresh_all_widgets()

menu = CPATmenu()
menu.createMenu()
menu.CreateMenuEntry()

#/------------------------UI Class ------------------------/#
class CPAT(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPAT")
        self.setFixedSize(800, 550)

        self.selected_project_dir = unreal.Paths.project_content_dir()
        self.UI()

#/---------------------------UI---------------------------/#
    def UI(self):
        central = QWidget()
        self.setCentralWidget(central)

        #Title label
        title = QLabel("Cross Project Asset Tracker (CPAT)")
        title.setAlignment(Qt.AlignCenter)

        #Buttons
        self.select_button = QPushButton("Select Folder")
        self.scan_button = QPushButton("Scan")
        self.remove_button = QPushButton("Remove")
        self.move_button = QPushButton("Move to Safe Folder")

        #Button Functions
        self.select_button.clicked.connect(self.select_folder)
        self.scan_button.clicked.connect(self.on_scan_clicked)
        self.remove_button.clicked.connect(self.remove_function)
        self.move_button.clicked.connect(self.move_to_safe_folder)

        #Top buttons
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.select_button)
        button_layout.addWidget(self.scan_button)

        #Ouput Labels
        self.total_text = QLabel("Total: 0")
        self.duplicate_text = QLabel("Duplicates: 0")
        self.unused_text = QLabel("Unused: 0")
        self.oversized_text = QLabel("Oversized: 0")

        summary_layout = QVBoxLayout()
        summary_layout.addWidget(self.total_text)
        summary_layout.addWidget(self.duplicate_text)
        summary_layout.addWidget(self.unused_text)
        summary_layout.addWidget(self.oversized_text)
        summary_layout.setSpacing(5)

        #Fonts
        title.setFont(QFont("Arial", 19))
        self.total_text.setFont(QFont("Arial", 14))
        self.duplicate_text.setFont(QFont("Arial", 14))
        self.unused_text.setFont(QFont("Arial", 14))
        self.oversized_text.setFont(QFont("Arial", 14))

        #Assets table
        self.asset_table = QTableWidget(0, 4)
        self.asset_table.setHorizontalHeaderLabels(["Name", "Status", "Size MB", "Path"])
        self.asset_table.horizontalHeader().setStretchLastSection(True)
        self.asset_table.setFixedHeight(230)

        #Output log
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedHeight(100)

        #Bottom buttons
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.remove_button)
        action_layout.addWidget(self.move_button)

        #Combines everything into a vertical layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addLayout(summary_layout)
        layout.addWidget(self.asset_table)
        layout.addLayout(action_layout)
        layout.addWidget(self.output_box)

        central.setLayout(layout)


#/------------------------Folder Select------------------------/#
    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.selected_project_dir = folder
            self.output_box.append(f"Selected folder: {folder}")


#/------------------------Folder Scan------------------------/#
    def scan_external_folder(self, folder):

        assets = []
        threshold = 10.0 

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

        unused = [] 

        return assets, duplicates, unused, oversized


#/------------------------Unreal Project Scan------------------------/#
    def scan_unreal_project(self):

        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        all_assets = registry.get_assets_by_path("/Game", recursive=True)

        assets, name_map = [], {}

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
            name_map.setdefault(name.lower(), []).append(a)

        # --- Duplicate Detection ---
        base_groups = {}
        for n in name_map:
            base = re.sub(r'(_\d+|_Copy.*|_C|_Inst)$', '', n.lower())
            base_groups.setdefault(base, []).extend(name_map[n])

        duplicates = [str(a.asset_name) for group in base_groups.values() if len(group) > 1 for a in group]

        # --- Unused Detection ---
        unused = []
        for a in all_assets:
            refs = registry.get_referencers(a.package_name, recursive=True)
            soft_refs = registry.get_soft_referencers(a.package_name, recursive=True)
            if not refs and not soft_refs:
                unused.append(a.object_path)

        # --- Oversized Detection ---
        threshold = 10.0 #MB
        oversized = [asset["name"] for asset in assets if asset["size_mb"] > threshold]

        return assets, duplicates, unused, oversized


#/------------------------Scan Button------------------------/#
    def on_scan_clicked(self):


        self.output_box.clear()
        self.output_box.append("Scanning...")

        # Decide if scanning Unreal project or external folder
        if self.selected_project_dir == unreal.Paths.project_content_dir():
            assets, duplicates, unused, oversized = self.scan_unreal_project()
            mode = "Unreal Project"
        else:
            assets, duplicates, unused, oversized = self.scan_external_folder(self.selected_project_dir)
            mode = "External Folder"

        # Update labels
        self.total_text.setText(f"Total: {len(assets)}")
        self.duplicate_text.setText(f"Duplicates: {len(duplicates)}")
        self.unused_text.setText(f"Unused: {len(unused)}")
        self.oversized_text.setText(f"Oversized: {len(oversized)}")

        # Populate table
        self.asset_table.setRowCount(len(assets))
        for i, a in enumerate(assets):
            name_lower = a["name"].lower()
            status = "Okay"
            if name_lower in [d.lower() for d in duplicates]:
                status = "Duplicate"
            elif a["path"] in unused:
                status = "Unused"
            elif a["name"] in [o for o in oversized]:
                status = "Oversized"

            # Table entries
            name_item = QTableWidgetItem(a["name"])
            status_item = QTableWidgetItem(status)
            size_item = QTableWidgetItem(str(a["size_mb"]))
            path_item = QTableWidgetItem(a["path"])

            # Color coding (for user testing clarity)
            if status == "Duplicate":
                status_item.setBackground(QColor(255, 150, 150))
            elif status == "Unused":
                status_item.setBackground(QColor(255, 200, 100))
            elif status == "Oversized":
                status_item.setBackground(QColor(255, 255, 120))
            else:
                status_item.setBackground(QColor(200, 255, 200))

            self.asset_table.setItem(i, 0, name_item)
            self.asset_table.setItem(i, 1, status_item)
            self.asset_table.setItem(i, 2, size_item)
            self.asset_table.setItem(i, 3, path_item)

        self.output_box.append(f"Scan complete ({mode})")


#/------------------------Remove Button------------------------/#
    def remove_function(self):

        row = self.asset_table.currentRow()
        if row < 0:
            self.output_box.append("No asset selected to remove.")
            return

        asset_name = self.asset_table.item(row, 0).text()
        asset_path = self.asset_table.item(row, 3).text()

        confirm = QMessageBox.question(self, "Confirm", f"Delete {asset_name}?", QMessageBox.Yes | QMessageBox.No)
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
                    self.output_box.append(f"Failed to delete Unreal asset.")
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

        # Creates SafeFolder inside the Unreal Content folder
        safe_folder_path = os.path.join(unreal.Paths.project_content_dir(), "SafeFolder")
        os.makedirs(safe_folder_path, exist_ok=True)

        if self.selected_project_dir != unreal.Paths.project_content_dir():
            # Moves file externally
            try:
                dest = os.path.join(safe_folder_path, os.path.basename(asset_path))
                shutil.move(asset_path, dest)
                self.output_box.append(f"Moved to SafeFolder: {dest}")
                self.asset_table.removeRow(row)
            except Exception as e:
                self.output_box.append(f"Error moving file: {e}")
        else:
            # Moves file in Unreal project
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

    menu = CPATmenu()
    menu.createMenu()
    menu.CreateMenuEntry()
    app = QApplication.instance() or QApplication(sys.argv)
    win = CPAT()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()