import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDateEdit, QTimeEdit, QComboBox, QPushButton, QTabWidget, QWidget, QTableWidget, QTableWidgetItem, QListWidget, QListWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt, QDate, QTime
from PyQt6.QtGui import QFont, QColor, QCursor
from modern_widgets import ModernButton, ModernLineEdit

# =====================
# Diálogo principal
# =====================
class DailyReportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Reporte Diario")
        self.setMinimumSize(1000, 700)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        # Encabezado: Supervisores, Fecha, Hora, Turno
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Fecha"))
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        header_layout.addWidget(self.date_edit)
        header_layout.addWidget(QLabel("Hora"))
        self.time_edit = QTimeEdit(QTime.currentTime())
        header_layout.addWidget(self.time_edit)
        header_layout.addWidget(QLabel("Turno"))
        self.shift_combo = QComboBox()
        self.shift_combo.addItems(["NOCHE", "DÍA", "TARDE"])
        self.shift_combo.setEnabled(False)
        header_layout.addWidget(self.shift_combo)
        layout.addLayout(header_layout)
        # Supervisores
        sup_layout = QHBoxLayout()
        sup_layout.addWidget(QLabel("Supervisor de Campo"))
        self.sup_campo_edit = QLineEdit()
        sup_layout.addWidget(self.sup_campo_edit)
        sup_layout.addWidget(QLabel("Supervisor de Cámaras"))
        self.sup_camaras_edit = QLineEdit()
        sup_layout.addWidget(self.sup_camaras_edit)
        layout.addLayout(sup_layout)
        # Tabs
        self.tabs = QTabWidget()
        self.tab_camaras = QWidget()
        self.tab_campo = QWidget()
        self.tab_patrullando = QWidget()
        self.tab_ocurrencias = QWidget()
        self.tabs.addTab(self.tab_camaras, "🎥 Pers. Cámaras")
        self.tabs.addTab(self.tab_campo, "🚶‍♂️ Pers. Campo")
        self.tabs.addTab(self.tab_patrullando, "🛡️ Pers. Patrullando")
        self.tabs.addTab(self.tab_ocurrencias, "⚠️ Ocurrencias")
        layout.addWidget(self.tabs)
        # Tab Cámaras
        cam_layout = QVBoxLayout(self.tab_camaras)
        self.camaras_list = QListWidget()
        cam_layout.addWidget(self.camaras_list)
        self.add_camara_btn = ModernButton("Seleccionar Personal de Cámaras", "primary")
        cam_layout.addWidget(self.add_camara_btn)
        # Tab Campo
        campo_layout = QVBoxLayout(self.tab_campo)
        self.campo_table = QTableWidget(0, 10)
        self.campo_table.setHorizontalHeaderLabels([
            "Tipo", "Descripción", "Unidad", "Matrícula", "Chofer", "Sereno/Operador", "Sereno/Apoyo", "Ubicación/Base", "Radio", "Acciones"
        ])
        self.campo_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        campo_layout.addWidget(self.campo_table)
        self.add_campo_btn = ModernButton("Agregar Personal de Campo", "primary")
        campo_layout.addWidget(self.add_campo_btn)
        # Tabs vacíos
        QVBoxLayout(self.tab_patrullando)
        QVBoxLayout(self.tab_ocurrencias)
        # Botón guardar
        self.save_btn = ModernButton("Guardar Reporte Diario", "primary")
        layout.addWidget(self.save_btn)
        # Conexiones
        self.time_edit.timeChanged.connect(self._update_shift)
        self.date_edit.dateChanged.connect(self._update_shift)

    def _update_shift(self):
        hora = self.time_edit.time().toString("HH:mm")
        if "22:00" <= hora or hora < "06:00":
            self.shift_combo.setCurrentText("NOCHE")
        elif "06:00" <= hora < "14:00":
            self.shift_combo.setCurrentText("DÍA")
        else:
            self.shift_combo.setCurrentText("TARDE")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = DailyReportDialog()
    dlg.exec() 