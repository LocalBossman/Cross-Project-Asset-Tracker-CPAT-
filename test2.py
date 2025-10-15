#/---Cross-Project-Asset-Tracker-CPAT---/



#TODO 
#Add UI
#Apply functions to UI e.g. scan button runs the scan function 
#Add detection for duplicate, oversized or unused files
#Add Report UI
#Add manual clean up



import unreal
import os
import sys
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QMainWindow, QTextEdit
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPalette, QColor


class CPAT(QMainWindow):

#/------------------------------------- Backend-Logic ------------------------------------------/#
    def scan(self, content_dir):
        """Scans the Unreal Content folder for .uasset files"""
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

#/------------------------------------- UI ------------------------------------------/#
    def __init__(self, parent=None):
        super(CPAT, self).__init__(parent)
        self.setWindowTitle("CPAT")
        self.setFixedSize(QSize(900, 500))

        # Unreal Content Directory
        self.project_content_dir = unreal.Paths.project_content_dir()

        # Build UI
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Title Label
        title = QLabel("Cross Project Asset Tracker")
        layout.addWidget(title)

        # Scan Button
        scan_button = QPushButton("Scan Assets")
        scan_button.clicked.connect(self.on_scan_clicked)
        scan_button.setFixedSize(QSize(100, 50))
        scan_button.autoFillBackground()
        scan_button_colour = scan_button.palette()
        scan_button_colour.setColor(QPalette.window, QColor("red"))
        scan_button.setPalette(scan_button_colour)
        layout.addWidget(scan_button)

        # Report Box
        self.output_box = QTextEdit()
        self.output_box.setReadOnly(True)
        self.output_box.setFixedSize(QSize(400, 300))
        layout.addWidget(self.output_box)

#/------------------------------------- Buttons ------------------------------------------/#
    def on_scan_clicked(self):
        assets = self.scan(self.project_content_dir)
        summary = f"Found {len(assets)} assets\n\n"
        for a in assets[:10]:
            summary += f"{a['name']} - {a['size_mb']} MB\n"
        self.output_box.setText(summary)

    def select_projects_button():
        pass
        
    def remove_button():
        pass
        
    def ignore_files_button():
        pass
        
    def move_to_folder_button():
        pass



#/------------------------------------- Run Code ------------------------------------------/#
def main():
    # Unreal sometimes already has a QApplication instance
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    window = CPAT()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()