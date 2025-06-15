import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import threading
import logging
from elements.format_email_body import *

mail_logger = logging.getLogger('email_sender')


# object ready to send an email
# if password_mail is not included in configuration, used default configured in this file
# logger used to get current log and rotate
class EmailSender:
    def __init__(self, configuration, logger):
        self.logger = logger
        self.configuration = configuration
        self.no_active = False
        self.csv_report = False

        try:
            # mandatory fields to activate service
            user = configuration["user_mail"]
            if len(user) == 0:
                raise KeyError
            destination = configuration["destination_mail"]
            if len(destination) == 0:
                raise KeyError
        except KeyError:
            # no mandatory fields, so, email not active
            mail_logger.info("service not active, no enough configuration")
            self.no_active = True

        try:
            self.csv_report = configuration['csv_report']
        except KeyError:
            # used text report by default
            pass

    def send_message(self, message, subject=None):
        if self.no_active:
            return
        self.__send__(message, subject)

    def send(self):
        """send current log
        """
        if self.no_active:
            return

        # send message after 10 seconds, to be sure DNS is up
        body = self.__make_log()
        timer = threading.Timer(10, self.__send__, args=(body))
        timer.start()

    def __send__(self, body=None, subject='report'):
        msg = MIMEMultipart()
        msg["From"] = self.configuration["user_mail"]
        msg["To"] = self.configuration["destination_mail"]

        try:
            password = self.configuration["password_mail"]
            if len(password) == 0:
                raise KeyError
        except KeyError:
            password = "gmail_appli_passwd"
        mail_logger.debug("ready to send with passwd : " + password)

        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        msg["Subject"] = f'{subject} at {timestamp}'

        if body:
            msg.attach(MIMEText(body, "plain"))

            text = msg.as_string()
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(msg["From"], password)

            server.sendmail(msg["From"], msg["To"], text)
            server.quit()

    def __make_log(self):
        body = self.logger.get_current_log()
        if body:
            body = format_data(body, self.csv_report)
        return body
