from qtpy.QtWidgets import QMainWindow, QTextEdit, QDockWidget, QVBoxLayout, \
    QPushButton, QWidget, QScrollArea, QToolBar, QPushButton, QAction, \
    QFileDialog, QListWidget, QListWidgetItem
from qtpy.QtCore import Qt, QFile
from qtpy.QtGui import QIcon, QImageReader, QPixmap, QKeySequence

import os
import sys
import glob
from widgets.canvas import Canvas

class MainWindow(QMainWindow):
    FIT_WINDOW, FIT_WIDTH, MANUAL_ZOOM = 0, 1, 2

    def __init__(self, label_file=None):
        super(MainWindow, self).__init__()
        self.showMaximized()
        self.setWindowTitle("VTCC.Labelling")

        self.file_dirs = []
        self.file_id = -1
        self.labels = []
        with open(label_file, 'r') as f:
            lines = f.read().splitlines()
            for label in lines:
                self.labels.append(label)

        # RIGHT DOCK
        self.label_dock = QDockWidget("Label List", self)
        self.label_list_widget = QListWidget(self)
        self.load_labels(label_file)
        self.label_dock.setWidget(self.label_list_widget)

        self.object_dock = QDockWidget("Object List", self)
        self.object_list_widget = QListWidget(self)
        self.object_list_widget.currentRowChanged.connect(self.change_object)
        self.object_dock.setWidget(self.object_list_widget)

        self.file_dock = QDockWidget("File List", self)
        self.file_list_widget = QListWidget(self)
        self.file_list_widget.currentRowChanged.connect(self.change_file)
        self.file_dock.setWidget(self.file_list_widget)

        self.addDockWidget(Qt.RightDockWidgetArea, self.label_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.object_dock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.file_dock)

        # MAIN CANVAS
        self.canvas = Canvas(self)

        self.canvas_area = QScrollArea()
        self.canvas_area.setWidget(self.canvas)
        self.canvas_area.setWidgetResizable(True)
        self.scrollBars = {
            Qt.Vertical: self.canvas_area.verticalScrollBar(),
            Qt.Horizontal: self.canvas_area.horizontalScrollBar(),
        }
        self.setCentralWidget(self.canvas_area)

        # LEFT DOCK
        self.open_action = QAction(QIcon('icons/open.png'), 'Open File', self)
        self.open_action.triggered.connect(self.open_file)
        self.open_action.setShortcut(QKeySequence("Ctrl+O"))
        self.open_dir_action = QAction(QIcon('icons/open.png'), 'Open Dir', self)
        self.open_dir_action.triggered.connect(self.open_dir)

        self.next_img_action = QAction(QIcon('icons/next.png'), 'Next Image', self)
        self.next_img_action.triggered.connect(self.next_img)
        self.next_img_action.setShortcut(QKeySequence("Right"))
        self.prev_img_action = QAction(QIcon('icons/prev.png'), 'Prev Image', self)
        self.prev_img_action.triggered.connect(self.prev_img)
        self.prev_img_action.setShortcut(QKeySequence("Left"))

        self.zoom_in_action = QAction(QIcon('icons/zoom-in.png'), 'Zoom In', self)
        self.zoom_in_action.triggered.connect(self.zoom_in)
        self.zoom_out_action = QAction(QIcon('icons/zoom-out.png'), 'Zoom Out', self)
        self.zoom_out_action.triggered.connect(self.zoom_out)
        self.zoom_org_action = QAction(QIcon('icons/fit-window.png'), 'Fit Window', self)
        self.zoom_org_action.triggered.connect(self.zoom_org)

        self.rectangle_action = QAction(QIcon('icons/objects.png'), 'New Rectangle', self)
        self.rectangle_action.triggered.connect(self.new_rectangle)
        self.auto_polygon_action = QAction(QIcon('icons/objects.png'), 'New Auto-Polygon', self)
        self.auto_polygon_action.triggered.connect(self.new_auto_polygon)
        self.polygon_action = QAction(QIcon('icons/objects.png'), 'New Polygon', self)
        self.polygon_action.triggered.connect(self.new_polygon)

        self.next_obj_action = QAction(QIcon('icons/next.png'), 'Next Object', self)
        self.next_obj_action.triggered.connect(self.canvas.next_obj)
        self.next_obj_action.setShortcut(QKeySequence("Down"))
        self.prev_obj_action = QAction(QIcon('icons/prev.png'), 'Prev Object', self)
        self.prev_obj_action.triggered.connect(self.canvas.prev_obj)
        self.prev_obj_action.setShortcut(QKeySequence("Up"))
        self.del_obj_action = QAction(QIcon('icons/delete.png'), 'Delete Object', self)
        self.del_obj_action.triggered.connect(self.canvas.del_obj)
        self.del_obj_action.setShortcut(QKeySequence("Del"))

        self.toolbar = QToolBar(self)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.toolbar.addAction(self.open_action)
        self.toolbar.addAction(self.open_dir_action)
        self.toolbar.addAction(self.next_img_action)
        self.toolbar.addAction(self.prev_img_action)
        # self.toolbar.addAction(self.zoom_in_action)
        # self.toolbar.addAction(self.zoom_out_action)
        # self.toolbar.addAction(self.zoom_org_action)
        self.toolbar.addAction(self.rectangle_action)
        self.toolbar.addAction(self.auto_polygon_action)
        self.toolbar.addAction(self.polygon_action)
        self.toolbar.addAction(self.next_obj_action)
        self.toolbar.addAction(self.prev_obj_action)
        self.toolbar.addAction(self.del_obj_action)

        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

        self.scalers = {
            self.FIT_WINDOW: self.scaleFitWindow,
            self.FIT_WIDTH: self.scaleFitWidth,
            # Set to one to scale to 100% when loading files.
            self.MANUAL_ZOOM: lambda: 1,
        }

    def update_mode(self, mode_id):
        pass

    def change_object(self, row):
        if (row >= 0):
            self.canvas.cur_object = row
            self.canvas.repaint()

    def change_file(self, row):
        if (row >= 0):
            self.file_id = row
            self.canvas.load_file(self.file_dirs[self.file_id])
            self.adjustScale(initial=True)

    def open_file(self):
        path = '.'
        if len(self.file_dirs) > 0:
            path = os.path.dirname(str(self.file_dirs[0]))    

        formats =   ['*.{}'.format(fmt.data().decode())
                    for fmt in QImageReader.supportedImageFormats()]
        filters = "Image files (%s)" % ' '.join(formats)
        file_dir = QFileDialog.getOpenFileName(self, \
                    "Choose Image file", path, filters)[0]

        self.file_dirs = [file_dir]
        self.import_files()

    def open_dir(self):
        targetDirPath = str(QFileDialog.getExistingDirectory(
            self, 'Open Directory', '.',
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks))

        self.file_dirs = []
        for fmt in QImageReader.supportedImageFormats():
            pattern = os.path.join(targetDirPath, "*." + fmt.data().decode())
            self.file_dirs += glob.glob(pattern)
        self.import_files()

    def next_img(self):
        if (len(self.file_dirs) > 0):
            self.file_id = (self.file_id + 1) % len(self.file_dirs)
            self.canvas.load_file(self.file_dirs[self.file_id])
            self.adjustScale(initial=True)
            self.file_list_widget.setCurrentRow(self.file_id)

    def prev_img(self):
        if (len(self.file_dirs) > 0):
            self.file_id = (self.file_id + len(self.file_dirs) - 1) % len(self.file_dirs)
            self.canvas.load_file(self.file_dirs[self.file_id])
            self.adjustScale(initial=True)
            self.file_list_widget.setCurrentRow(self.file_id)

    def import_files(self):
        self.load_file_list()

        self.file_id = 0
        self.canvas.load_file(self.file_dirs[0])
        self.adjustScale(initial=True)
        self.file_list_widget.setCurrentRow(self.file_id)

    def load_labels(self, label_file):
        self.label_list_widget.clear()
        for label in self.labels:
            item = QListWidgetItem(label)
            self.label_list_widget.addItem(item)

    def load_object_list(self, objects):
        self.object_list_widget.clear()
        for obj in objects:
            item = QListWidgetItem(obj.label)
            self.object_list_widget.addItem(item)

    def load_file_list(self):
        self.file_list_widget.clear()

        for image_dir in self.file_dirs:
            if not QFile.exists(image_dir):
                continue
            item = QListWidgetItem(image_dir)
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            label_dir = os.path.splitext(image_dir)[0] + '.json'
            if QFile.exists(label_dir):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)
            self.file_list_widget.addItem(item)

    def scaleFitWindow(self):
        """Figure out the size of the pixmap to fit the main widget."""
        e = 2.0  # So that no scrollbars are generated.
        w1 = self.centralWidget().width() - e
        h1 = self.centralWidget().height() - e
        a1 = w1 / h1
        # Calculate a new scale value based on the pixmap's aspect ratio.
        w2 = self.canvas.pixmap.width() - 0.0
        h2 = self.canvas.pixmap.height() - 0.0
        a2 = w2 / h2
        return w1 / w2 if a2 >= a1 else h1 / h2

    def scaleFitWidth(self):
        # The epsilon does not seem to work too well here.
        w = self.centralWidget().width() - 2.0
        return w / self.canvas.pixmap.width()

    def adjustScale(self, initial=False):
        value = self.scalers[self.FIT_WINDOW if initial else self.zoomMode]()
        self.canvas.rescale(value)

    def zoom_in(self):
        value = self.canvas.scale
        self.canvas.rescale(value * 1.1)

    def zoom_out(self):
        value = self.canvas.scale
        self.canvas.rescale(value * 0.9)

    def zoom_org(self):
        print(self.centralWidget().width(), self.centralWidget().height())
        print(self.canvas.pixmap.width(), self.canvas.pixmap.height())
        print(self.canvas.width(), self.canvas.height())
        print(self.canvas_area.width(), self.canvas_area.height())
        self.adjustScale(initial=True)
    
    def new_rectangle(self):
        self.canvas.points = []
        self.canvas.mode = self.canvas.RECTANGLE

    def new_auto_polygon(self):
        self.canvas.points = []
        self.canvas.mode = self.canvas.AUTO_POLYGON

    def new_polygon(self):
        self.canvas.points = []
        self.canvas.mode = self.canvas.POLYGON