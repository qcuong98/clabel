from app import MainWindow

import sys
from qtpy.QtWidgets import QApplication

if __name__ == '__main__':
    app = QApplication([])

    win = MainWindow(label_file=sys.argv[1])
    win.show()

    sys.exit(app.exec_())