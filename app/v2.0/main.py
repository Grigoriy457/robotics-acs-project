import io
import sys

from PIL import Image
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import serial
from serial.tools import list_ports

import requests
import urllib
import json
import os

from templates.template import Ui_MainWindow
from templates.dialog_template import Ui_Dialog


HOST = "robotics-acs-project.tk:5002"


def change_text_info(window: Ui_MainWindow, state):
	if state == 0:
		window.setEnabled(False)
		window.label_9.setText("Controller not connected")
		window.label_9.setStyleSheet("color: red;")
	elif state == 1:
		window.setEnabled(False)
		window.label_9.setText("Connecting...")
		window.label_9.setStyleSheet("color: #FFA216;")
	elif state == 2:
		window.setEnabled(True)
		window.pushButton.setEnabled(False)
		window.label_9.setText("Card isn’t detected!")
		window.label_9.setStyleSheet("color: #FF7A00;")
	elif state == 3:
		window.setEnabled(True)
		window.label_9.setText("Card detected!")
		window.label_9.setStyleSheet("color: #00FF29;")


def resource_path(relative_path):
	base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
	return os.path.join(base_path, relative_path)


class ConnectToSerial(QThread):
	cant_connect = pyqtSignal(bool)

	def __init__(self, parent, com_port):
		super().__init__(parent)
		self.parent = parent
		self.com_port = com_port
		self.parent.parent.serial = None
		self.cant_connect.connect(self.cant_connect_f)

	def cant_connect_f(self, value):
		if value:
			change_text_info(self.parent.parent, 0)
			self.parent.parent.can_connect = False
			self.parent.user_close = False
			self.parent.close()
			QMessageBox.critical(self.parent.parent, 'Access denied', 'Another application is connected to the controller!')
			dlg = CustomDialog(self.parent.parent)
			dlg.exec()
			self.parent.parent.get_uid = GetUid(self.parent.parent)
			self.parent.parent.get_uid.start()

	def run(self):
		try:
			change_text_info(self.parent.parent, 1)
			s = serial.Serial(port=self.com_port, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
							  bytesize=serial.EIGHTBITS, timeout=0)
			self.parent.parent.serial = s
			self.parent.user_close = False
			self.parent.close()
		except serial.serialutil.SerialException as excep:
			print("Serial Error:", excep)
			self.cant_connect.emit(True)


class CustomDialog(QDialog, Ui_Dialog):
	def __init__(self, parent: QMainWindow):
		self.parent = parent
		super().__init__(parent)
		self.setupUi(self)
		self.pushButton.clicked.connect(self.update)
		self.pushButton_2.clicked.connect(self.connect)
		self.update()
		self.setModal(True)
		self.show()
		self.user_close = True

	def update(self):
		self.comboBox.clear()
		ports = list(map(lambda t: str(t).split(" - "), list_ports.comports()))
		if len(ports) == 0:
			self.comboBox.addItem("-", None)
		for i in ports:
			port_name = i[1].replace(f' ({i[0]})', '').strip()
			self.comboBox.addItem(f"{i[0]} {f'({port_name})' if port_name != '' else ''}", i[0])

	def connect(self):
		com_port = self.comboBox.currentData()
		s = ConnectToSerial(self, com_port)
		s.start()

	def closeEvent(self, event):
		event.accept()
		if self.user_close:
			self.parent.close()
			sys.exit()


class GetUid(QThread):
	update_user_data = pyqtSignal(dict)
	controller_disconnected = pyqtSignal(bool)

	def __init__(self, parent: Ui_MainWindow):
		super().__init__(parent)
		self.parent = parent
		self.is_finished = False
		self.update_user_data.connect(self.update)
		self.controller_disconnected.connect(self.disconnected)

	def update(self, value):
		self.parent.treeView.selectionModel().clear()
		uid = value["uid"]
		uid_data = value["uid_data"]
		if len(uid_data) > 0:
			self.parent.lineEdit.setText(f"{uid_data[3]} {uid_data[4]} {uid_data[5]}")
			self.parent.lineEdit_2.setText(uid_data[13])
			self.parent.lineEdit_3.setText(uid_data[6])
			self.parent.lineEdit_4.setText(uid_data[7])
		else:
			self.parent.lineEdit.setText("")
			self.parent.lineEdit_2.setText("")
			self.parent.lineEdit_3.setText("")
			self.parent.lineEdit_4.setText("")
		self.parent.lineEdit_5.setText(uid)

	def disconnected(self, value):
		if value:
			change_text_info(self.parent, 0)
			QMessageBox.critical(self.parent, 'Error', 'Controller has been disabled!')
			dlg = CustomDialog(self.parent)
			dlg.exec()
			self.parent.get_uid = GetUid(self.parent)
			self.parent.get_uid.start()

	def run(self):
		s = self.parent.serial
		try:
			while True:
				string = ""
				while True:
					if self.is_finished:
						s.close()
						return
					if s.in_waiting != 0:
						symbol = s.readline()
						try:
							symbol = symbol.decode()
							string += symbol
							if symbol.endswith("\n"):
								break
						except UnicodeDecodeError:
							print("[ERROR]:", symbol)
				string = string.strip()
				if string != "":
					print("[SERIAL]:", string)
					if string.startswith("Card UID="):
						change_text_info(self.parent, 3)

						uid = string[len("Card UID="):]
						self.parent.now_uid = uid
						uid_data = requests.post(f"http://{HOST}/api/get_user_data/{urllib.parse.quote(uid)}/").json()

						user_avatar = requests.post(f"http://{HOST}/api/get_user_avatar/{urllib.parse.quote(uid)}/").content
						img = Image.open(io.BytesIO(user_avatar))
						img = img.resize((127, 127))
						img_byte_arr = io.BytesIO()
						img.save(img_byte_arr, format='PNG')

						pixmap = self.parent.label_3.pixmap()
						pixmap.loadFromData(img_byte_arr.getvalue())
						self.parent.label_3.setPixmap(pixmap)

						print(f"[bold blue]UID DATA: {uid_data}")
						self.update_user_data.emit({"uid": uid, "uid_data": uid_data})

					elif string.startswith("Is card attach="):
						value = int(string[len("Is card attach="):])
						if value == 0:
							self.parent.now_uid = None
							change_text_info(self.parent, 2)
							self.update_user_data.emit({"uid": "", "uid_data": list()})
							self.parent.label_3.setPixmap(QPixmap(resource_path("images/user-avatar.png")))

					elif string == "Waiting for card...":
						change_text_info(self.parent, 2)

		except serial.serialutil.SerialException as excep:
			print("Serial Error:", excep)
			change_text_info(self.parent, 0)
			self.controller_disconnected.emit(True)


class StandardItem(QStandardItem):
	def __init__(self, txt="", font_size=12, set_bold=False, color=QColor(0, 0, 0), data=None):
		super().__init__()

		fnt = QFont("Segoe UI", font_size)
		fnt.setBold(set_bold)

		self.setEditable(False)
		self.setForeground(color)
		self.setFont(fnt)
		self.setText(txt)
		self.setData(data, 5)


class LoadUsersData(QThread):
	users_data = pyqtSignal(dict)
	connection_error = pyqtSignal(str)

	def __init__(self, parent):
		super().__init__(parent=parent)
		self.parent = parent
		self.users_data.connect(self.load_data)
		self.connection_error.connect(self.connection_error_f)

	def connection_error_f(self, value):
		QMessageBox.critical(self.parent, "Fail", value)
		self.parent.close()

	def load_data(self, value):
		self.parent.treeView.setHeaderHidden(True)
		treeModel = QStandardItemModel()
		rootNode = treeModel.invisibleRootItem()

		user_type_names = ["Admins", "Teachers", "Students"]
		for user_type, j in value.items():
			user_type_item = StandardItem(user_type_names[int(user_type)], 14, set_bold=True, color=QColor(100, 100, 100))
			if isinstance(j, list):
				user_data = j
				for i in user_data:
					user_type_item.appendRow(StandardItem(f"{i[1]} {i[2]} {i[3]}", 12, color=QColor(0, 0, 0), data=i))
			else:
				classes = j
				for class_number, class_data in classes.items():
					class_number_item = StandardItem(class_number, 14, set_bold=True, color=QColor(100, 100, 100))
					for class_letter, user_data in class_data.items():
						class_letter_item = StandardItem(f"{class_letter} class", 14, set_bold=True, color=QColor(100, 100, 100))
						for i in user_data:
							class_letter_item.appendRow(StandardItem(f"{i[1]} {i[2]} {i[3]}", 12, color=QColor(0, 0, 0), data=i))
						class_number_item.appendRow(class_letter_item)
					user_type_item.appendRow(class_number_item)
			rootNode.appendRow(user_type_item)

		self.parent.treeView.setModel(treeModel)
		self.parent.treeView.expandAll()
		self.parent.treeView.selectionModel().selectionChanged.connect(self.parent.show_user_data)

	def run(self):
		try:
			response = requests.post(f"http://{HOST}/api/get_all_users/")
			if response.status_code == 200:
				data = json.loads(response.json())
				self.users_data.emit(data)
			else:
				self.connection_error.emit(f"Server error (status code: {response.status_code})!")
		except requests.exceptions.ConnectionError:
			self.connection_error.emit("Failed connect to server!")


class MainWindow(QMainWindow, Ui_MainWindow):
	def __init__(self):
		super().__init__()
		self.setupUi(self)
		self.show()
		change_text_info(self, 0)
		self.now_user_id = None
		self.now_uid = None
		self.pushButton.clicked.connect(self.upload_user_data)

		self.load_user_data = LoadUsersData(self)
		self.load_user_data.start()

		dlg = CustomDialog(self)
		dlg.exec()

		self.get_uid = GetUid(self)
		self.get_uid.start()

	# def get_rows(self, item: QModelIndex, parent=QModelIndex()):
	# 	rows = list()
	# 	for i in range(item.model().rowCount()):
	# 		row_model = item.model().index(i, 0, parent).model()
	# 		if row_model is not None:
	# 			if item.model().index(i, 0, parent).data(5) is None:
	# 				for row in self.get_rows(item.model().index(i, 0, parent), item.model().index(i, 0, parent)):
	# 					rows.append(row)
	# 			else:
	# 				rows.append(item.model().index(i, 0, parent))
	# 	return rows

	def upload_user_data(self):
		data = self.treeView.currentIndex().data(5)
		if data is not None:
			self.now_user_id = data[0]
		if (self.now_user_id is not None) and (self.now_uid is not None):
			button = QMessageBox.question(self, "Question", f"Are you sure you want to write down a card for {data[1]} {data[2]} {data[3]}?", QMessageBox.Yes | QMessageBox.No)
			if button == QMessageBox.Yes:
				try:
					response = requests.post(f"http://{HOST}/api/upload_user_data/{self.now_user_id}/{self.now_uid}/")
					if response.status_code == 200:
						self.load_user_data = LoadUsersData(self)
						self.load_user_data.start()

						json_data = json.loads(response.json())["user_data"]
						print(json_data)
						self.lineEdit_5.setText(json_data[6])
						QMessageBox.information(self, "Info", "User uid successfully updated!")
					else:
						QMessageBox.critical(self, "Fail", f"Server error (status code: {response.status_code})!")
				except requests.exceptions.ConnectionError:
					QMessageBox.critical(self, "Fail", "Failed connect to server!")

	def show_user_data(self):
		data = self.treeView.currentIndex().data(5)
		if data is None:
			self.pushButton.setEnabled(False)
			self.lineEdit.setText("")
			self.lineEdit_2.setText("")
			self.lineEdit_3.setText("")
			self.lineEdit_4.setText("")
			self.lineEdit_5.setText("")
		else:
			if self.now_uid is not None:
				self.pushButton.setEnabled(True)
			self.lineEdit.setText(f"{data[1]} {data[2]} {data[3]}")
			self.lineEdit_2.setText(f"{data[7]}{data[8]}" if (data[7] is not None) and (data[8] is not None) else None)
			self.lineEdit_3.setText(data[4])
			self.lineEdit_4.setText(data[5])
			self.lineEdit_5.setText(data[6])
		self.label_3.setPixmap(QPixmap(resource_path("images/user-avatar.png")))


	def closeEvent(self, event):
		try:
			self.get_uid.is_finished = True
			while not self.get_uid.isFinished():
				pass
		except AttributeError:
			pass
		event.accept()
		sys.exit()


def except_hook(cls, exception, traceback):
	sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = MainWindow()
	sys.excepthook = except_hook
	sys.exit(app.exec_())
