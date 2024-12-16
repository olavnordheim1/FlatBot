import os
from modules.Expose import Expose
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ApplicationGenerator:
    def __init__(self):
        self.default_text = os.getenv("DEFAULT_APPLICATION_TEXT")

    def generate_application(self, Expose):
        if Expose:
            pass
        return self.default_text
        