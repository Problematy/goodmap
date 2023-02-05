from .templates.report_location_template import report_location_email_template

class EmailService:
    def __init__(self, config, sendmail):
        self.config = config
        self.__send_email = sendmail

    def send_report_location_email(self, location_data):
        email_receiver = self.config["ADMIN_EMAIL"]
        subject = "Reported location"
        message_content = report_location_email_template(location_data)
        self.__send_email(email_receiver, subject, message_content)
