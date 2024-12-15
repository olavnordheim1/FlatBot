import os
from datetime import datetime
from dotenv import load_dotenv

class Expose:
    def __init__(self, expose_id, source=None, title=None, price_kalt=None, price_warm=None, nebekosten=None, 
                 location=None, square_meters=None, number_of_rooms=None, agent_name=None, 
                 real_estate_agency=None, energetic_rating=None, construction_year=None, description=None, 
                 neighborhood=None, processed=0, failures=0, received_at=None):
        self.expose_id = expose_id
        self.source = source
        self.title = title
        self.price_kalt = price_kalt
        self.price_warm = price_warm
        self.nebekosten = nebekosten
        self.location = location
        self.square_meters = square_meters
        self.number_of_rooms = number_of_rooms
        self.agent_name = agent_name
        self.real_estate_agency = real_estate_agency
        self.energetic_rating = energetic_rating
        self.construction_year = construction_year
        self.description = description
        self.neighborhood = neighborhood
        self.processed = processed
        self.failures = failures
        self.received_at = received_at or datetime.utcnow()

    def update_field(self, field_name, value):
        if hasattr(self, field_name):
            setattr(self, field_name, value)
        else:
            raise AttributeError(f"Field '{field_name}' does not exist in Expose.")

    def get_field(self, field_name):
        if hasattr(self, field_name):
            return getattr(self, field_name)
        else:
            raise AttributeError(f"Field '{field_name}' does not exist in Expose.")

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        fields = ', '.join(f'{key}="{value}"' if isinstance(value, str) else f'{key}={value}' for key, value in self.to_dict().items() if value is not None)
        return f"<Expose {fields}>"
    
    def __eq__(self, other):
        if isinstance(other, Expose):
            return self.expose_id == other.expose_id
        return False
