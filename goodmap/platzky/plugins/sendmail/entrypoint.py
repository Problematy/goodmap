import smtplib

from pydantic import BaseModel, Field


def send_mail(sender_email, password, smtp_server, port, receiver_email, subject, message):
    full_message = f"From: {sender_email}\nTo: {receiver_email}\nSubject: {subject}\n\n{message}"
    server = smtplib.SMTP_SSL(smtp_server, port)
    server.ehlo()
    server.login(sender_email, password)
    server.sendmail(sender_email, receiver_email, full_message)
    server.close()


class SendMailConfig(BaseModel):
    user: str = Field(alias="sender_email")
    password: str = Field(alias="password")
    server: str = Field(alias="smtp_server")
    port: int = Field(alias="port")
    receiver: str = Field(alias="receiver_email")
    subject: str = Field(alias="subject")


def process(app, config):
    plugin_config = SendMailConfig.parse_obj(config)

    def notify(message):
        send_mail(
            sender_email=plugin_config.user,
            password=plugin_config.password,
            smtp_server=plugin_config.server,
            port=plugin_config.port,
            receiver_email=plugin_config.receiver,
            subject=plugin_config.subject,
            message=message,
        )

    app.add_notifier(notify)
    return app
