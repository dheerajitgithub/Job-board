"""Email utils"""

import logging
import smtplib
import os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from core.settings import logger
from core import settings

logger = logging.LoggerAdapter(logger, {"app_name": "core.utils.emails"})

def send_an_email(
    receiver_email,
    subject,
    body,
    host=None,
    port=None,
    sender_email=None,
    sender_password=None,
    connection=None,
    start_tls=False,
    cc=None,
    file_paths=None,
):
    try:
        if file_paths is None:
            file_paths = []
        # instance of MIMEMultipart
        msg = MIMEMultipart()
        msg["Subject"] = subject
        smtp_server = settings.SMTP_SERVER if not host else host
        smtp_port = settings.SMTP_PORT if not port else port
        smtp_connection = settings.SMTP_CONNECTION if not connection else connection
        msg["From"] = smtp_sender_email = settings.SMTP_SENDER_EMAIL if not sender_email else sender_email
        smtp_password = settings.SMTP_PASSWORD if not sender_password else sender_password
        logger.info(
            f"SMTP {smtp_server} {smtp_port} {smtp_sender_email} {smtp_password}"
        )
        # attach the body with the msg instance
        msg.attach(MIMEText(body, "html"))
        for file_path in file_paths:
            try:
                file_name = file_path.split("/")[-1]
                attachment = open(file_path, "rb")
                # instance of MIMEBase and named as p
                p = MIMEBase("application", "octet-stream")
                # To change the payload into encoded form
                p.set_payload((attachment).read())
                # encode into base64
                encoders.encode_base64(p)
                p.add_header("Content-Disposition", f"attachment; filename= {file_name}")
                # attach the instance 'p' to instance 'msg'
                msg.attach(p)
                os.remove(file_path)
            except Exception as e:
                logger.info(f"Attachment failed for path {file_path}", e)
        # creates SMTP session
        s = (smtplib.SMTP_SSL(smtp_server, smtp_port)
             if smtp_connection == "SSL"
             else smtplib.SMTP(smtp_server, smtp_port))

        logger.info(f"CONNECTION : {smtp_connection}")
        # start TLS for security
        if start_tls:
            s.starttls()
            logger.info("TLS STARTED")
        # Authentication
        s.login(smtp_sender_email, smtp_password)
        logger.info("LOGIN SUCCESS")
        # sending the mail
        final_to = ""
        for recepient in receiver_email:
            final_to += f"{recepient},"
        msg["To"] = final_to
        if cc:
            final_cc = ""
            for recepient in cc:
                final_cc  += f"{recepient},"
                receiver_email.append(recepient)
            msg["Cc"] = final_cc
        s.sendmail(from_addr=smtp_sender_email, to_addrs=receiver_email, msg=str(msg))
        logger.info("MAIL SENT :")
        # terminating the session
        s.quit()
        return True, "Success"
    except Exception as e:
        logger.info(f"EXCEPTION :{e}")
        return False, str(e)

