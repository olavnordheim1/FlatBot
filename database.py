import sqlite3
import os
from datetime import datetime
from dotenv import load_dotenv

class Expose:
    def __init__(self, expose_id, source=None, title=None, price_kalt=None, price_warm=None, nebekosten=None, 
                 location=None, square_meters=None, number_of_rooms=None, agent_name=None, 
                 real_estate_agency=None, energetic_rating=None, construction_year=None, description=None, 
                 neighborhood=None, processed=0, failures=0, scraped_at=None):
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
        self.scraped_at = scraped_at or datetime.utcnow()

    def update_field(self, field_name, value):
        if hasattr(self, field_name):
            setattr(self, field_name, value)
        else:
            raise AttributeError(f"Field '{field_name}' does not exist in Expose.")

    def to_dict(self):
        return self.__dict__

    def __repr__(self):
        props = ', '.join(f'{key}={value}' for key, value in self.to_dict().items() if value is not None)
        return f"<Expose {props}>"

class ExposeDB:
    def __init__(self, db_file="flats.db", max_attempts=50):
        load_dotenv()
        self.db_file = os.getenv("DB_FILE", db_file)
        self.max_attempts_expose = int(os.getenv("MAX_ATTEMPTS_EXPOSE", max_attempts))
        self.init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_file)

    def init_db(self):
        fields = ', '.join(
            f"{key} {self._get_sql_type(value)}" for key, value in Expose().__dict__.items()
        )
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS exposes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, {fields}
            );
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            print("Database created and initialized.")
        self.create_indexes()

    def _get_sql_type(self, value):
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, str):
            return "TEXT"
        if isinstance(value, datetime):
            return "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        return "TEXT"

    def insert_expose(self, expose):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                fields = ', '.join(expose.to_dict().keys())
                placeholders = ', '.join(['?'] * len(expose.to_dict()))
                values = tuple(expose.to_dict().values())
                cursor.execute(f"""
                    INSERT INTO exposes ({fields})
                    VALUES ({placeholders})
                """, values)
                print(f"Expose {expose.expose_id} inserted successfully.")
            except sqlite3.IntegrityError:
                print(f"Expose {expose.expose_id} already exists in the database.")

    def update_expose(self, expose):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join(f"{key}=?" for key in expose.to_dict().keys())
            values = tuple(expose.to_dict().values()) + (expose.expose_id,)
            cursor.execute(f"""
                UPDATE exposes SET {fields} WHERE expose_id=?
            """, values)
            print(f"Expose {expose.expose_id} updated successfully.")

    def get_expose(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM exposes WHERE expose_id=?
            """, (expose_id,))
            row = cursor.fetchone()
            if row:
                return Expose(*row[1:])
            return None

    def expose_exists(self, expose_id):
        return self.get_expose(expose_id) is not None

    def print_all_exposes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exposes")
            rows = cursor.fetchall()
            if rows:
                print("\n=== All Exposes in Database ===")
                for row in rows:
                    print(row)
                print("================================\n")
            else:
                print("No exposes found in the database.\n")

    def clear_exposes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exposes")
            conn.commit()
            print("All exposes have been deleted from the database.\n")

    def delete_expose_by_id(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exposes WHERE expose_id=?", (expose_id,))
            if cursor.rowcount:
                print(f"Expose {expose_id} deleted from the database.\n")
            else:
                print(f"Expose {expose_id} not found in the database.\n")
            conn.commit()

    def mark_expose_as_processed(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE exposes SET processed=1 WHERE expose_id=?
            """, (expose_id,))
            if cursor.rowcount:
                print(f"Expose {expose_id} marked as processed.\n")
            else:
                print(f"Expose {expose_id} not found in the database.\n")
            conn.commit()

    def get_unprocessed_exposes(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exposes WHERE processed=0 AND failures < ?", (self.max_attempts_expose,))
            rows = cursor.fetchall()
            return rows

    def increase_failures_count(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE exposes SET failures = failures + 1 WHERE expose_id=?
            """, (expose_id,))
            cursor.execute("""
                SELECT failures FROM exposes WHERE expose_id=?
            """, (expose_id,))
            result = cursor.fetchone()
            if result:
                failures_count = result[0]
                print(f"Failures count for expose {expose_id} increased to {failures_count}.")
                if failures_count >= self.max_attempts_expose:
                    cursor.execute("""
                        UPDATE exposes SET processed=1 WHERE expose_id=?
                    """, (expose_id,))
                    print(f"Expose {expose_id} marked as processed due to exceeding failures limit.\n")
            else:
                print(f"Expose {expose_id} not found in the database while attempting to record the failure.\n")
            conn.commit()
