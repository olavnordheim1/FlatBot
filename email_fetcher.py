import os
import poplib
import base64
import re
from email import parser
from email.message import EmailMessage
from dotenv import load_dotenv
from database import insert_expose, expose_exists

# Load environment variables
load_dotenv()

# Decoded email credentials
EMAIL_USER = base64.b64decode(os.getenv("EMAIL_USER")).decode("utf-8")
EMAIL_PASSWORD = base64.b64decode(os.getenv("EMAIL_PASSWORD")).decode("utf-8")
POP3_SERVER = "pop3s.aruba.it"
POP3_PORT = 995

# Control Features
DELETE_EMAILS_AFTER_PROCESSING = os.getenv("DELETE_EMAILS_AFTER_PROCESSING", "False").lower() == "true"

# Source Mapping
SENDER_SOURCE_MAPPING = {
    domain.strip(): source.strip() for domain, source in 
    (pair.split(":") for pair in os.getenv("SENDER_SOURCE_MAPPING", "").split(",") if ":" in pair)
}

# Filter Keywords
SUBJECT_FILTER = [keyword.strip() for keyword in os.getenv("SUBJECT_FILTER", "").split(",")]

def extract_expose_links_immobilienscout24(subject, email_body):
    """Extract unique expose links from the email body specific to Immobilienscout24."""
    pattern = re.compile(r"https:\/\/[a-zA-Z0-9./?=&_-]*expose/(\d+)")
    return list(set(pattern.findall(email_body)))

def get_email_body(email_message: EmailMessage):
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

def fetch_emails():
    try:
        mailbox = poplib.POP3_SSL(POP3_SERVER, POP3_PORT)
        mailbox.user(EMAIL_USER)
        mailbox.pass_(EMAIL_PASSWORD)

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
                if not any(keyword in subject_lower for keyword in SUBJECT_FILTER):
                    print(f"Email with subject '{subject}' does not match filter keywords.")
                    continue

                body = get_email_body(email_message)
                expose_ids = []
                if body:
                    source = next((value for domain, value in SENDER_SOURCE_MAPPING.items() if domain in sender), None)
                    if source:
                        function_name = f"extract_expose_links_{source}"
                        if function_name in globals():
                            expose_ids = globals()[function_name](subject, body)

                    if expose_ids:
                        for expose_id in expose_ids:
                            if not expose_exists(expose_id):
                                insert_expose(
                                    expose_id=expose_id, 
                                    source=source
                                )
                                print(f"Inserted expose {expose_id} into the database with source '{source}'.")
                            else:
                                print(f"Expose {expose_id} already exists.")
                    else:
                        print(f"Email with subject '{subject}' has no readable body.")
                else:
                    print(f"Email with subject '{subject}' has no readable body.")

                if DELETE_EMAILS_AFTER_PROCESSING:
                    mailbox.dele(i+1)
                    print(f"Deleted email with subject: {subject}")

        mailbox.quit()

    except Exception as e:
        print("Error:", str(e))
