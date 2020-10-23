import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading


# object ready to send an email
# if password_mail is not included in configuration, used default configured in this file
class EmailSender:
    def __init__(self, configuration, logger):
        self.logger = logger
        self.configuration = configuration
        self.no_active = False
        try:
            # mandatory field to activate service
            configuration["user_mail"]
            configuration["destination_mail"]
        except KeyError:
            # no mandatory field, so, email not active
            self.no_active = True

    def send(self):
        if self.no_active:
            return

        # send message after 10 seconds, to be sure DNS is up
        timer = threading.Timer(10, self.__send__)
        timer.start()

    def __send__(self):
        msg = MIMEMultipart()
        msg["From"] = self.configuration["user_mail"]
        msg["To"] = self.configuration["destination_mail"]

        try:
            password = self.configuration["password_mail"]
        except KeyError:
            password = "gmail_appli_passwd"

        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        msg["Subject"] = 'report at ' + timestamp

        body = self.logger.get_current_log()
        if body:

            msg.attach(MIMEText(body, "plain"))

            text = msg.as_string()
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(msg["From"], password)

            server.sendmail(msg["From"], msg["To"], text)
            server.quit()
