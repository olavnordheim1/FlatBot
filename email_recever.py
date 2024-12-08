import os
import poplib
import base64
from email import parser
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Decoded email credentials
EMAIL_USER = base64.b64decode(os.getenv("EMAIL_USER")).decode("utf-8")
EMAIL_PASSWORD = base64.b64decode(os.getenv("EMAIL_PASSWORD")).decode("utf-8")
POP3_SERVER = "pop3s.aruba.it"
POP3_PORT = 995

def receive_emails():
    try:
        # Connect to the server
        mail = poplib.POP3_SSL(POP3_SERVER, POP3_PORT)
        mail.user(EMAIL_USER)
        mail.pass_(EMAIL_PASSWORD)

        # Get email stats
        num_messages = len(mail.list()[1])
        print(f"Found {num_messages} emails.")

        if num_messages > 0:
            # Loop through all messages
            for i in range(1, num_messages + 1):
                response, messages, octets = mail.retr(i)
                email_content = b"\n".join(messages).decode("utf-8")
                email_message = parser.Parser().parsestr(email_content)

                # Print email details
                print(f"From: {email_message['from']}")
                print(f"Subject: {email_message['subject']}")

                # Extract and print content
                if email_message.is_multipart():
                    for part in email_message.walk():
                        content_type = part.get_content_type()
                        if content_type == "text/plain":
                            print("Body:", part.get_payload(decode=True).decode("utf-8"))
                else:
                    print("Body:", email_message.get_payload(decode=True).decode("utf-8"))

                # Delete email after processing
                mail.dele(i)
                print(f"Email {i} deleted.\n")

        # Close the connection
        mail.quit()

    except Exception as e:
        print("Error:", str(e))


if __name__ == "__main__":
    receive_emails()
