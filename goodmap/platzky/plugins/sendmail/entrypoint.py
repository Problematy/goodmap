import smtplib

from pydantic import BaseModel, Field


def send_mail(sender_email, password, smtp_server, port, receiver_email, subject, message):
    full_message = f"From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{message}"
    server = smtplib.SMTP_SSL(smtp_server, port)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, full_message)
    server.close()


def process(app, plugin_config):
    def notify(message):
        send_mail(
            sender_email=plugin_config["USER"],
            password=plugin_config["PASSWORD"],
            smtp_server=plugin_config["SERVER"],
            port=plugin_config["PORT"],
            receiver_email=plugin_config["RECEIVER"],
            subject=plugin_config["SUBJECT"],
            message=message,
        )

    app.add_notifier(notify)
    return app


class SendMailPlugin(BaseModel):
    port: str = Field(alias="PORT")
    server: str = Field(alias="SERVER")
    user: str = Field(alias="USER")
    password: str = Field(alias="PASSWORD")
