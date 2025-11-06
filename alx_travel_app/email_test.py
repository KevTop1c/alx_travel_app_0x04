import smtplib
from email.mime.text import MIMEText

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = "kev.topic001@gmail.com"
EMAIL_HOST_PASSWORD = "ifzqtxxmyqnphyow"  # App password
TO_EMAIL = "kev.topic001@gmail.com"

msg = MIMEText("Hello! This is a test email from Python.")
msg["Subject"] = "SMTP Test"
msg["From"] = EMAIL_HOST_USER
msg["To"] = TO_EMAIL

server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
server.set_debuglevel(1)

try:
    print(">>> EHLO")
    server.ehlo()

    print(">>> STARTTLS")
    server.starttls()
    server.ehlo()

    print(">>> LOGIN")
    server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)

    print(">>> SEND MAIL")
    server.sendmail(EMAIL_HOST_USER, TO_EMAIL, msg.as_string())
    print("✅ Email sent successfully!")
except Exception as e: # pylint: disable=broad-exception-caught
    print("❌ Error:", e)
finally:
    server.quit()
