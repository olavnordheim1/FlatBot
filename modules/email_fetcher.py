import os
import poplib
import base64
import re
from email import parser
from email.message import EmailMessage
from dotenv import load_dotenv
from database import ExposeDB, Expose

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
        self.delete_emails_after_processing = os.getenv("DELETE_EMAILS_AFTER_PROCESSING", "False").lower() == "true"

        # Source Mapping
        self.sender_source_mapping = {
            domain.strip(): source.strip() for domain, source in 
            (pair.split(":") for pair in os.getenv("SENDER_SOURCE_MAPPING", "").split(",") if ":" in pair)
        }

        # Filter Keywords
        self.subject_filter = [keyword.strip() for keyword in os.getenv("SUBJECT_FILTER", "").split(",")]

    def extract_expose_links_immobilienscout24(self, subject, email_body):
        """Extract unique expose links from the email body specific to Immobilienscout24."""
        pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
        return list(set(pattern.findall(email_body)))

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
            print(f"Found {num_messages} emails.")

            if num_messages > 0:
                for i in range(num_messages):
                    raw_email = b"\n".join(mailbox.retr(i+1)[1])
                    email_message = parser.Parser().parsestr(raw_email.decode("utf-8"))

                    subject = email_message["Subject"]
                    sender = email_message["From"]

                    # Check subject filter before processing
                    subject_lower = subject.lower()
                    if not any(keyword in subject_lower for keyword in self.subject_filter):
                        print(f"Email with subject '{subject}' does not match filter keywords.")
                        continue

                    body = self.get_email_body(email_message)
                    expose_ids = []
                    if body:
                        source = next((value for domain, value in self.sender_source_mapping.items() if domain in sender), None)
                        if source:
                            function_name = f"extract_expose_links_{source}"
                            if hasattr(self, function_name):
                                expose_ids = getattr(self, function_name)(subject, body)

                        if expose_ids:
                            for expose_id in expose_ids:
                                if not self.db.expose_exists(expose_id):
                                    new_expose = Expose(
                                        expose_id=expose_id, 
                                        source=source
                                    )
                                    self.db.insert_expose(new_expose)
                                    print(f"Inserted expose {expose_id} into the database with source '{source}'.")
                                else:
                                    print(f"Expose {expose_id} already exists.")
                            if self.delete_emails_after_processing:
                                mailbox.dele(i+1)
                                print(f"Deleted email with subject: {subject}")
                    else:
                        print(f"Email with subject '{subject}' has no readable body.")

            mailbox.quit()

        except Exception as e:
            print("Error:", str(e))
