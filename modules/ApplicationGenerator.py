import os
import logging
from datetime import datetime
from modules.Expose import Expose
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ApplicationGenerator:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        self.template_path = os.getenv("TEMPLATE_FILENAME")
        self.fallback_text = os.getenv("FALLBACK_TEXT")
        self.applicant_data = {
            "first_name": os.getenv("APPLICANT_NAME"),
            "surname": os.getenv("APPLICANT_SURNAME"),
            "birthdate": os.getenv("APPLICANT_BIRTHDATE"),
            "address": os.getenv("APPLICANT_ADDRESS"),
            "post_code": os.getenv("APPLICANT_POST_CODE"),
            "city": os.getenv("APPLICANT_CITY"),
            "neighborhood": os.getenv("APPLICANT_NEIGHBORHOOD"),
            "job_status": os.getenv("APPLICANT_JOB_STATUS"),
            "job_title": os.getenv("APPLICANT_JOB"),
            "company": os.getenv("APPLICANT_COMPANY"),
            "net_income": os.getenv("APPLICANT_NET_INCOME_M"),
            "gender": os.getenv("APPLICANT_SEX"),
            "household_size": os.getenv("APPLICANT_HOUSEHOLD_SIZE"),
            "pets": os.getenv("APPLICANT_PETS"),
            "smoker": os.getenv("APPLICANT_SMOKE"),
            "marital_status": os.getenv("APPLICANT_MARRIED"),
            "age" : self._calculate_age(os.getenv("APPLICANT_BIRTHDATE")),
        }

    def get_applicant_attribute(self, attribute):
        return self.applicant_data.get(attribute, "Unknown")
    
    
    def generate_application(self, Expose):
        logger.info("Generating Application text")
        if Expose:
            text = self._fill_application_template(Expose)
            #TO-DO debug print("Generated Application Text \n")
            #TO-DO debug print(text)
        else:
            text = self.default_text
        logger.info(text)
        return text
    
    def _fill_application_template(self, Expose):
        #Loads the template file, fills in the placeholders, and returns the filled string.
        #:param kwargs: Key-value pairs to replace placeholders in the template.
        application_data = {
            "Landlord_Name": Expose.agent_name,
            "APPLICANT_NAME": self.applicant_data['first_name'],
            "APPLICANT_SURNAME": self.applicant_data['surname'],
            "Flat_Address": Expose.location,
            "APPLICANT_JOB": self.applicant_data['job_title'],
            "APPLICANT_COMPANY": self.applicant_data['company'],
            "APPLICANT_CITY": self.applicant_data['city'],
            "APPLICANT_NET_INCOME_M": self.applicant_data['net_income'],
            "APPLICANT_JOB_STATUS": self.applicant_data['job_status'],
            "APPLICANT_AGE": self._calculate_age(self.applicant_data['birthdate']),
        }
        try:
            if not os.path.exists(self.template_path):
                logger.error(f"Template file '{self.template_path}' not found.")

            with open(self.template_path, 'r', encoding='utf-8') as file:
                template_content = file.read()

            filled_content = template_content.format(**application_data)
            return filled_content
        except:
            return self.fallback_text


    def _calculate_age(self, birthdate):
        logger.debug(f"calculating age from {birthdate}")
        #Calculates age from a birthdate string in the format DD.MM.YYYY.
        birthdate = datetime.strptime(birthdate, "%d.%m.%Y")
        today = datetime.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        logger.info(f"Age is {age}")
        return age
