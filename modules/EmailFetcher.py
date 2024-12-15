import os
import poplib
import base64
import re
import importlib
from email import parser
from email.message import EmailMessage
from dotenv import load_dotenv
from modules.Database import ExposeDB
from modules.Expose import Expose
from modules.BaseExposeProcessor import BaseExposeProcessor

class EmailFetcher:
    def __init__(self, db=None):
        load_dotenv()
        self.db = db if db else ExposeDB()

        # Decoded email credentials
        self.email_user = base64.b64decode(os.getenv("EMAIL_USER")).decode("utf-8")
        self.email_password = base64.b64decode(os.getenv("EMAIL_PASSWORD")).decode("utf-8")
        self.pop3_server = "pop3s.aruba.it"
        self.pop3_port = 995
        # Control Features
        self.delete_emails_after_processing = False
        # Debugging
        self.debug = False
        # Load processors dynamically
        self.processors = self.load_processors()
        # Filter Keywords
        self.subject_filter = [keyword.strip() for keyword in os.getenv("SUBJECT_FILTER", "").split(",")]

    def set_debug(self, debug):
        self.debug = debug
        self._debug_log(f"Debug mode set to {self.debug}")

    def _debug_log(self, message):
        if self.debug:
            print(message)
            
    def load_processors(self):
        processors = {}
        modules_dir = "modules"
        for module_name in os.listdir(modules_dir):
            if module_name.endswith("_processor.py"):
                module = importlib.import_module(f"{modules_dir}.{module_name[:-3]}")
                for attr in dir(module):
                    processor_class = getattr(module, attr)
                    if isinstance(processor_class, type) and issubclass(processor_class, BaseExposeProcessor) and processor_class is not BaseExposeProcessor:
                        instance = processor_class(
                            name=processor_class.name,
                            domain=processor_class.domain,
                        )
                        processors[instance.get_domain()] = instance
        return processors

    def get_email_body(self, email_message: EmailMessage):
        """Extract the body of the email in plain text."""
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    return part.get_payload(decode=True).decode("utf-8", errors="ignore")
        else:
            return email_message.get_payload(decode=True).decode("utf-8", errors="ignore")
        return None

    def fetch_emails(self):
        try:
            mailbox = poplib.POP3_SSL(self.pop3_server, self.pop3_port)
            mailbox.user(self.email_user)
            mailbox.pass_(self.email_password)

            num_messages = len(mailbox.list()[1])
            self._debug_log(f"Found {num_messages} emails.")

            if num_messages > 0:
                for i in range(num_messages):
                    raw_email = b"\n".join(mailbox.retr(i+1)[1])
                    email_message = parser.Parser().parsestr(raw_email.decode("utf-8"))

                    subject = email_message["Subject"]
                    sender = email_message["From"]

                    body = self.get_email_body(email_message)
                    if body:
                        for domain, processor in self.processors.items():
                            if domain in sender:
                                expose_ids = processor.extract_expose_link(subject, body)
                                if expose_ids:
                                    for expose_id in expose_ids:
                                        if not self.db.expose_exists(expose_id):
                                            new_expose = Expose(
                                                expose_id=expose_id, 
                                                source=processor.get_name()
                                            )
                                            self.db.insert_expose(new_expose)
                                            self._debug_log(f"Inserted expose {expose_id} into the database with source '{processor.get_name()}'.")
                                        else:
                                            self._debug_log(f"Expose {expose_id} already exists.")
                                    if self.delete_emails_after_processing:
                                        mailbox.dele(i+1)
                                        self._debug_log(f"Deleted email with subject: {subject}")
                                break
                    else:
                        self._debug_log(f"Email with subject '{subject}' has no readable body.")

            mailbox.quit()

        except Exception as e:
            self._debug_log(f"Error: {str(e)}")
