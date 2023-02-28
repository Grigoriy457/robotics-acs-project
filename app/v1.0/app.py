import pip
import time
import os, sys
from threading import Timer
import asyncio
import requests

try:
	import eel
except ModuleNotFoundError:
	pip.main(["install", "eel"])
	import eel

try:
	import serial
except ModuleNotFoundError:
	pip.main(["install", "pyserial"])
	import serial
from serial.tools import list_ports

try:
	from rich.console import Console
except ModuleNotFoundError:
	pip.main(["install", "rich"])
	from rich.console import Console



platform = sys.platform
if platform == "win32":
	os.system("cls")
elif platform == "linux":
	os.system("clear")



s = None
console = Console()


UPDATE_SPEED = 0.2
HOST = "http://89.223.70.199:5003/"


@eel.expose
def close_program_py():
	console.print("[red]Closing in program...")
	os.kill(os.getpid(), 9)


@eel.expose
def check_port(now_port=None):
	global s

	if now_port == "":
		now_port = None

	ports = [str(i).split(" - ") for i in list_ports.comports()]

	try:
		if len(ports) == 1:
			s = serial.Serial(port=ports[0][0], baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
		else:
			if now_port is None:
				print("error (1)")
				return "0"
			else:
				s = serial.Serial(port=now_port, baudrate=9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=0)
		time.sleep(2.5)
		print("connected to: " + s.portstr)
		return "1"
	except serial.serialutil.SerialException:
		s = None
		print("error (2)")
		return "0"


@eel.expose
def get_com_list():
	com_list = [str(i).split(" - ") for i in list_ports.comports()]
	return com_list, ("0" if s is not None else "1")


def start():
	global s

	try:
		# s.write("1".encode('utf-8'))
		print('START!')
		return "1"
	except serial.serialutil.SerialException:
		s = None
		print("error (3)")
		return "error"


def get_uid():
	global s

	try:
		if s == None:
			return "error"
		try:
			string = ""
			while True:
				text = str(s.read(), 'utf-8')
				if text == "\n":
					break
				elif text != '':
					string += text

			string = string.strip()
			if string != "":
				console.print(f"[yellow][SERIAL]:[/yellow] [green]{string}[/green]")
				if string.startswith("Card UID="):
					uid = string[len("Card UID="):]

					uid_data = requests.post(HOST + f"/api/get_user_data/{uid.replace(' ', '%20')}/").json()

					console.print(f"[bold blue]UID DATA: {uid_data}")
					if uid_data == list():
						uid_data = ["", None, "", uid]

					return uid_data

				elif string.startswith("Is card attach="):
					return string[len("Is card attach="):]
		except NameError:
			s = None
			print("error (4)")
			return "error"
		except serial.serialutil.SerialException:
			s = None
			print("error (5)")
			return "error"

	except KeyboardInterrupt:
		close_program_py()


def display_uid_py():
	global display_uid_timer

	try:
		ret = eel.display_uid(get_uid())
		if ret == "clear":
			display_uid_timer.cancel()
		else:
			display_uid_timer = Timer(UPDATE_SPEED, display_uid_py).start()
	except KeyboardInterrupt:
		close_program_py()


@eel.expose
def start_click(now_port):
	global display_uid_timer
	ret = start()

	try:
		if ret == "error":
			eel.show_hide_dialog("0")
		else:
			eel.change_display('data', 'block')
			display_uid_timer = Timer(UPDATE_SPEED, display_uid_py).start()
	except KeyboardInterrupt:
		close_program_py()


@eel.expose
def get_cabinets():
	return list(map(lambda t: t[0], requests.post(HOST + "/api/get_cabinets/").json()))


@eel.expose
def add_user(name, cabinet, user_type, uid):
	name = name.strip().replace(" ", " ")
	if name != "" and (cabinet != "" or ("Ученик" not in user_type)) and user_type != "" and uid != "":
		if cabinet == "":
			cabinet = 0
		print("Name:", name)
		print("Cabinet:", cabinet)
		print("User type:", user_type)
		print("UID:", uid)
		print()

		requests.post(HOST + "/api/add_user/", json={"name": name, "cabinet": cabinet, "user_type": user_type, "uid": uid})

		return "1"
	else:
		if uid == "":
			ret = "Приложите электронную карточку!"
		elif name == "":
			ret = "Поле ФИО должно быть заполнено!"
		elif cabinet == "" and "Ученик" in user_type:
			ret = "Выберите кабинет!"
		elif user_type == "":
			ret = "Выберите тип пользователя!"
		return ret



if __name__ == "__main__":
	try:
		eel.init("web")
		eel.start("main.html", size=(1000, 711), mode="chrome")
	except Exception:
		console.print_exception(show_locals=True)