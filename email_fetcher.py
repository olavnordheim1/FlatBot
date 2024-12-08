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
DELETE_EMAILS_AFTER_PROCESSING = False

def extract_expose_links(email_body):
    """Extract unique expose links from the email body."""
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
                body = get_email_body(email_message)

                if body:
                    expose_ids = extract_expose_links(body)

                    # Process expose IDs
                    for expose_id in expose_ids:
                        # Check if the expose already exists in the DB
                        if not expose_exists(expose_id):
                            data = (
                                expose_id,  # Expose ID
                                None,       # Title from email subject
                                None,       # Price Kalt
                                None,       # Price Warm
                                None,       # Location
                                None,       # Size
                                None,       # Number of Rooms
                                None,       # Agent Name
                                None,       # Real Estate Agency
                                None,       # Energetic Rating
                                None,       # Construction Year
                                None,       # Description
                                None,       # Neighborhood
                                0           # Processed (default)
                            )

                            insert_expose(data)
                            print(f"Inserted expose {expose_id} into the database.")
                        else:
                            print(f"Expose {expose_id} already exists.")
                    
                    if DELETE_EMAILS_AFTER_PROCESSING:
                        mailbox.dele(i+1)
                        print(f"Deleted email with subject: {subject}")
                else:
                    print(f"Email with subject '{subject}' has no readable body.")

        mailbox.quit()

    except Exception as e:
        print("Error:", str(e))
