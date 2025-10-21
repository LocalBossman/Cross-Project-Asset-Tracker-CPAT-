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

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CPAT")
        self.setFixedSize(800, 550)

        self.selected_project_dir = unreal.Paths.project_content_dir()
        self.UI()

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
        self.output_box.setFixedHeight(100)

        #Bottom buttons
        action_layout = QHBoxLayout()
        action_layout.addWidget(self.remove_button)
        action_layout.addWidget(self.move_button)

        #Combines everything into avertical layout
        layout = QVBoxLayout()
        layout.addWidget(title)
        layout.addLayout(button_layout)
        layout.addLayout(summary_layout)
        layout.addWidget(self.asset_table)
        layout.addLayout(action_layout)
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

    app = QApplication.instance() or QApplication(sys.argv)
    win = CPAT()
    win.show()
    app.exec()

if __name__ == "__main__":
    main()