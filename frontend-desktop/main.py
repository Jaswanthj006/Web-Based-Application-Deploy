"""
Chemical Equipment Parameter Visualizer - Desktop (PyQt5 + Matplotlib)
Connects to the same Django backend API.
"""
import sys
import os
import webbrowser
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTableWidget, QTableWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QScrollArea, QFrame, QTabWidget,
    QHeaderView, QComboBox, QProgressBar, QSplitter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
import requests
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib
matplotlib.use('Qt5Agg')

# Default backend URL (change if needed)
API_BASE = os.environ.get('API_BASE', 'http://127.0.0.1:8000/api')


class ApiClient:
    def __init__(self, base=API_BASE):
        self.base = base.rstrip('/')
        self.token = None

    def set_token(self, token):
        self.token = token

    def _headers(self, auth=False):
        h = {'Content-Type': 'application/json'}
        if auth and self.token:
            h['Authorization'] = f'Token {self.token}'
        return h

    def login(self, username, password):
        r = requests.post(f'{self.base}/auth/login/', json={'username': username, 'password': password})
        r.raise_for_status()
        return r.json()

    def register(self, username, password):
        r = requests.post(f'{self.base}/auth/register/', json={'username': username, 'password': password})
        r.raise_for_status()
        return r.json()

    def upload(self, path, name=None):
        with open(path, 'rb') as f:
            files = {'file': (os.path.basename(path), f, 'text/csv')}
            data = {}
            if name:
                data['name'] = name
            r = requests.post(f'{self.base}/upload/', headers=self._headers(auth=True), files=files, data=data)
        r.raise_for_status()
        return r.json()

    def history(self):
        r = requests.get(f'{self.base}/history/')
        r.raise_for_status()
        return r.json()

    def summary(self, pk):
        r = requests.get(f'{self.base}/summary/{pk}/')
        r.raise_for_status()
        return r.json()

    def data(self, pk):
        r = requests.get(f'{self.base}/data/{pk}/')
        r.raise_for_status()
        return r.json()


class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class LoginWidget(QWidget):
    def __init__(self, api, on_login):
        super().__init__()
        self.api = api
        self.on_login = on_login
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        self.username = QLineEdit()
        self.username.setPlaceholderText('Username')
        self.password = QLineEdit()
        self.password.setPlaceholderText('Password')
        self.password.setEchoMode(QLineEdit.Password)
        self.error_label = QLabel()
        self.error_label.setStyleSheet('color: #ef4444;')
        self.error_label.setVisible(False)
        login_btn = QPushButton('Log in')
        login_btn.clicked.connect(self.do_login)
        reg_btn = QPushButton('Create account')
        reg_btn.setFlat(True)
        reg_btn.clicked.connect(self.do_register)
        layout.addWidget(QLabel('Chemical Equipment Visualizer'))
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.error_label)
        layout.addWidget(login_btn)
        layout.addWidget(reg_btn)

    def do_login(self):
        self._submit('login')

    def do_register(self):
        self._submit('register')

    def _submit(self, mode):
        u, p = self.username.text().strip(), self.password.text()
        if not u or not p:
            self.error_label.setText('Username and password required')
            self.error_label.setVisible(True)
            return
        self.error_label.setVisible(False)
        try:
            if mode == 'login':
                data = self.api.login(u, p)
            else:
                data = self.api.register(u, p)
            self.on_login(data['token'], data['username'])
        except requests.RequestException as e:
            try:
                err = e.response.json().get('error', str(e))
            except Exception:
                err = str(e)
            self.error_label.setText(err)
            self.error_label.setVisible(True)


class ChartsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.bar_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.doughnut_canvas = FigureCanvas(Figure(figsize=(4, 3)))
        layout.addWidget(QLabel('Averages'))
        layout.addWidget(self.bar_canvas)
        layout.addWidget(QLabel('Equipment type distribution'))
        layout.addWidget(self.doughnut_canvas)

    def update_charts(self, summary):
        if not summary:
            return
        av = summary.get('averages', {})
        type_dist = summary.get('type_distribution', {})
        # Bar chart
        self.bar_canvas.figure.clear()
        ax = self.bar_canvas.figure.add_subplot(111)
        labels = [k for k, v in av.items() if v is not None]
        values = [av[k] for k in labels]
        if labels:
            ax.bar(labels, values, color=['#3b82f6', '#10b981', '#f59e0b'][:len(labels)])
            ax.set_ylabel('Average')
        self.bar_canvas.draw()
        # Doughnut
        self.doughnut_canvas.figure.clear()
        ax2 = self.doughnut_canvas.figure.add_subplot(111)
        if type_dist:
            ax2.pie(type_dist.values(), labels=list(type_dist.keys()), autopct='%1.0f%%',
                    colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'][:len(type_dist)],
                    startangle=90)
        self.doughnut_canvas.draw()


class MainWidget(QWidget):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self.history = []
        self.current_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.upload_btn = QPushButton('Upload CSV')
        self.upload_btn.clicked.connect(self.upload_csv)
        self.pdf_btn = QPushButton('Download PDF Report')
        self.pdf_btn.clicked.connect(self.download_pdf)
        self.pdf_btn.setEnabled(False)
        self.history_combo = QComboBox()
        self.history_combo.currentIndexChanged.connect(self.on_select_history)
        top.addWidget(self.upload_btn)
        top.addWidget(self.pdf_btn)
        top.addWidget(QLabel('Dataset:'))
        top.addWidget(self.history_combo, 1)
        layout.addLayout(top)

        self.summary_label = QLabel('Select or upload a dataset.')
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)

        self.charts = ChartsWidget()
        layout.addWidget(self.charts)

        self.table = QTableWidget()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.load_history()

    def load_history(self):
        try:
            self.history = self.api.history()
        except Exception:
            self.history = []
        self.history_combo.clear()
        self.history_combo.addItem('-- Select --', None)
        for h in self.history:
            self.history_combo.addItem(f"{h.get('name', h['id'])} ({h['total_count']} items)", h['id'])
        if self.history and not self.current_id:
            self.history_combo.setCurrentIndex(1)
            self.current_id = self.history[0]['id']
            self.refresh_data()

    def on_select_history(self, idx):
        pk = self.history_combo.itemData(idx)
        self.current_id = pk
        if pk:
            self.pdf_btn.setEnabled(True)
            self.refresh_data()
        else:
            self.pdf_btn.setEnabled(False)
            self.summary_label.setText('Select or upload a dataset.')
            self.charts.update_charts(None)
            self.table.setRowCount(0)
            self.table.setColumnCount(0)

    def refresh_data(self):
        if not self.current_id:
            return
        try:
            summary_res = self.api.summary(self.current_id)
            data_res = self.api.data(self.current_id)
        except Exception as e:
            QMessageBox.warning(self, 'Error', str(e))
            return
        summary = summary_res.get('summary') or summary_res
        total = summary_res.get('total_count', 0)
        av = summary.get('averages', {})
        parts = [f"Total: {total}"]
        for k, v in (av or {}).items():
            if v is not None:
                parts.append(f"Avg {k}: {v}")
        self.summary_label.setText(' | '.join(parts))
        self.charts.update_charts(summary)
        data = data_res.get('data', [])
        if not data:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return
        cols = list(data[0].keys())
        self.table.setColumnCount(len(cols))
        self.table.setRowCount(len(data))
        self.table.setHorizontalHeaderLabels(cols)
        for i, row in enumerate(data):
            for j, c in enumerate(cols):
                self.table.setItem(i, j, QTableWidgetItem(str(row.get(c, ''))))

    def upload_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select CSV', '', 'CSV (*.csv)')
        if not path:
            return
        self.upload_btn.setEnabled(False)
        worker = Worker(self.api.upload, path, os.path.basename(path))
        worker.finished.connect(self._upload_done)
        worker.error.connect(self._upload_error)
        worker.start()
        self._worker = worker

    def _upload_done(self, result):
        self.upload_btn.setEnabled(True)
        self.load_history()
        self.current_id = result['id']
        idx = self.history_combo.findData(result['id'])
        if idx >= 0:
            self.history_combo.setCurrentIndex(idx)
        self.refresh_data()
        QMessageBox.information(self, 'Upload', 'File uploaded successfully.')

    def _upload_error(self, err):
        self.upload_btn.setEnabled(True)
        QMessageBox.warning(self, 'Upload failed', err)

    def download_pdf(self):
        if not self.current_id or not self.api.token:
            return
        url = f'{API_BASE}/report/{self.current_id}/pdf/?token={self.api.token}'
        webbrowser.open(url)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api = ApiClient()
        self.setWindowTitle('Chemical Equipment Parameter Visualizer')
        self.setMinimumSize(900, 700)
        self.resize(1000, 750)
        self.show_login()

    def show_login(self):
        self.setCentralWidget(LoginWidget(self.api, self.on_login))

    def on_login(self, token, username):
        self.api.set_token(token)
        self.setCentralWidget(MainWidget(self.api))
        self.statusBar().showMessage(f'Logged in as {username}')


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
