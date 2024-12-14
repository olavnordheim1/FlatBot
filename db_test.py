# test.py
from database import print_all_exposes, clear_exposes, delete_expose_by_id


def main():
    print("Testing Database Utilities...")

    # Print all exposes
    print_all_exposes()

    # Clear all exposes
    clear_exposes()

    # Delete a specific expose
    #delete_expose_by_id("155920388")

if __name__ == "__main__":
    main()