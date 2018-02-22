import os
import shutil

from PyQt5 import QtWidgets, QtCore
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from pijp_dti import qc_design, qc_func


class QCApp(QtWidgets.QMainWindow, qc_design.Ui_MainWindow):

    def __init__(self, code, image_path, overlay_path, overlay_original_path, disable_edit, parent=None):
        super(QCApp, self).__init__(parent)

        self.code = code
        self.image_path = image_path
        self.overlay_path = overlay_path
        self.overlay_original_path = overlay_original_path
        self.disable_edit = disable_edit
        self.edited = False
        self.outcome = None
        self.comments = None

        self.setupUi(self)
        center_point = QtWidgets.QDesktopWidget().availableGeometry().center()
        center_point.setX(center_point.x() - self.width()*0.5)
        center_point.setY(center_point.y() - self.height()*0.75)
        self.move(center_point)
        self.last_width = self.width()

        self.image = qc_func.load_image(self.image_path)
        self.overlay = qc_func.load_overlay(self.overlay_path)
        self.plot = MyMplCanvas(self.image, self.overlay, parent=self.centralwidget)
        self.image_frame.addWidget(self.plot)

        self.slider_opacity.valueChanged.connect(self.change_alpha)
        self.button_submit.clicked.connect(self.submit)
        self.button_skip.clicked.connect(self.skip)
        self.button_open.clicked.connect(self.open_editor)
        self.button_clear.clicked.connect(self.clear)
        self.button_hide.clicked.connect(self.hide)
        self.group_button = QtWidgets.QButtonGroup(self.centralwidget)
        self.group_button.addButton(self.button_pass)

        if self.disable_edit:
            self.button_edit.deleteLater()
        else:
            self.group_button.addButton(self.button_edit)

        self.group_button.addButton(self.button_fail)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.detect_edits)
        self.timer.start(5000)

        self.label_code.setText(self.code)


    def skip(self):
        msg = QtWidgets.QMessageBox(self.centralwidget)
        msg.setIcon(msg.NoIcon)
        msg.setWindowTitle("QC Tool")
        msg.setText("Are you sure you want to skip?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if self.edited:
            msg.setIcon(msg.Critical)
            msg.setText("Error: Edits detected!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

        else:
            result = msg.exec_()

            if result == msg.Ok:
                self.outcome = 'cancelled'
                self.comments = 'skipped'
                self.close()

    def clear(self):
        msg = QtWidgets.QMessageBox(self.centralwidget)
        msg.setIcon(msg.Warning)
        msg.setWindowTitle("QC Tool")
        msg.setText("Warning: Are you sure you want to clear edits?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if qc_func.masks_are_same(self.overlay_path, self.overlay_original_path):
            msg.setIcon(msg.Critical)
            msg.setText("Error: No edits detected!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()
        
        else:
            result = msg.exec_()
            if result == msg.Ok:
                if not os.path.isfile(self.overlay_original_path):
                    msg.setIcon(msg.Critical)
                    msg.setText("Error: Original overlay not found!")
                    msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
                    msg.exec_()
                shutil.copyfile(self.overlay_original_path, self.overlay_path)
                self.detect_edits()

    def open_editor(self):
        try:
            qc_func.open_editor(self.image_path, self.overlay_path)
            self.detect_edits()

        except FileNotFoundError:
            msg = QtWidgets.QMessageBox(self.centralwidget)
            msg.setIcon(msg.Critical)
            msg.setWindowTitle("QC Tool")
            msg.setText("Error: FSLeyes not foud!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

    def submit(self):
        msg = QtWidgets.QMessageBox(self.centralwidget)
        msg.setIcon(msg.NoIcon)
        msg.setWindowTitle("QC Tool")
        msg.setText("Are you sure you want to submit?")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)

        if self.group_button.checkedId() == -1:  # First checks if any button is selected
            msg.setIcon(msg.Critical)
            msg.setText("Error: No result selected!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

        elif (not self.disable_edit and
              self.group_button.checkedId() == self.group_button.id(self.button_edit)
              and not self.edited):
            msg.setIcon(msg.Critical)
            msg.setText("Error: No edits detected!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

        elif (not self.disable_edit and
              self.group_button.checkedId() != self.group_button.id(self.button_edit)
              and self.edited):
            msg.setIcon(msg.Critical)
            msg.setText("Error: Edits detected!")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

        else:
            result = msg.exec_()
            if result == msg.Ok:
                    self.outcome = self.group_button.button(self.group_button.checkedId()).text()
                    self.comments = self.line_comment.text()
                    self.close()

    def detect_edits(self):
        self.label_detect.setText('Detecting edits...')
        self.label_detect.setStyleSheet("color: rgb(85, 85, 255);\n""font: 81 9pt \"Open Sans\";")
        if not qc_func.masks_are_same(self.overlay_path, self.overlay_original_path):
            self.label_detect.setText('Edits detected!')
            self.label_detect.setStyleSheet("color: rgb(214, 48, 49);\n""font: 81 9pt \"Open Sans\";")
            self.button_edit.setChecked(True)
            self.edited = True

        else:
            self.label_detect.setText('No edits detected.')
            self.label_detect.setStyleSheet("color: rgb(85, 85, 255);\n""font: 81 9pt \"Open Sans\";")
            self.edited = False

        self.image = qc_func.load_image(self.image_path)
        self.overlay = qc_func.load_overlay(self.overlay_path)
        self.plot.update_figure(self.image, self.overlay)

    def change_alpha(self):
        self.plot.update_alpha(self.slider_opacity.value()/100)

    def hide(self):
        if self.button_hide.text() == "Hide":
            self.last_width = self.width()
            self.resize(self.minimumSize().width(), self.height())
            self.button_hide.setText("Show")
        else:
            self.resize(self.last_width, self.height())
            self.button_hide.setText("Hide")


class MyMplCanvas(FigureCanvas):

    def __init__(self, image, overlay, parent=None):

        self.image = image
        self.overlay = overlay
        self.masked = None
        self.projection = None
        self.hue = np.array([253, 121, 168])/255
        self.alpha = 0.5
        self.slice = self.image.shape[2]//2

        # Setting up figure
        fig = Figure()
        fig.set_facecolor('black')
        self.axes = fig.add_subplot(111)
        self.axes.set_axis_off()
        self.axes.set_frame_on(False)

        FigureCanvas.__init__(self, fig)

        # Setting up widget
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)

        FigureCanvas.updateGeometry(self)

        self.compute_initial_figure()

    def compute_initial_figure(self):
        self.masked = qc_func.mask_image(self.image, self.overlay, self.hue, self.alpha)
        self.projection = self.axes.imshow(self.masked[..., self.slice, :])

    def update_slice(self, delta):
        self.slice += np.sign(delta) * 3
        if self.slice < 0:
            self.slice = self.masked.shape[2] - 1
        if self.slice >= self.masked.shape[2]:
            self.slice = 0
        self.projection.set_data(self.masked[..., self.slice, :])
        self.draw()

    def update_alpha(self, value):
        self.alpha = value
        self.masked = qc_func.mask_image(self.image, self.overlay, self.hue, self.alpha)
        self.projection.set_data(self.masked[..., self.slice, :])
        self.draw()

    def update_figure(self, image, overlay):
        self.image = image
        self.overlay = overlay
        self.masked = qc_func.mask_image(self.image, self.overlay, self.hue, self.alpha)
        self.projection.set_data(self.masked[..., self.slice, :])
        self.draw()

    def wheelEvent(self, QWheelEvent):
        delta = QWheelEvent.angleDelta().y()
        self.update_slice(delta)


def main(code, image_path, overlay_path, overlay_original_path, disable_edit=False):
    app = QtWidgets.QApplication([])
    form = QCApp(code, image_path, overlay_path, overlay_original_path, disable_edit)
    form.show()
    app.exec()
    outcome = form.outcome
    comments = form.comments

    if outcome is None:
        outcome = 'cancelled'
        comments = ''

    app.exit()

    return outcome, comments
