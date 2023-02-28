from dateutil.relativedelta import relativedelta
import random


APP_NAME = "ACS for schools"
HOST = "192.168.8.100"
DB_NAME = "static/db.db"

PORT = 5002
SOCKET_SERVER_PORT = 5001

HISTORY_SHOW_LIMIT = relativedelta(months=1)
# HISTORY_SHOW_LIMIT = relativedelta(years=5)
ROUND_PERCENT = 0

USE_HOLIDAYS = False
WEEK_DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
def RANDOM_2FA_RECOVERY_CODE(): return "R" + str(random.randint(10000, 99999))


RESENT_EMAIL_COOLDOWN = 31
REDIRECT_AFTER_DELETE_ACCOUNT_TIME = 1500


USE_YANDEX_EMAIL = False
YANDEX_PASSWORD = "qgnalwksrztgwtyx"
SENDINBLUE_API_TOKEN = "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"
NOREPLY_EMAIL = "no-reply@robotics-acs-project.tk"
LOGIN_EMAIL = "login@robotics-acs-project.tk"

# LESSONS_TIME = [["08:30", "09:10"], ["09:25", "10:05"], ["10:25", "11:05"], ["11:25", "12:05"], ["12:15", "12:55"], ["13:15", "13:55"], ["14:15", "14:55"], ["15:05", "15:45"]]
