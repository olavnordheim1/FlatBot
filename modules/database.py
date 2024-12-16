import sqlite3
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from modules.Expose import Expose

logger = logging.getLogger(__name__)

class ExposeNotFoundError(Exception):
    pass

class ExposeUpdateError(Exception):
    pass

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
            f"{key} {self._get_sql_type(value)}" for key, value in Expose(expose_id=None).__dict__.items()
        )
        create_table_query = f"""
            CREATE TABLE IF NOT EXISTS exposes (
                id INTEGER PRIMARY KEY AUTOINCREMENT, {fields}
            );
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            logging.info("Database created and initialized.")

    def _get_sql_type(self, value):
        if isinstance(value, int):
            return "INTEGER"
        if isinstance(value, str):
            return "TEXT"
        if isinstance(value, datetime):
            return "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        return "TEXT"

    def insert_or_update_expose(self, expose):
        try:
            if self.update_expose(expose):
                return True
        except ExposeUpdateError:
            return self.insert_expose(expose)

    def insert_expose(self, expose):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join(expose.to_dict().keys())
            placeholders = ', '.join(['?'] * len(expose.to_dict()))
            values = tuple(expose.to_dict().values())
            cursor.execute(f"""
                INSERT INTO exposes ({fields})
                VALUES ({placeholders})
            """, values)
            logging.info(f"Expose {expose.expose_id} inserted successfully.")
            return True

    def update_expose(self, expose):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            fields = ', '.join(f"{key}=?" for key in expose.to_dict().keys())
            values = tuple(expose.to_dict().values()) + (expose.expose_id,)
            cursor.execute(f"""
                UPDATE exposes SET {fields} WHERE expose_id=?
            """, values)
            if cursor.rowcount:
                logging.info(f"Expose {expose.expose_id} updated successfully.")
                return True
            else:
                raise ExposeUpdateError(f"Failed to update expose {expose.expose_id}, not found.")

    def get_expose(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM exposes WHERE expose_id=?
            """, (expose_id,))
            row = cursor.fetchone()
            if row:
                return Expose(*row[1:])
            raise ExposeNotFoundError(f"Expose {expose_id} not found.")

    def expose_exists(self, expose_id):
        try:
            self.get_expose(expose_id)
            return True
        except ExposeNotFoundError:
            return False

    def delete_expose_by_id(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exposes WHERE expose_id=?", (expose_id,))
            conn.commit()
            if cursor.rowcount == 0:
                logging.warning(f"Expose {expose_id} not found in the database.")
                return False
            return True

    def mark_expose_as_processed(self, expose_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE exposes SET processed=1 WHERE expose_id=?
            """, (expose_id,))
            if cursor.rowcount:
                logging.info(f"Expose {expose_id} marked as processed.\n")
                conn.commit()
                return True
            else:
                raise ExposeNotFoundError(f"Expose {expose_id} not found in the database.")

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
                logging.info(f"Failures count for expose {expose_id} increased to {failures_count}.")
                return failures_count
            raise ExposeNotFoundError(f"Expose {expose_id} not found.")

    def get_unprocessed_exposes(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exposes WHERE processed=0 AND failures < ?", (self.max_attempts_expose,))
            rows = cursor.fetchall()
            exposes = [Expose(*row[1:]) for row in rows]
            logging.info(f"Fetched {len(exposes)} unprocessed exposes.")
            return exposes
        
    def print_all_exposes(self):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exposes")
            rows = cursor.fetchall()
            for row in rows:
                print(Expose(*row[1:]))

    def clear_all_exposes(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM exposes")
            conn.commit()
            logging.warning("All exposes have been cleared.")