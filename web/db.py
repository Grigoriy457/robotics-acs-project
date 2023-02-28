import sqlite3
import zoneinfo

import pytz
import datetime
import time
from dateutil.relativedelta import relativedelta
import holidays
import calendar
import os
import threading
import platform

import config


TZ_OFFSET = lambda: 0 if platform.system() == "Windows" else 2


def datetime_strftime(unix_time, with_tz=False):
	_time = datetime.datetime.strptime(unix_time, "%H:%M:%S").replace(tzinfo=pytz.timezone('CET')).astimezone(pytz.timezone("UTC")) + relativedelta(hours=1)
	if platform.system() == "Windows" or (not with_tz):
		return _time
	else:
		return _time + relativedelta(hours=TZ_OFFSET())


def check_day_on_holiday(date, lesson_days):
	return ((date not in holidays.country_holidays('RU')) or (not config.USE_HOLIDAYS)) and (date.weekday() in lesson_days)


class Database:
	def __init__(self, db_file, timezone="Europe/Moscow"):
		self.connection = sqlite3.connect(db_file, check_same_thread=False)
		# self.connection.isolation_level = None
		self.cursor = self.connection.cursor()
		self.timezone = timezone
		with self.connection:
			self.cursor.execute("PRAGMA foreign_keys=ON")

	def get_cabinets(self):
		with self.connection:
			return self.cursor.execute("""SELECT * FROM cabinets;""").fetchall()

	def is_uid_exists_in_users(self, uid):
		with self.connection:
			return bool(len(self.cursor.execute("""SELECT * FROM web_users WHERE uid = ?;""", (uid,)).fetchall()))

	def get_all_users_count(self):
		with self.connection:
			return len(self.cursor.execute("""SELECT * FROM web_users;""").fetchall())

	def _get_info_by_uid(self, uid):
		with self.connection:
			return self.cursor.execute("""SELECT * FROM web_users WHERE uid = ?;""", (uid,)).fetchall()

	def get_info_by_uid(self, uid, with_connection=True):
		if with_connection:
			with self.connection:
				return self._get_info_by_uid(uid)
		else:
			return self._get_info_by_uid(uid)

	def get_user_id_by_uid(self, uid):
		with self.connection:
			return self.cursor.execute("""SELECT id FROM web_users WHERE uid = ?;""", (uid,)).fetchone()[0]

	def get_uid_by_user_id(self, user_id):
		with self.connection:
			ret = self.cursor.execute("""SELECT uid FROM web_users WHERE id = ?;""", (user_id,)).fetchone()
			return ret[0] if ret is not None else None

	def add_user_to_users(self, name, cabinet, user_type, uid):
		with self.connection:
			self.cursor.execute("""INSERT INTO users (name, cabinet, user_type, uid) VALUES ('{}', {}, '{}', '{}');""".format(name, cabinet, user_type, uid))

	def add_user_to_history(self, entry_or_exit, user_id):
		with self.connection:
			self.cursor.execute("""INSERT INTO history ([date], entry_or_exit, user_id) VALUES (?, ?, ?);""", (datetime.datetime.now() + relativedelta(hours=TZ_OFFSET()), entry_or_exit, user_id,))

	def get_website_views_count(self, date):
		with self.connection:
			response = self.cursor.execute("""SELECT * FROM website_views WHERE date = ?;""", (date,)).fetchone()
			if response != None:
				response = response[2]
			return response

	def _get_website_views_count_now(self, date):
		response = self.cursor.execute("""SELECT * FROM website_views WHERE date = ?;""", (date,)).fetchone()
		if response != None:
			response = response[2]
		return response

	def get_website_views_count_now(self, date=(datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"), with_connection=True):
		if with_connection:
			with self.connection:
				return self._get_website_views_count_now(date=date)
		else:
			return self._get_website_views_count_now(date=date)

	def get_website_views_count_all(self):
		with self.connection:
			return [i for i in self.cursor.execute("""SELECT * FROM website_views;""").fetchall() if datetime.datetime.strptime(i[1], "%d.%m.%Y") > ((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())) - config.HISTORY_SHOW_LIMIT)]

	def add_one_view_to_website_views(self):
		with self.connection:
			if self.get_website_views_count_now(with_connection=False) == None:
				self.cursor.execute("""INSERT INTO website_views (date, views) VALUES (?, ?);""", ((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"), 1,))
			else:
				try:
					self.cursor.execute("""UPDATE website_views SET views = views + 1 WHERE date = ?;""", ((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"),))
				except sqlite3.OperationalError:
					pass

	def get_entrys_count(self):
		with self.connection:
			return len(self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("entry",)).fetchall())

	def get_today_entrys_count(self, date=(datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y")):
		with self.connection:
			return len(list(filter(lambda t: datetime.datetime.strptime(date, "%d.%m.%Y") < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.strptime(f"{date} 23:59:59", "%d.%m.%Y %H:%M:%S"),
			                  self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("entry",)).fetchall())))

	def get_all_entrys(self):
		with self.connection:
			return list(filter(lambda t: (datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"), "%d.%m.%Y") - config.HISTORY_SHOW_LIMIT) < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f"),
			                   self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("entry",)).fetchall()))

	def get_exits_count(self):
		with self.connection:
			return len(self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("exit",)).fetchall())

	def get_today_exits_count(self, date=(datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y")):
		with self.connection:
			return len(list(filter(lambda t: datetime.datetime.strptime(date, "%d.%m.%Y") < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.strptime(f"{date} 23:59:59", "%d.%m.%Y %H:%M:%S"),
			                  self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("exit",)).fetchall())))

	def get_all_exits(self):
		with self.connection:
			return list(filter(lambda t: (datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"), "%d.%m.%Y") - config.HISTORY_SHOW_LIMIT) < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f"),
			                   self.cursor.execute("""SELECT * FROM history WHERE entry_or_exit = ?;""", ("exit",)).fetchall()))

	def get_history_by_day(self, date: str):
		with self.connection:
			return list(filter(lambda t: datetime.datetime.strptime(date, "%d.%m.%Y") < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.strptime(f"{date} 23:59:59", "%d.%m.%Y %H:%M:%S"),
			                   self.cursor.execute("""SELECT * FROM history;""").fetchall()))

	def get_last_user_id__exit_entry_by_day(self, user_id, date: str):
		with self.connection:
			ret = sorted(list(filter(lambda t: (datetime.datetime.strptime(date, "%d.%m.%Y") < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.strptime(f"{date} 23:59:59.999999", "%d.%m.%Y %H:%M:%S.%f") and t[3] == 0),
			                         self.cursor.execute("""SELECT * FROM history WHERE user_id = ?;""", (user_id,)).fetchall())),
			             key=lambda t: datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f"))
			print("RET:", ret)
			exits = list(filter(lambda t: t[1] == "exit", ret))
			entrys = list(filter(lambda t: t[1] == "entry", ret))
			print(exits, entrys)
			if (len(entrys) != 0) and (len(exits) != 0):
				if datetime.datetime.strptime(exits[-1][0], "%Y-%m-%d %H:%M:%S.%f") < datetime.datetime.strptime(entrys[-1][0], "%Y-%m-%d %H:%M:%S.%f"):
					print("HERE", exits[-1], entrys[-1])
					return exits[-1], entrys[-1]
				else:
					print("HERE (2)", exits[-1], None)
					return exits[-1], None
			print("HERE (3)")
			return None, None

	def get_all_entrys_exits(self):
		with self.connection:
			return list(filter(lambda t: (datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%d.%m.%Y"), "%d.%m.%Y") - config.HISTORY_SHOW_LIMIT) < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f"),
			                   self.cursor.execute("""SELECT * FROM history;""").fetchall()))

	def get_all_entrys_exits_by_user_id_date(self, user_id, date: str):
		with self.connection:
			start_date = datetime.datetime.strptime(date, "%d.%m.%Y")
			end_date = datetime.datetime.strptime(date, "%d.%m.%Y") + relativedelta(days=1)
			return [i for i in filter(lambda t: start_date < datetime.datetime.strptime(t[0], "%Y-%m-%d %H:%M:%S.%f") < end_date,
			                          self.cursor.execute("""SELECT * FROM history WHERE user_id = ?;""", (user_id,)).fetchall())]

	def get_alarm_value(self, alarm_type):
		with self.connection:
			try:
				return bool(self.cursor.execute("""SELECT alarm_bool FROM alarms WHERE alarm_type = ?;""", (alarm_type,)).fetchone()[0])
			except sqlite3.ProgrammingError:
				return None

	def set_alarm_value(self, alarm_type, alarm_value):
		with self.connection:
			try:
				self.cursor.execute("""UPDATE alarms SET alarm_bool = ? WHERE alarm_type = ?;""", (alarm_value, alarm_type,))
			except sqlite3.OperationalError:
				pass

	def is_correct_login(self, login, password):
		with self.connection:
			return bool(len(self.cursor.execute("""SELECT * FROM web_users WHERE login = ? AND password = ?""", (login, password,)).fetchall()))

	def change_user_password_by_user_id(self, user_id, user_password):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET password = ? WHERE id = ?;""", (user_password, user_id,))

	def get_user_password_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT password FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def get_user_name_by_login(self, login, need_with_conn=True):
		quare = """SELECT last_name, first_name, middle_name, mail, phone FROM web_users WHERE login = ?"""
		if need_with_conn:
			with self.connection:
				return self.cursor.execute(quare, (login,)).fetchone()
		else:
			return self.cursor.execute(quare, (login,)).fetchone()

	def get_all_logins(self):
		with self.connection:
			return list(map(lambda t: t[0], self.cursor.execute("""SELECT login FROM web_users;""").fetchall()))

	def update_user_data_by_user_id(self, user_id, login, password, last_name, first_name, middle_name, mail, phone):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET login = ?, password = ?, first_name = ?, last_name = ?, middle_name = ?, mail = ?, phone = ? WHERE id = ?""", (login, password, first_name, last_name, middle_name, mail, phone, user_id,))

	def update_user_uid_by_user_id(self, user_id, uid):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET uid = NULL WHERE uid = ?""", (uid,))
			self.cursor.execute("""UPDATE web_users SET uid = ? WHERE id = ?""", (uid, user_id,))

	def add_user_data(self, user_type, login, password, last_name, first_name, middle_name, mail, phone, user_secret):
		with self.connection:
			self.cursor.execute("""INSERT INTO web_users (user_type, login, password, first_name, last_name, middle_name, mail, phone, user_secret, is_2fa_enabled) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);""", (user_type, login, password, first_name, last_name, middle_name, mail, phone, user_secret, 0))

	def delete_user_by_user_id(self, user_id):
		with self.connection:
			self.cursor.execute("""DELETE FROM web_users WHERE id = ?;""", (user_id,))

	def get_all_user_ids(self):
		with self.connection:
			return list(map(lambda t: t[0], self.cursor.execute("""SELECT id FROM web_users;""").fetchall()))

	def get_user_type_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT user_type FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def get_user_type_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT user_type FROM web_users WHERE id = ?""", (user_id,)).fetchone()[0]

	def get_user_id_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT id FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def get_login_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT login FROM web_users WHERE id = ?""", (user_id,)).fetchone()[0]

	def get_user_email_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT mail FROM web_users WHERE id = ?""", (user_id,)).fetchone()[0]

	def get_user_secret_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT user_secret FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def get_user_id_by_email(self, email):
		with self.connection:
			ret = self.cursor.execute("""SELECT id FROM web_users WHERE mail = ?""", (email,)).fetchone()
			return ret[0] if ret is not None else None

	def get_is_2fa_enabled_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT is_2fa_enabled FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def set_is_2fa_enabled(self, user_secret, is_2fa_enabled):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET is_2fa_enabled = ? WHERE user_secret = ?;""", (is_2fa_enabled, user_secret,))

	def set_is_2fa_enabled_by_user_id(self, user_id, is_2fa_enabled):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET is_2fa_enabled = ? WHERE id = ?;""", (is_2fa_enabled, user_id,))

	def set_2fa_recovery_code_by_user_id(self, user_id, _2fa_recovery_code):
		with self.connection:
			self.cursor.execute("""UPDATE web_users SET recovery_code = ? WHERE id = ?;""", (_2fa_recovery_code, user_id,))

	def get_2fa_recovery_code_by_login(self, login):
		with self.connection:
			return self.cursor.execute("""SELECT recovery_code FROM web_users WHERE login = ?""", (login,)).fetchone()[0]

	def get_2fa_recovery_code_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT recovery_code FROM web_users WHERE id = ?""", (user_id,)).fetchone()[0]

	def get_users_data_by_user_type(self, user_type):
		with self.connection:
			return self.cursor.execute("""SELECT web_users.id, web_users.last_name, web_users.first_name, web_users.middle_name, web_users.mail, web_users.phone, web_users.uid,
											classes_data.class_number, classes_data.class_letter FROM web_users
											LEFT JOIN classes ON web_users.id = classes.user_id
											LEFT JOIN classes_data ON classes.class_id = classes_data.id
											WHERE user_type = ?""", (user_type,)).fetchall()

	def get_user_data_by_user_id(self, user_id: int):
		with self.connection:
			return self.cursor.execute("""SELECT web_users.id, web_users.last_name, web_users.first_name, web_users.middle_name, web_users.mail, web_users.phone, web_users.uid,
											classes_data.class_number, classes_data.class_letter FROM web_users
											LEFT JOIN classes ON web_users.id = classes.user_id
											LEFT JOIN classes_data ON classes.class_id = classes_data.id
											WHERE web_users.id = ?""", (user_id,)).fetchone()

	def get_mails_except_user_id(self, user_id=None):
		with self.connection:
			return list(map(lambda t: t[0], self.cursor.execute("""SELECT mail FROM web_users WHERE NOT id = ?""", (user_id,)).fetchall()))

	def get_user_lessons_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT id FROM lessons WHERE teacher_id = ?;""", (user_id,)).fetchall()

	def get_lessons_by_class_id(self, class_id):
		with self.connection:
			return self.cursor.execute("""SELECT DISTINCT lesson_id FROM schedule WHERE class_id = ?;""", (class_id,)).fetchall()

	def get_lesson_name_by_lesson_id(self, lesson_id, need_with_conn=True):
		if need_with_conn:
			with self.connection:
				return self.cursor.execute("""SELECT lesson_name FROM lessons WHERE id = ?;""", (lesson_id,)).fetchone()[0]
		else:
			return self.cursor.execute("""SELECT lesson_name FROM lessons WHERE id = ?;""", (lesson_id,)).fetchone()[0]

	def get_lesson_index_by_lesson_id_weekday(self, lesson_id, weekday):
		with self.connection:
			ret = list(map(lambda t: t[1], sorted(self.cursor.execute("""SELECT id, lesson_id FROM schedule WHERE week_day_index = ?;""", (weekday,)).fetchall(), key=lambda t: t[0])))
			return ret.index(lesson_id)

	def get_class_id_by_user_id(self, user_id):
		with self.connection:
			return self.cursor.execute("""SELECT class_id FROM classes WHERE user_id = ?;""", (user_id,)).fetchone()[0]

	def get_all_students_by_class_id(self, class_id):
		with self.connection:
			return list(map(lambda t: t[0], self.cursor.execute("""SELECT user_id FROM classes WHERE class_id = ?;""", (class_id,)).fetchall()))

	def get_schedule_by_class_id(self, class_id):
		lessons = list(map(lambda t: t[0], self.get_lessons_by_class_id(class_id)))
		with self.connection:
			ret = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(), 5: list(), 6: list()}
			for lesson_id in lessons:
				lessons_in_schedule = self.cursor.execute("""SELECT schedule.class_id, schedule.week_day_index, schedule.lesson_time__start, schedule.lesson_time__end,
															 web_users.first_name, web_users.last_name, web_users.middle_name FROM schedule
															 JOIN lessons ON schedule.lesson_id = lessons.id
															 JOIN web_users ON lessons.teacher_id = web_users.id
															 WHERE lesson_id = ?;""", (lesson_id,)).fetchall()
				for lesson_in_schedule in lessons_in_schedule:
					ret[lesson_in_schedule[1]].append([lesson_id, self.get_lesson_name_by_lesson_id(lesson_id, False), lesson_in_schedule[0], lesson_in_schedule[2], lesson_in_schedule[3], lesson_in_schedule[4:7]])
					ret[lesson_in_schedule[1]] = sorted(ret[lesson_in_schedule[1]], key=lambda t: datetime_strftime(t[3]))
			new_ret = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(), 5: list(), 6: list()}
			for i in ret.items():
				modified_list = list()
				for j in i[1]:
					modified_list.append({"lesson_id": j[0], "lesson_name": j[1], "class_id": j[2], "lesson_time__start": datetime_strftime(j[3]), "lesson_time__end": datetime_strftime(j[4]), "theacher_name": f"{j[5][0]} {j[5][1]} {j[5][2]}"})
				new_ret[i[0]] = modified_list
		return new_ret

	def get_teacher_schedule_by_user_id(self, user_id):
		user_lessons = list(map(lambda t: t[0], self.get_user_lessons_by_user_id(user_id)))
		with self.connection:
			ret = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(), 5: list(), 6: list()}
			for lesson_id in user_lessons:
				lessons_in_schedule = self.cursor.execute("""SELECT class_id, week_day_index, lesson_time__start, lesson_time__end FROM schedule WHERE lesson_id = ?;""", (lesson_id,)).fetchall()
				for lesson_in_schedule in lessons_in_schedule:
					ret[lesson_in_schedule[1]].append([lesson_id, self.get_lesson_name_by_lesson_id(lesson_id, False), lesson_in_schedule[0], lesson_in_schedule[2], lesson_in_schedule[3]])
			for i, j in ret.items():
				ret[i] = sorted(ret[i], key=lambda t: datetime_strftime(t[3]))
			new_ret = {0: list(), 1: list(), 2: list(), 3: list(), 4: list(), 5: list(), 6: list()}
			for i in ret.items():
				modified_list = list()
				for j in i[1]:
					modified_list.append({"lesson_id": j[0], "lesson_name": j[1], "class_id": j[2], "lesson_time__start": datetime_strftime(j[3]), "lesson_time__end": datetime_strftime(j[4])})
				new_ret[i[0]] = modified_list
		return new_ret

	def get_students_marks_by_lesson_id_class_id_lesson_date(self, lesson_id, class_id, lesson_date):
		with self.connection:
			students_in_class = list(map(lambda t: t[0], self.cursor.execute("""SELECT user_id FROM classes WHERE class_id = ?;""", (class_id,))))

			ret_marks = list()

			lesson_date = datetime.datetime.strptime(lesson_date, "%Y-%m-%d")
			first_month_day = datetime.datetime.strptime(f"01-{'0' + str(lesson_date.month) if len(str(lesson_date.month)) == 1 else lesson_date.month}-{lesson_date.year}", "%d-%m-%Y")
			days_in_month = calendar.monthrange(lesson_date.year, lesson_date.month)[1]
			for user_id in students_in_class:
				marks = list()
				for j in range(days_in_month):
					date = first_month_day + relativedelta(days=j)
					if not check_day_on_holiday(date, self.get_lesson_days_from_schedule_by_lesson_id(lesson_id, need_with_conn=False)):
						continue
					mark = self.cursor.execute("""SELECT mark FROM marks WHERE lesson_id = ? AND lesson_date = ? AND user_id = ?;""", (lesson_id, date.strftime("%Y-%m-%d"), user_id,)).fetchone()
					marks.append("A" if mark is None else mark[0])
				user_data = self.get_user_name_by_login(self.get_login_by_user_id(user_id), False)
				user_avatar_path = f"/static/user-avatars/{user_id}.png"
				ret_marks.append({"name": " ".join(user_data[:3]), "id": user_id, "user_avatar_path": (user_avatar_path if os.path.exists("." + user_avatar_path) else "/static/img/user-avatar.png"), "marks": marks})
			return ret_marks

	def get_lesson_id_class_id_by_user_id(self, user_id):
		class_id = self.get_class_id_by_user_id(user_id)
		now = (datetime.datetime.now() + relativedelta(hours=TZ_OFFSET()))
		now_time = datetime.datetime.strptime(f"{now.hour}:{now.minute}:{now.second}", "%H:%M:%S")
		with self.connection:
			lessons = list(filter(lambda t: datetime.datetime.strptime(t[2], "%H:%M:%S") > now_time,
			                      self.cursor.execute("""SELECT lesson_id, lesson_time__start, lesson_time__end FROM schedule WHERE week_day_index = ? AND class_id = ?;""", (now.weekday(), class_id,)).fetchall()))
			if len(lessons) != 0:
				lesson_id = min(lessons, key=lambda t: t[1])[0]
			else:
				lesson_id = None
			return lesson_id, class_id

	def get_lesson_time_by_lesson_id_lesson_date_class_id(self, lesson_id, lesson_date, class_id):
		week_day_index = datetime.datetime.strptime(lesson_date, "%Y-%m-%d").weekday()
		with self.connection:
			return self.cursor.execute("""SELECT lesson_time__start, lesson_time__end FROM schedule WHERE week_day_index = ? AND lesson_id = ? AND class_id = ?;""", (week_day_index, lesson_id, class_id,)).fetchone()

	def get_previous_lesson_id_by_lesson_id_lesson_date_class_id(self, lesson_id, lesson_date, class_id):
		now_lesson = self.get_lesson_time_by_lesson_id_lesson_date_class_id(lesson_id, lesson_date, class_id)
		week_day_index = datetime.datetime.strptime(lesson_date, "%Y-%m-%d").weekday()
		lesson_time__start = now_lesson[0]
		with self.connection:
			previous_lesson = self.cursor.execute("""SELECT lesson_id, lesson_time__start FROM schedule WHERE week_day_index = ? AND class_id = ? AND lesson_time__start < ?;""", (week_day_index, class_id, lesson_time__start)).fetchall()
			if previous_lesson != list():
				return max(previous_lesson, key=lambda t: t[1])[0]
			return None

	def get_student_mark_by_lesson_id_user_id_lesson_date(self, lesson_id, user_id, lesson_date):
		with self.connection:
			mark = self.cursor.execute("""SELECT mark FROM marks WHERE lesson_id = ? AND lesson_date = ? AND user_id = ?;""", (lesson_id, lesson_date, user_id,)).fetchone()
			if mark is None:
				mark = ("A",)
			return mark[0]

	def set_student_mark_by_lesson_id_lesson_date_user_id(self, lesson_id, lesson_date, user_id, mark):
		with self.connection:
			try:
				self.cursor.execute("""INSERT INTO marks (lesson_id, lesson_date, user_id, mark, check_col) VALUES (?, ?, ?, ?, ?);""", (lesson_id, lesson_date, user_id, mark, f"{lesson_id}__{lesson_date}__{user_id}",))
			except sqlite3.OperationalError:
				pass

	def get_lesson_days_from_schedule_by_lesson_id(self, lesson_id, need_with_conn=True):
		if need_with_conn:
			with self.connection:
				return list(map(lambda t: t[0], self.cursor.execute("""SELECT week_day_index FROM schedule WHERE lesson_id = ?;""", (lesson_id,)).fetchall()))
		else:
			return list(map(lambda t: t[0], self.cursor.execute("""SELECT week_day_index FROM schedule WHERE lesson_id = ?;""", (lesson_id,)).fetchall()))

	def set_recovery_code(self, user_id, recovery_code):
		with self.connection:
			self.cursor.execute("""INSERT INTO recovery_codes (user_id, verify_code) VALUES (?, ?);""", (user_id, recovery_code,))

	def get_recovery_code_by_user_id(self, user_id):
		with self.connection:
			verify_code = self.cursor.execute("""SELECT verify_code FROM recovery_codes WHERE user_id = ?;""", (user_id,)).fetchone()
			return verify_code[0] if verify_code is not None else None

	def remove_recovery_code_by_user_id(self, user_id):
		with self.connection:
			self.cursor.execute("""DELETE FROM recovery_codes WHERE user_id = ?;""", (user_id,))

	def get_all_classes_data(self):
		with self.connection:
			grades = sorted(list(set(map(lambda t: t[0], self.cursor.execute("""SELECT class_number FROM classes_data;""").fetchall()))), key=int)
			ret = list()
			for class_number in grades:
				classes = list()
				for _class in sorted(self.cursor.execute("""SELECT class_letter, id FROM classes_data WHERE class_number = ?;""", (class_number,)).fetchall(), key=lambda t: t[0]):
					classes.append({"class_letter": _class[0], "students_in_class": len(self.cursor.execute("""SELECT * FROM classes WHERE class_id = ?;""", (_class[1],)).fetchall()), "class_id": _class[1]})
				ret.append([class_number, sorted(classes, key=lambda t: t["class_letter"])])
			return ret

	def add_new_class_data(self, grade, class_letter):
		with self.connection:
			self.cursor.execute("""INSERT INTO classes_data (class_number, class_letter, checker) VALUES (?, ?, ?);""", (grade, class_letter, f"{grade}_{class_letter}",))

	def remove_class_data(self, class_id):
		with self.connection:
			self.cursor.execute("""DELETE FROM classes_data WHERE id = ?;""", (class_id,))

	def get_class_name_by_class_id(self, class_id):
		with self.connection:
			return "".join(list(map(str, self.cursor.execute("""SELECT class_number, class_letter FROM classes_data WHERE id = ?;""", (class_id,)).fetchone())))

	def remove_lessons_from_schedule_by_class_id(self, class_id):
		with self.connection:
			self.cursor.execute("""DELETE FROM schedule WHERE class_id = ?;""", (class_id,))

	def add_new_lesson_in_schedule(self, class_id, lesson_id, week_day_index, lesson_time__start, lesson_time__end):
		with self.connection:
			self.cursor.execute("""INSERT INTO schedule (class_id, lesson_id, week_day_index, lesson_time__start, lesson_time__end) VALUES (?, ?, ?, ?, ?);""", (class_id, lesson_id, week_day_index, lesson_time__start, lesson_time__end,))

	def add_new_lesson_in_lessons_by_teacher_id(self, teacher_id, lesson_name):
		with self.connection:
			return self.cursor.execute("""INSERT INTO lessons (teacher_id, lesson_name, checker) VALUES (?, ?, ?);""", (teacher_id, lesson_name, f"{teacher_id}__{lesson_name}")).lastrowid

	def get_all_lessons(self):
		with self.connection:
			return list(map(lambda t: [t[0], t[1], f"{t[2]} {t[3]} {t[4]}"],
							self.cursor.execute("""SELECT lessons.id, lessons.lesson_name, web_users.first_name, web_users.last_name, web_users.middle_name FROM lessons
													JOIN web_users ON lessons.teacher_id = web_users.id;""").fetchall()))

	def get_all_teachers(self):
		with self.connection:
			return list(map(lambda t: [t[0], f"{t[1]} {t[2]} {t[3]}"], self.cursor.execute("""SELECT id, first_name, last_name, middle_name FROM web_users WHERE user_type = ?;""", (1,)).fetchall()))

	def remove_lesson_by_lesson_id(self, lesson_id):
		with self.connection:
			self.cursor.execute("""DELETE FROM lessons WHERE id = ?;""", (lesson_id,))

	def get_can_students_leave_by_lesson_id(self, lesson_id):
		with self.connection:
			ret = self.cursor.execute("""SELECT can_students_leave FROM lessons WHERE id = ?;""", (lesson_id,)).fetchone()
			return ret[0] if ret is not None else None

	def set_can_students_leave_by_lesson_id(self, lesson_id, can_students_leave):
		with self.connection:
			self.cursor.execute("""UPDATE lessons SET can_students_leave = ? WHERE id = ?;""", (can_students_leave, lesson_id,))

	def set_do_not_show_in_exits_table(self, user_exit_data, lesson_data, value=1):
		if user_exit_data is None:
			return None
		with self.connection:
			self.cursor.execute("""UPDATE history SET do_not_show_in_exits_table = ? WHERE date = ? AND user_id = ?;""", (value, user_exit_data[0], user_exit_data[2],))
		return lesson_data[1].strftime("%Y-%m-%d %H:%M:%S.%f"), "entry", user_exit_data[2]

	def get_exits_data(self, lesson_id, class_id, lesson_date):
		_lesson_date = datetime.datetime.strptime(lesson_date, "%Y-%m-%d")
		lesson_data = list(map(lambda t: datetime.datetime.strptime(t, "%H:%M:%S"), self.get_lesson_time_by_lesson_id_lesson_date_class_id(lesson_id, lesson_date, class_id)))
		students = self.get_all_students_by_class_id(class_id)
		print(students)
		print(list(map(lambda t: (t[0], t[1]) if (t[1] is not None) else ((t[0], None) if datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%H:%M:%S"), "%H:%M:%S") < lesson_data[1]
		                                                                  else (t[0], self.set_do_not_show_in_exits_table(t[0], lesson_data))),
		               [self.get_last_user_id__exit_entry_by_day(t, _lesson_date.strftime("%d.%m.%Y")) for t in students])))
		students_exits = list(filter(lambda t: t[0] is not None,
		                             map(lambda t: (t[0], t[1]) if (t[1] is not None) else ((t[0], None) if datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%H:%M:%S"), "%H:%M:%S") < lesson_data[1]
		                                                                                    else (t[0], self.set_do_not_show_in_exits_table(t[0], lesson_data))),
		                                 [self.get_last_user_id__exit_entry_by_day(t, _lesson_date.strftime("%d.%m.%Y")) for t in students])))
		print(students_exits)

		filtered_exits = list(filter(lambda t: lesson_data[0] < datetime.datetime.strptime(t[0][0].split(" ")[1], "%H:%M:%S.%f") < lesson_data[1], students_exits))
		filtered_exits = list(map(lambda t: {"exit_date": (datetime.datetime.strptime(t[0][0], "%Y-%m-%d %H:%M:%S.%f") - relativedelta(seconds=0)).strftime("%H:%M:%S"),
		                                     "entry_date": ((datetime.datetime.strptime(t[1][0], "%Y-%m-%d %H:%M:%S.%f") - relativedelta(seconds=0)).strftime("%H:%M:%S") if t[1] is not None else ""),
		                                     "event": "exit" if t[1] is None else "entry", "user_id": t[0][2],
		                                     "user_name": " ".join(self.get_user_data_by_user_id(t[0][2])[1:3])}, filtered_exits))
		return sorted(filtered_exits, key=lambda t: (int(t["event"] == "entry"),
		                                             -((datetime.datetime.strptime(t["entry_date"], "%H:%M:%S") if t["entry_date"] != ""
		                                                else datetime.datetime.strptime((datetime.datetime.now() + relativedelta(hours=TZ_OFFSET())).strftime("%H:%M:%S"), "%H:%M:%S")) - datetime.datetime.strptime(t["exit_date"], "%H:%M:%S"))))

	def close_connection(self):
		self.connection.close()


if __name__ == '__main__':
	db = Database("./static/db.db")
	print(datetime_strftime(datetime.datetime.now().strftime("%H:%M:%S")))
	# print(db.get_exits_data(4, 1, "2023-02-19"))
