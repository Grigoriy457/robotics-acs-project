import zoneinfo

from flask import *
import werkzeug
from ua_parser import user_agent_parser
from werkzeug.user_agent import UserAgent
from werkzeug.utils import cached_property

import random
from rich.console import Console
import json
import requests
import os
from PIL import Image
import threading
from urllib.parse import unquote

import pytz
import datetime
import time
from dateutil.relativedelta import relativedelta
import holidays
import calendar

import pyotp
import qrcode

import secrets
import string

import re

import sqlite3

import config
from db import Database
import email_sender



app = Flask(__name__)
app.config["SECRET_KEY"] = "ThisIsASecretKey"
app.config["REMEMBER_COOKIE_DURATION"] = datetime.timedelta(days=20)


# pprint = Console().print


def _enumerate(_list):
	return enumerate(_list)


def generate_password():
	alphabet = string.ascii_letters + string.digits
	return ''.join(secrets.choice(alphabet) for _ in range(8))


def check_day_on_holiday(date, lesson_id):
	db = Database(config.DB_NAME)
	try:
		return ((date not in holidays.country_holidays('RU')) or (not config.USE_HOLIDAYS)) and (date.weekday() in db.get_lesson_days_from_schedule_by_lesson_id(lesson_id))
	finally:
		db.close_connection()


def day_is_holiday(date):
	return (date in holidays.country_holidays('RU')) and config.USE_HOLIDAYS


def datetime_strftime(unix_time):
	hours = str(unix_time // 60 // 60)
	minutes = str(unix_time // 60 % 60)
	if len(hours) == 1:
		hours = "0" + hours
	if len(minutes) == 1:
		minutes = "0" + minutes
	return f"{hours}:{minutes}"


def from_utc(utc_time, tz):
	return utc_time.replace(tzinfo=pytz.timezone('UTC')).astimezone(pytz.timezone(tz))


def now_utc(f=None):
	if f is None:
		return datetime.datetime.utcnow()
	return datetime.datetime.strptime(datetime.datetime.utcnow().strftime(f), f)


def get_entrys_exits_count_by_date(data):
	labels = list()
	entrys = list()
	exits = list()

	now_date = ""
	entrys_counter = 0
	exits_counter = 0
	for i in data:
		formated_date = datetime.datetime.strptime(i[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%d.%m.%Y")

		if now_date == "":
			now_date = formated_date
			if i[1] == "entry":
				entrys_counter += 1
			elif i[1] == "exit":
				exits_counter += 1
			else:
				print(i)
		elif now_date == formated_date:
			if i[1] == "entry":
				entrys_counter += 1
			elif i[1] == "exit":
				exits_counter += 1
			else:
				print(i)
		else:
			labels.append(now_date)

			entrys.append(entrys_counter)
			exits.append(exits_counter)
			if i[1] == "entry":
				entrys_counter = 1
				exits_counter = 0
			elif i[1] == "exit":
				exits_counter = 1
				entrys_counter = 0
			else:
				print(i)
			now_date = formated_date

	labels.append(now_date)

	entrys.append(entrys_counter)
	exits.append(exits_counter)

	return labels, entrys, exits


def get_website_views_count_by_date(data):
	db = Database(config.DB_NAME)
	try:
		labels = list()
		website_views = list()

		for i in data:
			labels.append(i[1])

			website_views_count = db.get_website_views_count(i[1])
			if website_views_count != None:
				website_views.append(website_views_count)
			else:
				website_views.append(0)

		return (labels, website_views)

	finally:
		db.close_connection()


def format_number(number):
	str_number = str(number)
	new_number = ""
	for i, j in enumerate(str_number[::-1]):
		new_number += j
		if (i + 1) % 3 == 0:
			new_number += " "
	return new_number[::-1]


def format_persent(persent):
	if int(persent) == persent:
		return int(persent)
	return persent


def get_persent(today_count, yesterday_count):
	if today_count == None:
		today_count = 0
	if yesterday_count == None:
		yesterday_count = 0

	if yesterday_count == 0:
		if today_count != 0:
			return format_persent(round((today_count / (1 / 100)), config.ROUND_PERCENT))
		else:
			return 0
	elif today_count == 0:
		return -100
	return format_persent(round((today_count / (yesterday_count / 100)) - 100, config.ROUND_PERCENT))


def add_one_to_views(func):
	def inner(*args, **kwargs):
		# db.add_one_view_to_website_views()
		return func(*args, **kwargs)
	inner.__name__ = func.__name__
	return inner


class ParsedUserAgent(UserAgent):
	@cached_property
	def _details(self):
		return user_agent_parser.Parse(self.string)

	@property
	def platform(self):
		return self._details['os']['family']

	@property
	def browser(self):
		return self._details['user_agent']['family']

	@property
	def version(self):
		return '.'.join(
			part
			for key in ('major', 'minor', 'patch')
			if (part := self._details['user_agent'][key]) is not None
		)


@app.route('/login/', methods=["GET", "POST"])
@add_one_to_views
def login():
	db = Database(config.DB_NAME)
	try:
		if session.get('logged_in', False):
			return redirect("/")

		if request.method == "GET":
			return render_template("sign-in.html", need_confirmation_code=0, is_error=int(request.args.get("is_wrong_data", "0")))
		else:
			login = request.form.get("login")
			password = request.form.get("password")
			confirmation_code = request.form.get("confirmation-code")
			rememberMe = request.form.get("rememberMe", "on")
			session_token = request.cookies.get("session")

			if db.is_correct_login(login, password):
				if db.get_is_2fa_enabled_by_login(login):
					if confirmation_code is not None:
						if pyotp.TOTP(db.get_user_secret_by_login(login)).verify(int(confirmation_code)):
							session['logged_in'] = True
							session['login'] = login
							session['session'] = session_token

							user_email = db.get_user_email_by_user_id(db.get_user_id_by_login(login))
							entry_time = datetime.datetime.now(zoneinfo.ZoneInfo(session.get("timezone", "Europe/Moscow")))

							users_browser_data = ParsedUserAgent(request.user_agent.string)
							device = users_browser_data.platform.lower()
							browser = users_browser_data.browser.lower()
							version = users_browser_data.version.lower()
							ip_address = request.remote_addr

							email_sender.new_login(user_email, entry_time, device, browser, version, ip_address)

							return redirect("/")
						return render_template("sign-in.html", need_confirmation_code=1, login=login, password=password, confirmation_code=confirmation_code, is_error=1)
					return render_template("sign-in.html", need_confirmation_code=1, login=login, password=password)

				session['logged_in'] = True
				session['login'] = login
				session['session'] = session_token

				user_email = db.get_user_email_by_user_id(db.get_user_id_by_login(login))
				entry_time = datetime.datetime.now(zoneinfo.ZoneInfo(session.get("timezone", "Europe/Moscow")))

				users_browser_data = ParsedUserAgent(request.user_agent.string)
				device = users_browser_data.platform.lower()
				browser = users_browser_data.browser.lower()
				version = users_browser_data.version.lower()
				ip_address = request.remote_addr

				email_sender.new_login(user_email, entry_time, device, browser, version, ip_address)

				return redirect("/")
			else:
				return redirect("/login?is_wrong_data=1")
	finally:
		db.close_connection()


@app.route('/reset-password/', methods=["GET", "POST"])
def reset_password():
	db = Database(config.DB_NAME)
	try:
		if session.get('logged_in', False):
			return redirect("/")

		if request.method == "POST":
			email = request.form.get("email", "").strip()
			_2fa_recovery_code = request.form.get("2fa_recovery_code", "").strip()
			verif_code = request.form.get("verif_code", "").strip()
			if email == "":
				email = None

			user_id = db.get_user_id_by_email(email)
			if email is None or (not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)) or user_id is None:
				db.remove_recovery_code_by_user_id(user_id)
				session["is_already_created_new_password"] = False
				return render_template("reset_password.html", is_invalid_mail=1, show_recovery_code=0, is_invalid_recovery_code=0, show_verif_code=0, email=email)
			is_2fa_enabled = db.get_is_2fa_enabled_by_login(db.get_login_by_user_id(user_id))
			if is_2fa_enabled and _2fa_recovery_code == "":
				db.remove_recovery_code_by_user_id(user_id)
				session["is_already_created_new_password"] = False
				return render_template("reset_password.html", is_invalid_mail=0, show_recovery_code=1, is_invalid_recovery_code=0, disable_recovery_code=0, show_verif_code=0, email=email, recovery_code="")
			if is_2fa_enabled and db.get_2fa_recovery_code_by_user_id(user_id) != _2fa_recovery_code:
				db.remove_recovery_code_by_user_id(user_id)
				session["is_already_created_new_password"] = False
				return render_template("reset_password.html", is_invalid_mail=0, show_recovery_code=1, is_invalid_recovery_code=1, disable_recovery_code=0, show_verif_code=0, email=email, recovery_code=_2fa_recovery_code)

			recovery_code = db.get_recovery_code_by_user_id(user_id)

			is_password_reseted = 0
			is_wrong_verif_code = 0
			if verif_code != "":
				if int(verif_code) == recovery_code:
					is_password_reseted = 1
					if not session.get("is_already_created_new_password"):
						db.set_is_2fa_enabled_by_user_id(user_id, 0)
						new_password = generate_password()
						db.change_user_password_by_user_id(user_id, new_password)
						threading.Thread(target=email_sender.send_user_data, args=(email, db.get_login_by_user_id(user_id), new_password,)).start()
						session["is_already_created_new_password"] = True
				else:
					is_wrong_verif_code = 1
			else:
				if recovery_code is None:
					recovery_code = random.randint(100000, 999999)
					threading.Thread(target=email_sender.send_recovery_code, args=(email, recovery_code,)).start()
					db.set_recovery_code(user_id, recovery_code)
			return render_template("reset_password.html",
									user_id=user_id,
									resent_email_cooldown=config.RESENT_EMAIL_COOLDOWN,
									is_last_msg=is_password_reseted,
									is_invalid_mail=0,
									is_wrong_verif_code=is_wrong_verif_code,
									is_password_reseted=is_password_reseted,
									disable_recovery_code=(_2fa_recovery_code != ""),
									show_verif_code=1,
									email=email,
									recovery_code=_2fa_recovery_code,
									verif_code=verif_code)
		return render_template("reset_password.html")

	finally:
		db.close_connection()


@app.route('/reset-acсount-2fa/', methods=["GET", "POST"])
def reset_account_2fa():
	db = Database(config.DB_NAME)
	try:
		if session.get('logged_in', False):
			return redirect("/")

		if request.method == "POST":
			email = request.form.get("email", "").strip()
			_2fa_recovery_code = request.form.get("2fa_recovery_code", "").strip()
			verif_code = request.form.get("verif_code", "").strip()
			if email == "":
				email = None

			user_id = db.get_user_id_by_email(email)
			if email is None or (not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email)) or user_id is None:
				db.remove_recovery_code_by_user_id(user_id)
				return render_template("reset_account_2fa.html", is_invalid_mail=1, show_recovery_code=0, is_invalid_recovery_code=0, show_verif_code=0, email=email)
			is_2fa_enabled = db.get_is_2fa_enabled_by_login(db.get_login_by_user_id(user_id))
			if is_2fa_enabled and _2fa_recovery_code == "":
				db.remove_recovery_code_by_user_id(user_id)
				return render_template("reset_account_2fa.html", is_invalid_mail=0, show_recovery_code=1, is_invalid_recovery_code=0, disable_recovery_code=0, show_verif_code=0, email=email, recovery_code="")
			if is_2fa_enabled and db.get_2fa_recovery_code_by_user_id(user_id) != _2fa_recovery_code:
				db.remove_recovery_code_by_user_id(user_id)
				return render_template("reset_account_2fa.html", is_invalid_mail=0, show_recovery_code=1, is_invalid_recovery_code=1, disable_recovery_code=0, show_verif_code=0, email=email, recovery_code=_2fa_recovery_code)

			recovery_code = db.get_recovery_code_by_user_id(user_id)

			is_password_reseted = 0
			is_wrong_verif_code = 0
			if verif_code != "":
				if int(verif_code) == recovery_code:
					is_password_reseted = 1
					db.set_is_2fa_enabled_by_user_id(user_id, 0)
				else:
					is_wrong_verif_code = 1
			else:
				if recovery_code is None:
					recovery_code = random.randint(100000, 999999)
					threading.Thread(target=email_sender.send_recovery_code, args=(email, recovery_code,)).start()
					db.set_recovery_code(user_id, recovery_code)
			return render_template("reset_account_2fa.html",
									user_id=user_id,
									resent_email_cooldown=config.RESENT_EMAIL_COOLDOWN,
									is_invalid_mail=0,
									is_wrong_verif_code=is_wrong_verif_code,
									is_password_reseted=is_password_reseted,
									disable_recovery_code=(_2fa_recovery_code != ""),
									show_verif_code=1,
									email=email,
									recovery_code=_2fa_recovery_code,
									verif_code=verif_code)
		return render_template("reset_account_2fa.html")

	finally:
		db.close_connection()


@app.route("/resendVerifCode/<int:user_id>/", methods=["POST"])
def resendVerifCode(user_id):
	db = Database(config.DB_NAME)
	try:
		if session.get('logged_in', False):
			return jsonify({"is_ok": False})

		threading.Thread(target=email_sender.send_recovery_code, args=(db.get_user_email_by_user_id(user_id), db.get_recovery_code_by_user_id(user_id),)).start()
		return jsonify({"is_ok": True})

	finally:
		db.close_connection()


@app.route("/resendPassword/<int:user_id>/", methods=["POST"])
def resendPassword(user_id):
	db = Database(config.DB_NAME)
	try:
		if session.get('logged_in', False):
			return jsonify({"is_ok": False})

		user_login = db.get_login_by_user_id(user_id)
		threading.Thread(target=email_sender.send_user_data, args=(db.get_user_email_by_user_id(user_id), user_login, db.get_user_password_by_login(user_login),)).start()
		return jsonify({"is_ok": True})

	finally:
		db.close_connection()


@app.route('/logout/')
def logout():
	session['logged_in'] = False
	session['login'] = None
	return redirect('/')


@app.route('/profile/')
@add_one_to_views
def profile():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)):
			return redirect("/")

		user_id = db.get_user_id_by_login(user_login)
		if not db.get_is_2fa_enabled_by_login(user_login):
			db.set_2fa_recovery_code_by_user_id(user_id, config.RANDOM_2FA_RECOVERY_CODE())

		user_password = db.get_user_password_by_login(user_login)
		first_name, last_name, middle_name, mail, phone = db.get_user_name_by_login(user_login)

		user_avatar_path = f"/static/user-avatars/{user_id}.png"
		is_have_avatar = True
		if not os.path.exists("." + user_avatar_path):
			user_avatar_path = "/static/img/user-avatar.png"
			is_have_avatar = False

		user_secret = db.get_user_secret_by_login(user_login)
		qr_code_path = f"./static/qr-codes/{user_secret}.png"
		if not os.path.exists(qr_code_path):
			totp = pyotp.TOTP(user_secret)
			uri = totp.provisioning_uri(name=mail, issuer_name=config.APP_NAME)
			img = qrcode.make(uri)
			img.save(qr_code_path)

		return render_template("profile.html",
								is_can_changind=1,
								user_id=user_id,
								user_login=user_login,
								user_password=user_password,
								user_type=db.get_user_type_by_login(user_login),
								first_name=first_name,
								last_name=last_name,
								middle_name=middle_name,
								mail=(mail if mail is not None else ""),
								phone=(phone if phone is not None else ""),
								user_avatar_path=user_avatar_path,
								default_user_avatar="/static/img/user-avatar.png",
								is_have_avatar=int(is_have_avatar),
								is_other_profile=False,
								is_2fa_enabled=db.get_is_2fa_enabled_by_login(user_login),
								user_secret=user_secret,
								recovery_code=db.get_2fa_recovery_code_by_login(user_login))
	finally:
		db.close_connection()


@app.route('/profile/<int:user_id>/')
@add_one_to_views
def other_profile(user_id):
	db = Database(config.DB_NAME)
	try:
		if not session.get('logged_in', False):
			return redirect("/")

		if user_id not in db.get_all_user_ids():
			abort(404)

		user_type = db.get_user_type_by_login(session['login'])

		if user_type == 0 or user_type == 1:
			user_condition = (user_type == 0) or (user_id == db.get_user_id_by_login(session['login']))
			user_login = db.get_login_by_user_id(user_id)
			user_password = db.get_user_password_by_login(user_login)
			first_name, last_name, middle_name, mail, phone = db.get_user_name_by_login(user_login)

			user_avatar_path = f"/static/user-avatars/{user_id}.png"
			is_have_avatar = True
			if not os.path.exists("." + user_avatar_path):
				user_avatar_path = "/static/img/user-avatar.png"
				is_have_avatar = False
			return render_template("profile.html",
								is_can_changind=int(user_condition),
								user_id=user_id,
								user_login=(user_login if user_condition else ""),
								user_password=(user_password if user_condition else ""),
								user_type=db.get_user_type_by_login(session['login']),
								first_name=first_name,
								last_name=last_name,
								middle_name=middle_name,
								mail=(mail if mail is not None else ""),
								phone=(phone if phone is not None else ""),
								user_avatar_path=user_avatar_path,
								default_user_avatar="/static/img/user-avatar.png",
								is_have_avatar=int(is_have_avatar),
								is_other_profile=True,
								is_2fa_enabled=False)
		return redirect("/")

	finally:
		db.close_connection()


@app.route('/create-new-teacher/')
@app.route('/create-new-student/')
@add_one_to_views
def create_new_student():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 0:
			return redirect("/")
		return render_template("create_new_teacher_student.html", user_type=(1 if "create-new-teacher" in request.path else 2))

	finally:
		db.close_connection()


@app.route('/addNewUserData/', methods=["POST"])
def addNewUserData():
	db = Database(config.DB_NAME)
	try:
		if not session.get('logged_in', False):
			return redirect("/")

		user_type = request.args.get("user_type")
		login = request.args.get("login")
		is_wrong_login = False
		if login in db.get_all_logins(): is_wrong_login = True
		password = request.args.get("password")
		first_name = request.args.get("first_name").strip()
		last_name = request.args.get("last_name").strip()
		middle_name = request.args.get("middle_name").strip()

		mail = request.args.get('mail').strip()
		is_mail_invalid = False
		if mail == "": mail = None
		if mail is not None and ((not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', mail)) or mail in db.get_mails_except_user_id()): is_mail_invalid = True

		phone = request.args.get("phone")
		is_wrong_phone = False
		if phone == "": phone = None
		if phone is not None and len(phone) != 17: is_wrong_phone = True

		if is_wrong_phone or is_mail_invalid or is_wrong_login:
			return jsonify({"is_ok": False, "is_wrong_login": is_wrong_login, "is_mail_invalid": is_mail_invalid, "is_wrong_phone": is_wrong_phone})

		user_secret = pyotp.random_base32()
		totp = pyotp.TOTP(user_secret)
		uri = totp.provisioning_uri(name=mail, issuer_name=config.APP_NAME)
		img = qrcode.make(uri)
		img.save(f"./static/qr-codes/{user_secret}.png")

		db.add_user_data(int(user_type), login, password, first_name, last_name, middle_name, mail, phone, user_secret)
		user_id = db.get_user_id_by_login(login)
		return jsonify({"is_ok": True, "user_id": user_id})

	finally:
		db.close_connection()


@app.route("/saveUserData/", methods=["POST"])
def saveUserData():
	db = Database(config.DB_NAME)
	try:
		time.sleep(1)

		if not session.get('logged_in', False):
			return redirect("/")

		user_id = request.args.get("user_id")
		login = request.args.get("login")
		is_wrong_login = False
		if login in [i for i in db.get_all_logins() if i != db.get_login_by_user_id(user_id)]: is_wrong_login = True
		password = request.args.get("password")
		first_name = request.args.get("first_name").strip()
		last_name = request.args.get("last_name").strip()
		middle_name = request.args.get("middle_name").strip()

		mail = request.args.get('mail').strip()
		is_mail_invalid = False
		if mail == "": mail = None
		if mail is not None and ((not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', mail)) or mail in db.get_mails_except_user_id(user_id)): is_mail_invalid = True

		phone = request.args.get("phone")
		is_wrong_phone = False
		if phone == "": phone = None
		if phone is not None and len(phone) != 18: is_wrong_phone = True

		if is_wrong_phone or is_mail_invalid or is_wrong_login:
			return jsonify({"is_ok": False, "is_wrong_login": is_wrong_login, "is_mail_invalid": is_mail_invalid, "is_wrong_phone": is_wrong_phone})

		if db.get_login_by_user_id(user_id) == session.get('login'):
			session['login'] = login
		db.update_user_data_by_user_id(user_id, login, password, first_name, last_name, middle_name, mail, phone)
		return jsonify({"is_ok": True})

	finally:
		db.close_connection()


@app.route("/saveImage/", methods=["POST"])
def saveImage():
	db = Database(config.DB_NAME)
	try:
		user_id = request.args.get("user_id")
		if (not session.get('logged_in', False)) or user_id is None:
			return redirect("/")

		login = db.get_login_by_user_id(user_id)

		try:
			if request.files['myFile'].filename.split('.')[-1] in ["jpg", "jpeg", "png"]:
				file_path = f"./static/user-avatars/{db.get_user_id_by_login(login)}.png"
				request.files['myFile'].save(file_path)

				img = Image.open(file_path)
				width, height = img.size
				if width != height:
					if width > height:
						a = (width - height) // 2
						img = img.crop((a, 0, width - a, height))
					else:
						a = (height - width) // 2
						img = img.crop((0, a, width, height - a))
				img = img.resize((800, 800))
				img.save(file_path)

				return jsonify({"path": f"{file_path[1:]}?v={datetime.datetime.now().strftime('%f')}", "is_changed": True, "is_wrong_extension": False})
			return jsonify({"is_wrong_extension": True})

		except KeyError:
			return jsonify({"path": "", "is_changed": False, "is_wrong_extension": False})
	finally:
		db.close_connection()


@app.route("/removeUserAvatar/", methods=["POST"])
def removeUserAvatar():
	db = Database(config.DB_NAME)
	try:
		if not session.get('logged_in', False):
			return redirect("/")

		try:
			os.remove(f"./static/user-avatars/{db.get_user_id_by_login(session['login'])}.png")
		except FileNotFoundError:
			pass
		return "Ok"
	finally:
		db.close_connection()


@app.route("/deleteAccount/<int:user_id>/", methods=["POST"])
def deleteAccount(user_id):
	db = Database(config.DB_NAME)
	try:
		if not session.get('logged_in', False):
			return redirect("/")

		redirect_to = unquote(request.args.get("from", "/profile"))
		if user_id == db.get_user_id_by_login(session.get("login")):
			del session["login"]
			session["logged_in"] = False
			redirect_to = "/"

		user_secret = db.get_user_secret_by_login(db.get_login_by_user_id(user_id))
		db.delete_user_by_user_id(user_id)
		qr_code_path = f"./static/qr-codes/{user_secret}.png"
		if os.path.exists(qr_code_path):
			os.remove(qr_code_path)
		return jsonify({"is_ok": True, "redirect_to": redirect_to})
	finally:
		db.close_connection()


@app.route("/verifyCode/", methods=["POST"])
def verifyCode():
	db = Database(config.DB_NAME)
	try:
		time.sleep(1)

		token = request.args.get("token")
		code = request.args.get("code")

		if token == "" or code == "":
			return "0"

		totp = pyotp.TOTP(token)
		verify = totp.verify(int(code))
		if verify:
			db.set_is_2fa_enabled(token, 1)
		return str(int(verify))
	finally:
		db.close_connection()


@app.route("/disable2FA/", methods=["POST"])
def disable2FA():
	db = Database(config.DB_NAME)
	try:
		time.sleep(1)

		token = request.args.get("token")
		db.set_is_2fa_enabled(token, 0)
		return "Ok"
	finally:
		db.close_connection()


@app.route('/')
@app.route('/dashboard/')
@add_one_to_views
def home():
	db = Database(config.DB_NAME)
	try:
		is_logged_in = session.get('logged_in', False)
		user_login = session.get("login")

		website_views_labels, website_views = get_website_views_count_by_date(db.get_website_views_count_all())
		entrys_exits_labels, entrys, exits = get_entrys_exits_count_by_date(db.get_all_entrys_exits())
		entrys_exits_history = dict()
		for i in [i for i in entrys_exits_labels if i != ""]:
			rows = list()
			for j in db.get_history_by_day(i)[::-1]:
				items = [datetime.datetime.strptime(j[0], "%Y-%m-%d %H:%M:%S.%f").strftime("%H:%M:%S"),
						 j[1], db.get_uid_by_user_id(j[2])]
				#  ---start
				card_data = db.get_info_by_uid(items[2])[0]
				if len(card_data) != 0:
					user_type = card_data[9]
					if user_type == 0:
						items.append("Admin")
						items.append("-")
					elif user_type == 1:
						items.append("Teacher")
						items.append("-")
					elif user_type == 2:
						items.append("Student")
						items.append(db.get_class_name_by_class_id(db.get_class_id_by_user_id(j[2])))
					else:
						items.append("-")
						items.append("-")
					items.append(" ".join(card_data[3:5]))
				else:
					items.append("-")
				#  ---end
				rows.append(items)
			entrys_exits_history.update([(i, rows)])

		return render_template("home.html",
								is_logged_in=int(is_logged_in),
								user_type=(db.get_user_type_by_login(user_login) if user_login is not None else 10),
								fire_alarm_state=int(db.get_alarm_value("fire_alarm")),
								website_views_labels=website_views_labels,
								website_views=website_views,
								registered_users_count=format_number(db.get_all_users_count()),
								entrys_exits_history=(entrys_exits_history if bool(is_logged_in) and (db.get_user_type_by_login(user_login) == 0 or db.get_user_type_by_login(user_login) == 1) else dict()),
								entrys_exits_labels=entrys_exits_labels,
								entrys=entrys,
								exits=exits,
								website_views_count=format_number(db.get_website_views_count_now()),
								website_views_persent=get_persent(db.get_website_views_count_now(), (db.get_website_views_count_now(date=(datetime.datetime.now() - relativedelta(days=1)).strftime("%d.%m.%Y")))),
								entrys_count=format_number(db.get_today_entrys_count()),
								entrys_count_persent=get_persent(db.get_today_entrys_count(), (db.get_today_entrys_count(date=(datetime.datetime.now() - relativedelta(days=1)).strftime("%d.%m.%Y")))),
								exits_count=format_number(db.get_today_exits_count()),
								exits_count_persent=get_persent(db.get_today_exits_count(), (db.get_today_exits_count(date=(datetime.datetime.now() - relativedelta(days=1)).strftime("%d.%m.%Y")))))
	finally:
		db.close_connection()


def get_number_postfix(number):
	number = str(number)
	if number[-1] == '1' and (not number.endswith("11")):
		number_postfix = "st"
	elif number[-1] == '2' and (not number.endswith("12")):
		number_postfix = "nd"
	elif number[-1] == '3' and (not number.endswith("13")):
		number_postfix = "rd"
	else:
		number_postfix = "th"
	return number_postfix


@app.route("/admin-schedule/", methods=["GET", "POST"])
@add_one_to_views
def admin_schedule():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 0:
			return redirect("/")

		if request.method == "POST":
			grade = request.form.get("grade", "").strip()
			class_letter = request.form.get("class-letter", "").strip()
			if grade != "" and class_letter != "":
				db.add_new_class_data(grade, class_letter)
				return redirect("/admin-schedule/")

		schedule = db.get_all_classes_data()
		new_schedule = list()
		for i in schedule:
			new_schedule.append([f"{i[0]}{get_number_postfix(i[0])}", i[1]])

		return render_template("schedule_admin.html", schedule=new_schedule)
	finally:
		db.close_connection()


@app.route("/admin-class-schedule/<int:class_id>/")
def admin_class_schedule(class_id):
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 0:
			return redirect("/")

		schedule = db.get_schedule_by_class_id(class_id)
		new_schedule = list()
		now_weekday = datetime.datetime.today().weekday()
		for i in schedule.items():
			date = datetime.datetime.now() - relativedelta(days=(now_weekday - i[0]))
			if str(date.day)[-1] == '1' and date.day != 11:
				day_str = "st"
			elif str(date.day)[-1] == '2' and date.day != 12:
				day_str = "nd"
			elif str(date.day)[-1] == '3' and date.day != 13:
				day_str = "rd"
			else:
				day_str = "th"

			for j in i[1]:
				is_now_this_lesson = (date.strftime("%Y-%m-%d") == datetime.datetime.now().strftime("%Y-%m-%d")) and \
										(j["lesson_time__start"] <= pytz.UTC.localize(datetime.datetime.strptime(from_utc(now_utc(), session["timezone"]).strftime("%H:%M"), "%H:%M")) <= j["lesson_time__end"])
				j.update([("lesson_date", date.strftime("%Y-%m-%d")),
							("is_now_this_lesson", is_now_this_lesson),
							("lesson_time__start", j["lesson_time__start"].strftime("%H:%M")),
							("lesson_time__end",  j["lesson_time__end"].strftime("%H:%M"))])
			new_schedule.append([config.WEEK_DAYS[i[0]], f"{date.day}{day_str} of {date.strftime('%B')}", i[1], day_is_holiday(date), i[0]])

		return render_template("admin_class_schedule.html", class_name=db.get_class_name_by_class_id(class_id), class_id=class_id, schedule=new_schedule, lessons=db.get_all_lessons(), teachers=db.get_all_teachers())
	finally:
		db.close_connection()


@app.route("/admin-teachers-list/")
@add_one_to_views
def admin_teachers_list():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 0:
			return redirect("/")

		default_avatar = "/static/img/user-avatar.png"
		user_avatar_path = "/static/user-avatars/{}.png"
		teachers_list = list(map(lambda t: [t[0], f"{t[1]} {t[2]} {t[3]}", t[4], t[5], (default_avatar if not os.path.exists("." + user_avatar_path.format(t[0])) else user_avatar_path.format(t[0]))], db.get_users_data_by_user_type(1)))

		return render_template("admin_teachers_list.html", teachers_list=teachers_list)
	finally:
		db.close_connection()


@app.route("/admin-students-list/")
@add_one_to_views
def admin_students_list():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 0:
			return redirect("/")

		default_avatar = "/static/img/user-avatar.png"
		user_avatar_path = "/static/user-avatars/{}.png"
		students_list = list(map(lambda t: [t[0], f"{t[1]} {t[2]} {t[3]}", t[4], t[5], (default_avatar if not os.path.exists("." + user_avatar_path.format(t[0])) else user_avatar_path.format(t[0]))], db.get_users_data_by_user_type(2)))

		return render_template("admin_students_list.html", students_list=students_list)
	finally:
		db.close_connection()


@app.route("/teacher-schedule/")
@add_one_to_views
def teacher_schedule():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 1:
			return redirect("/")

		schedule = db.get_teacher_schedule_by_user_id(db.get_user_id_by_login(user_login))
		new_schedule = list()
		now_weekday = datetime.datetime.today().weekday()
		for i in schedule.items():
			date = datetime.datetime.now() - relativedelta(days=(now_weekday - i[0]))
			if str(date.day)[-1] == '1' and date.day != 11:
				day_str = "st"
			elif str(date.day)[-1] == '2' and date.day != 12:
				day_str = "nd"
			elif str(date.day)[-1] == '3' and date.day != 13:
				day_str = "rd"
			else:
				day_str = "th"

			ru_holidays = holidays.country_holidays('RU')
			for j in i[1]:
				is_now_this_lesson = (date.strftime("%Y-%m-%d") == datetime.datetime.now().strftime("%Y-%m-%d")) and \
										(j["lesson_time__start"] <= pytz.UTC.localize(datetime.datetime.strptime(from_utc(now_utc(), session["timezone"]).strftime("%H:%M"), "%H:%M")) <= j["lesson_time__end"])
				j.update([("lesson_date", date.strftime("%Y-%m-%d")),
							("is_now_this_lesson", is_now_this_lesson),
							("lesson_time__start", j["lesson_time__start"].strftime("%H:%M")),
							("lesson_time__end", j["lesson_time__end"].strftime("%H:%M"))])
			new_schedule.append([config.WEEK_DAYS[i[0]], f"{date.day}{day_str} of {date.strftime('%B')}", i[1], ((date in ru_holidays) and config.USE_HOLIDAYS)])

		return render_template("schedule_teacher.html", schedule=new_schedule)
	finally:
		db.close_connection()


@app.route('/teacher-lesson/<int:lesson_id>/<int:class_id>/<string:_lesson_date>/')
@add_one_to_views
def teacher_lesson(lesson_id, class_id, _lesson_date):
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)) or db.get_user_type_by_login(user_login) != 1:
			return redirect("/")

		lesson_name = db.get_lesson_name_by_lesson_id(lesson_id)
		lesson_date = datetime.datetime.strptime(_lesson_date, "%Y-%m-%d")
		lesson_index = db.get_lesson_index_by_lesson_id_weekday(lesson_id, lesson_date.weekday())
		first_month_day = datetime.datetime.strptime(f"01-{'0' + str(lesson_date.month) if len(str(lesson_date.month)) == 1 else lesson_date.month}-{lesson_date.year} 00:00:00", "%d-%m-%Y %H:%M:%S")
		now = datetime.datetime.now()

		students = db.get_students_marks_by_lesson_id_class_id_lesson_date(lesson_id, class_id, _lesson_date)
		return render_template("teacher_lesson.html",
							   students=sorted(students, key=lambda t: t["name"]),
							   lesson_name=lesson_name,
							   lesson_id=lesson_id,
							   class_id=class_id,
							   lesson_date=lesson_date.strftime("%d.%m.%Y"),
							   _lesson_date=_lesson_date,
							   month_name=lesson_date.strftime('%B'),
							   days_in_month=[(i, now.strftime("%d.%m.%Y") == (first_month_day + relativedelta(days=i)).strftime("%d.%m.%Y"))
							                  for i in range(calendar.monthrange(lesson_date.year, lesson_date.month)[1]) if check_day_on_holiday(first_month_day + relativedelta(days=i), lesson_id)],
							   need_to_show_check_students_btn=((lesson_index > 0) and (lesson_date.strftime("%Y-%m-%d") == lesson_date)),
							   need_to_show_students_exits=(datetime.datetime.now().strftime("%Y-%m-%d") == _lesson_date),
							   can_students_leave=db.get_can_students_leave_by_lesson_id(lesson_id),
		                       exits_data=db.get_exits_data(lesson_id, class_id, _lesson_date))
	finally:
		db.close_connection()


@app.route("/saveStudentMark/", methods=["POST"])
def saveStudentMark():
	db = Database(config.DB_NAME)
	try:
		user_login = session.get("login")
		if user_login is None or (not session.get('logged_in', False)):
			return jsonify({"is_ok": False})

		if db.get_user_type_by_login(user_login) != 1:
			return jsonify({"is_ok": False})

		user_id = request.args.get("user_id")
		lesson_id = request.args.get("lesson_id")
		lesson_date = datetime.datetime.strptime(request.args.get("lesson_date"), "%d.%m.%Y").strftime("%Y-%m-%d")
		mark = request.args.get("mark")
		db.set_student_mark_by_lesson_id_lesson_date_user_id(lesson_id, lesson_date, user_id, mark)

		return jsonify({"is_ok": True})
	finally:
		db.close_connection()


@app.route('/test_table/')
@add_one_to_views
def test_table():
	return render_template("test_table.html")


@app.route('/edit_profile/<int:profile_id>/')
@add_one_to_views
def edit_profile(profile_id):
	return str(profile_id)


@app.route('/test/')
def test():
	return render_template("test.html")


@app.route('/api/')
@add_one_to_views
def api_methogs():
	return """
				<p><b>Check uid</b> <code><span>POST</span> /api/check_uid/[uid]/?cabinet_id=[cabinet_id]&access_token=[access_token]</code></p>
				<p><b>Create new profile</b> <code><span>POST</span> /api/create_new_profile/?full_name=[full_name]&user_type=[user type]&access_token=[access_token]</code></p>
				<p><b>Edit profile</b> <code><span>POST</span> /api/edit_profile/?profile_id=[profile_id]&full_name=[full_name]&user_type=[user type]&access_token=[access_token]</code></p>
				<p><b>Get profiles by uid</b> <code><span>POST</span> /api/get_profiles/[uid]/?access_token=[access_token]</code></p>
				<style>p {display: flex; flex-direction: column;} code {margin-left: 15px} span {color: #1db954; font-weight: 600;} body {font-family: Roboto;}</style>
		   """


@app.route('/api/<path:method>/', methods=['GET', 'POST'])
@app.route('/api/<path:method>/<string:value>/', methods=['GET', 'POST'])
@app.route('/api/<path:method>/<string:value>/<string:value2>/', methods=['GET', 'POST'])
@app.route('/api/<path:method>/<string:value>/<string:value2>/<string:value3>/', methods=['GET', 'POST'])
def api(method, value="", value2="", value3=""):
	db = Database(config.DB_NAME)
	try:
		print("[bold green]" + request.url.replace("%20", " "))
		if request.method == "POST":
			if method == "ping":
				return "Ok"

			elif method == "get_cabinets":
				return Response(json.dumps(db.get_cabinets()), mimetype='application/json')

			elif method == "get_all_users":
				users = {0: list(), 1: list(), 2: dict()}
				for user_type in users.keys():
					for user_data in db.get_users_data_by_user_type(user_type):
						if user_type != 2:
							users[user_type].append(user_data)
						else:
							if users[user_type].get(user_data[7]) is None:
								users[user_type][user_data[7]] = {user_data[8]: [user_data]}
							else:
								if users[user_type][user_data[7]].get(user_data[8]) is None:
									users[user_type][user_data[7]][user_data[8]] = [user_data]
								else:
									users[user_type][user_data[7]][user_data[8]].append(user_data)
				return jsonify(json.dumps(users))

			elif method == "upload_user_data":
				if value != "" and value2 != "":
					user_id = value
					uid = value2.replace("%20", " ").strip()
					db.update_user_uid_by_user_id(user_id, uid)
					return jsonify(json.dumps({"user_data": db.get_user_data_by_user_id(user_id)}))
				return abort(412)

			elif method == "get_user_data":
				if value != "":
					value = value.replace("%20", " ").strip()
					print("UID=" + value)

					data = db.get_info_by_uid(value)
					if len(data) != 0:
						data = list(data[0]) + [db.get_class_name_by_class_id(db.get_class_id_by_user_id(data[0][0])) if data[0][9] == 2 else "-"]
					return Response(json.dumps(data), mimetype='application/json')
				return abort(412)

			elif method == "get_user_avatar":
				if value != "":
					data = db.get_info_by_uid(value)
					if len(data) != 0:
						user_avatar_path = f"static/user-avatars/{data[0][0]}.png"
						return send_file(user_avatar_path if os.path.exists(user_avatar_path) else "static/img/user-avatar.png")
					return send_file("static/img/user-avatar.png")
				return abort(412)

			elif method == "add_user":
				json_response = request.get_json()
				db.add_user_to_users(json_response["name"], json_response["cabinet"], json_response["user_type"], json_response["uid"])
				return "Ok"

			elif method == "entry_uid":
				if value != "":
					value = value.replace("%20", " ").strip()
					print("UID=" + value)

					response = db.is_uid_exists_in_users(value)
					user_id = db.get_user_id_by_uid(value)

					if response:
						db.add_user_to_history("entry", user_id)
						user_type = db.get_user_type_by_user_id(user_id)
						if user_type == 2:
							lesson_id, _ = db.get_lesson_id_class_id_by_user_id(user_id)
							if lesson_id is not None:
								lesson_date = datetime.datetime.now().strftime("%Y-%m-%d")
								print("LESSON DATE:", lesson_date)
								if db.get_student_mark_by_lesson_id_user_id_lesson_date(lesson_id, user_id, lesson_date) == "A":
									db.set_student_mark_by_lesson_id_lesson_date_user_id(lesson_id, lesson_date, user_id, "")
							else:
								response = False
						else:
							response = True

					return str(int(bool(response)))
				return "0"

			elif method == "add_uid":
				return "Ok"

			elif method == "exit_uid":
				if value != "":
					value = value.replace("%20", " ").strip()
					print("UID=" + value)

					response = db.is_uid_exists_in_users(value)
					user_id = db.get_user_id_by_uid(value)

					if response:
						user_type = db.get_user_type_by_user_id(user_id)
						print("USER TYPE:", user_type)
						if user_type == 2:
							lesson_id, _ = db.get_lesson_id_class_id_by_user_id(user_id)
							print("LESSON ID:", lesson_id)
							if lesson_id is not None:
								print("RET:", db.get_can_students_leave_by_lesson_id(lesson_id))
								if db.get_can_students_leave_by_lesson_id(lesson_id):
									db.add_user_to_history("exit", db.get_user_id_by_uid(value))
									return "1"
								else:
									return "0"
						db.add_user_to_history("exit", db.get_user_id_by_uid(value))
						return "1"
				return "0"

			elif method == "get_fire_alarm_state":
				fire_alarm_state = db.get_alarm_value("fire_alarm")
				return str(int(fire_alarm_state if fire_alarm_state != None else 0))
			elif method == "set_fire_alarm_state":
				if value != "":
					db.set_alarm_value("fire_alarm", bool(int(value)))
					return "1"
				return "0"

			elif method == "check_students_for_absence":
				if value == "" or value2 == "":
					return jsonify({"is_error": True})
				time.sleep(1)

				lesson_id = value
				class_id = value2
				lesson_date = datetime.datetime.now()

				need_remove_absence_mark = list()
				for user_id in db.get_all_students_by_class_id(class_id):
					previous_lesson_id = db.get_previous_lesson_id_by_lesson_id_lesson_date_class_id(lesson_id, lesson_date.strftime("%Y-%m-%d"), class_id)
					previous_mark = db.get_student_mark_by_lesson_id_user_id_lesson_date(previous_lesson_id, user_id, datetime.datetime.strptime(lesson_date.strftime("%Y-%m-%d"), "%Y-%m-%d"))
					if previous_lesson_id is not None:
						if previous_mark != "A":
							entrys_exits = db.get_all_entrys_exits_by_user_id_date(user_id, lesson_date.strftime("%d.%m.%Y"))
							if entrys_exits == list() or sorted(entrys_exits, key=lambda t: t[0])[-1][1] != "exit":
								need_remove_absence_mark.append({"user_id": user_id, "lesson_id": lesson_id, "lesson_date": lesson_date.strftime("%d.%m.%Y")})
				return jsonify({"day": datetime.datetime.now().day, "data": need_remove_absence_mark})
			elif method == "remove_class":
				if value == "":
					return jsonify({"is_error": True})

				db.remove_class_data(value)
				return jsonify({"is_ok": True})

			elif method == "update_class_schedule":
				if value == "":
					return jsonify({"is_error": True})

				class_id = value

				schedule = request.json
				db.remove_lessons_from_schedule_by_class_id(class_id)
				for weekday_index, j in schedule.items():
					for lesson in j:
						lesson_time__start, lesson_time__end = map(lambda t: t + ":00", lesson[2].split("-"))
						db.add_new_lesson_in_schedule(class_id, lesson[0], weekday_index, lesson_time__start, lesson_time__end)
				return jsonify({"is_ok": True})

			elif method == "update_user_timezone":
				if value == "" or value2 == "":
					return jsonify({"is_error": True})
				timezone = f"{value}/{value2}"
				session["timezone"] = timezone
				return jsonify({"is_ok": True, "timezone": timezone})

			elif method == "create_lesson":
				if value == "" or value2 == "":
					return jsonify({"is_error": True})

				user_name = db.get_user_name_by_login(db.get_login_by_user_id(value))[:4]
				user_name = f"{user_name[0]} {user_name[1]} {user_name[2]}"
				try:
					return jsonify({"is_ok": True, "lesson_id": db.add_new_lesson_in_lessons_by_teacher_id(value, value2), "lesson_name": value2, "teacher_name": user_name})
				except sqlite3.IntegrityError:
					return jsonify({"is_error": True, "error": "A lesson with the same name already exists!"})

			elif method == "remove_lesson":
				if value == "":
					return jsonify({"is_error": True})

				db.remove_lesson_by_lesson_id(value)
				return jsonify({"is_ok": True})

			elif method == "set_can_students_leave":
				if value == "" or value2 == "":
					return jsonify({"is_error": True})

				db.set_can_students_leave_by_lesson_id(value, value2)
				return jsonify({"is_ok": True})

			elif method == "get_exits_data":
				if value == "" or value2 == "" or value3 == "":
					return jsonify({"is_error": True})

				return jsonify(db.get_exits_data(value, value2, value3))

			else:
				abort(404)
		else:
			abort(403)
	finally:
		db.close_connection()


@app.route("/404/")
def not_found_page():
	return abort(404)


@app.route("/500/")
def server_error_page():
	return abort(500)


@app.errorhandler(404)
def not_found(error):
	return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(error):
	return render_template('500.html'), 500


app.jinja_env.globals.update(enumerate=_enumerate)
app.jinja_env.globals.update(get_redirect_time=lambda: config.REDIRECT_AFTER_DELETE_ACCOUNT_TIME)


if __name__ == '__main__':
	app.debug = True
	app.run(host="10.10.10.58", port=config.PORT)
