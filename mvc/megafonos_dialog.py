import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit, QPushButton, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QGuiApplication, QPixmap
import platform
from modern_widgets import ModernButton, ModernLineEdit

class MegafonosDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔊 Buscador de Megáfonos")
        self.setMinimumSize(620, 780)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.data = self._load_data()
        self.filtered_data = self.data.copy()
        self.current_selection = -1
        self._setup_ui()

    def _load_data(self):
        raw_data = [
            ("Ignacio Merino", "236"), ("Ovalo Punta Arenas", "235"), ("Av. G", "234"), ("Av. H Colegios", "233"),
            ("Clínica Tresa", "213"), ("Niño Héroe", "237"), ("La Parada", "232"), ("Intercom la Parada", "MARCAR EL 3"),
            ("MORGUE", "221"), ("Montero", "222"), ("Palacio Municipal", "220"), ("Pipos", "219"), ("Mavila Apra", "217"),
            ("Iglesia la Inmaculada", "218"), ("Zona de Bancos", "216"), ("Curacao", "215"), ("Caja Piura", "214"),
            ("Parque 16", "227"), ("Parque 17 y 14", "223"), ("Parque 10", "224"), ("Grifo San Martin", "238"),
            ("SENATI", "239"), ("Toyota", "240"), ("Intercom. Toyota", "MARCAR EL 8"), ("Poste 08 Toyota", "***"),
            ("PTZ Poste Inmaculada", "***"), ("Intercom. Inmaculada", "MARCAR EL 2"), ("Poste 04 Mavila Centro Cívico", "***"),
            ("Intercom. Mavila", "MARCAR EL 4"), ("LRP Punta Arenas", "***"), ("Troncos", "245"), ("Salida a Lobitos", "200"),
            ("Puente Yale", "228"), ("Puente Víctor Raúl", "***"), ("PTZ Poste 10 Plazuela Pescador", "***"),
            ("Posta Cono Norte", "202"), ("Pollería Maruja", "225"), ("Politécnico", "207"), ("Plazuela Pescador", "204"),
            ("Plazuela Cáceres", "230"), ("Pecata", "226"), ("Parcela 25", "201"), ("Muelle Uno", "212"),
            ("Mercado Acapulco", "210"), ("Max Cornejo Pacora", "205"), ("Malecón San Pedro", "206"), ("Intercom Primax", "MARCAR EL 5"),
            ("Intercom Plazuela Pescador", "MARCAR EL 10"), ("Grifo Primax", "229"), ("Grifo Acapulco", "209"),
            ("Estadio Campeonísimo", "231"), ("Es Salud", "208"), ("Cocobongo", "211"), ("Camara PTZ Poste Primax", "***"),
            ("Base Cono Norte", "203"), ("FONAVI", "241"), ("Coliseo los Pinos", "243"), ("María Reina de la Paz", "242"),
            ("Ovalo Urba", "246"), ("Iglesia Señor de los Milagros", "247"), ("Calle 01 Talara Alta", "248"), ("SAPISA", "249"),
            ("Parque 28 Julio", "250"), ("Tanque Víctor Raúl", "252"), ("Posta Quiñones", "254"), ("Plazuela Quiñones", "256"),
            ("Colegio Señor de los Milagros", "257"), ("Escuela de San Sebastián", "258"), ("Paradero 20", "253"),
            ("Colegio 13", "255"), ("Cola de Gato", "263"), ("Cuadrado del Agua", "260"), ("Gruta Jorge Chávez", "259"),
            ("Pilar Nores", "261"), ("Chatarreros", "262"), ("Mario Aguirre", "264"), ("CORPAC", "244"), ("07 de Junio", "251"),
            ("PTZ Poste Ovalo de la Urba", "***"), ("Intercom Óvalo Urba", "MARCAR EL 1"), ("Poste 06 Gruta Jorge Chávez", "***"),
            ("Intercom Gruta Jorge Chávez", "MARCAR EL 6"), ("Poste 07 Aeropuerto", "***"), ("Aeropuerto", "MARCAR EL 7"),
            ("Poste 09 Víctor Raúl", "***"), ("Intercom Víctor Raúl", "MARCAR EL 9"),
            ("Sacobsa", "265"), ("Grifo Challe N.T", "266"), ("Negreiros-Luciano", "267"), ("Tanque Elevado", "268"), ("Enace II Antena", "269")
        ]
        return sorted([item for item in raw_data if len(item) == 2], key=lambda x: x[0].lower())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        # Encabezado
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(12)
        img_label = QLabel()
        pixmap = QPixmap("help/Megafonos.png")
        pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        img_label.setPixmap(pixmap)
        img_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(img_label)
        header = QLabel("<b>BUSCADOR DE MEGÁFONOS</b>")
        header.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(header)
        header_layout.addStretch(1)
        layout.addWidget(header_widget, alignment=Qt.AlignmentFlag.AlignHCenter)
        subtitle = QLabel("🔍 Búsqueda inteligente • Navegación con teclado • Copia rápida")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)
        # Búsqueda
        search_layout = QHBoxLayout()
        self.search_entry = ModernLineEdit("Buscar por nombre o código...")
        self.search_entry.returnPressed.connect(self._focus_results)
        self.search_entry.textChanged.connect(self._update_results)
        search_layout.addWidget(self.search_entry)
        self.clear_btn = ModernButton("✖ Limpiar", "secondary")
        self.clear_btn.clicked.connect(self._clear_search)
        search_layout.addWidget(self.clear_btn)
        layout.addLayout(search_layout)
        # Resultados
        self.results_list = QListWidget()
        self.results_list.setFont(QFont("Segoe UI", 11))
        self.results_list.itemSelectionChanged.connect(self._on_result_select)
        self.results_list.itemDoubleClicked.connect(self._copy_to_clipboard)
        layout.addWidget(self.results_list, 1)
        # Seleccionado
        self.selected_label = QLabel("Ninguno seleccionado")
        self.selected_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.selected_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(self.selected_label)
        # Acciones
        actions_layout = QHBoxLayout()
        self.reset_btn = ModernButton("🔄 Restablecer", "success")
        self.reset_btn.clicked.connect(self._reset_search)
        actions_layout.addWidget(self.reset_btn)
        layout.addLayout(actions_layout)
        # Barra de estado
        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        self._update_status()
        status_layout.addWidget(self.status_label)
        operador = platform.node().upper()
        user_label = QLabel(f"🪪 {operador}")
        user_label.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(user_label)
        version_label = QLabel("v1.0.0")
        version_label.setFont(QFont("Segoe UI", 9))
        version_label.setStyleSheet("color: #bdc3c7;")
        status_layout.addWidget(version_label)
        layout.addLayout(status_layout)
        self._update_results()
        self.search_entry.setFocus()

    def _update_results(self):
        search_text = self.search_entry.text().strip().lower()
        if not search_text:
            self.filtered_data = self.data
        else:
            self.filtered_data = self._smart_search(search_text)
        self.results_list.clear()
        max_name_length = max((len(nombre) for nombre, _ in self.filtered_data), default=0)
        for nombre, codigo in self.filtered_data:
            formatted = f"📍 {nombre.ljust(max_name_length)}   🔊 {codigo}"
            item = QListWidgetItem(formatted)
            self.results_list.addItem(item)
        self._update_status()
        if self.filtered_data:
            self.results_list.setCurrentRow(0)
            self._on_result_select()

    def _smart_search(self, query):
        results = []
        for condition in [
            lambda x: x[1].lower() == query,
            lambda x: x[1].lower().startswith(query),
            lambda x: x[0].lower().startswith(query),
            lambda x: query in x[1].lower(),
            lambda x: query in x[0].lower()
        ]:
            results.extend([item for item in self.data if condition(item) and item not in results])
        if ' ' in query:
            query_words = query.split()
            results.extend([item for item in self.data if all(word in item[0].lower() for word in query_words) and item not in results])
        return results

    def _on_result_select(self):
        row = self.results_list.currentRow()
        if 0 <= row < len(self.filtered_data):
            nombre, codigo = self.filtered_data[row]
            self.selected_label.setText(f"{codigo} - {nombre}")
            self.current_selection = row
        else:
            self.selected_label.setText("Ninguno seleccionado")
            self.current_selection = -1

    def _focus_results(self):
        if self.results_list.count() > 0:
            self.results_list.setFocus()
            self.results_list.setCurrentRow(0)
            self._on_result_select()

    def _copy_to_clipboard(self):
        if 0 <= self.current_selection < len(self.filtered_data):
            nombre, codigo = self.filtered_data[self.current_selection]
            QGuiApplication.clipboard().setText(codigo)
            self.selected_label.setText(f"✓ Copiado: {codigo}")

    def _clear_search(self):
        self.search_entry.setText("")
        self.search_entry.setFocus()

    def _reset_search(self):
        self.search_entry.setText("")
        self.selected_label.setText("Ninguno seleccionado")
        self.results_list.clearSelection()
        self.current_selection = -1
        self.search_entry.setFocus()
        self._update_results()

    def _update_status(self):
        total = len(self.data)
        filtered = len(self.filtered_data)
        if filtered == total:
            self.status_label.setText(f"📊 Total: {total} ubicaciones")
        else:
            self.status_label.setText(f"📊 Mostrando: {filtered} de {total} ubicaciones")

def abrir_dialogo_megafonos(parent=None):
    app = QApplication.instance() or QApplication(sys.argv)
    dlg = MegafonosDialog(parent)
    dlg.exec()

if __name__ == "__main__":
    abrir_dialogo_megafonos()