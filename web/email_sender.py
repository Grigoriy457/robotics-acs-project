import datetime
import smtplib
import ssl
import zoneinfo
from email import encoders
from email.utils import formataddr
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

import base64

import config

from_email = "grigori.p.vlasov@yandex.ru"
to_email = "grigori.p.vlasov@gmail.com"

message = MIMEMultipart("alternative")
message["Subject"] = "multipart test"
message["From"] = from_email
message["To"] = to_email


def sender(msg, html_template, send_to, is_login_msg=False):
	print("Sending...")
	if config.USE_YANDEX_EMAIL:
		with smtplib.SMTP_SSL("smtp.yandex.ru", 465, context=ssl.create_default_context()) as server:
			server.login(from_email, config.YANDEX_PASSWORD)

			msg["From"] = formataddr(("Acs For Schools", from_email))
			server.sendmail(from_email, send_to, msg.as_string())
			print("Message was sent successfully!")
	else:
		configuration = sib_api_v3_sdk.Configuration()
		configuration.api_key['api-key'] = config.SENDINBLUE_API_TOKEN

		api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
		send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
			sender={"name": "Acs For Schools", "email": config.NOREPLY_EMAIL if not is_login_msg else config.LOGIN_EMAIL},
			to=[{"email": send_to}], html_content=html_template, subject=msg["Subject"])

		try:
			api_instance.send_transac_email(send_smtp_email)
			print("Message was sent successfully!")
		except ApiException as e:
			print("Exception when calling SMTPApi->send_transact_email: %s\n" % e)


def send_recovery_code(send_to, recovery_code):
	with open("./templates/email_templates/email_recovery_code_template.html", mode="r", encoding="utf-8") as file:
		template = file.read()

	msg = MIMEMultipart()
	html_template = template.replace("{{ verify_code }}", str(recovery_code))
	msg.attach(MIMEText(html_template, "html"))
	with open("./static/img/logo.png", "rb") as logo:
		part = MIMEBase("application", "octet-stream")
		part.set_payload(logo.read())
		encoders.encode_base64(part)
		part.add_header('Content-ID', '<logo>')
		part.add_header(
			"Content-Disposition",
			f"attachment; filename=logo.png",
		)
		msg.attach(part)
	# html_template = f"<h1>Your recovery code is: {recovery_code}</h1>"
	msg["To"] = send_to
	msg["Subject"] = "Verify code"
	sender(msg, html_template, send_to)


def send_user_data(send_to, login, new_password):
	html_template = f"<h1>Your login is: {login}<br>Your new password is: {new_password}</h1>"
	msg = MIMEText(html_template, "html")
	msg["To"] = send_to
	msg["Subject"] = "New password"
	sender(msg, html_template, send_to)


def new_login(send_to, entry_time: datetime.datetime, device, browser, version, ip_address):
	html_template = f"""<h1>Dear user!</h1>
						<p>We have detected that you are signed in from a new device.<br>
						Entry time: <b>{entry_time.strftime("%b %d %Y %H:%M:%S %Z")}</b><br>
						Device: <b>{device}</b><br>
						Browser: <b>{browser}</b><br>
						IP address: <b>{ip_address}</b></p>"""
	msg = MIMEText(html_template, "html")
	msg["To"] = send_to
	msg["Subject"] = "Entry warning"
	sender(msg, html_template, send_to, is_login_msg=True)


if __name__ == "__main__":
	new_login("grigori.p.vlasov@gmail.com", datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Moscow")), "", "", "", "")
	# send_recovery_code("grigori.p.vlasov@gmail.com", "123456")
