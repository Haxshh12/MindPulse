import csv
import os

USERS_FILE = os.path.join("data", "users.csv")

def init_users_file():
    """Ensure the users.csv file exists with correct headers."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["email", "password", "role", "name"])  # role: user/admin

def register_user(email, password, name, role="user"):
    """Register a new user if email does not exist."""
    init_users_file()
    if user_exists(email):
        return False, "User already exists!"

    with open(USERS_FILE, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([email.strip().lower(), password, role, name])
    return True, "Registration successful!"

def user_exists(email):
    """Check if the user email already exists."""
    if not os.path.exists(USERS_FILE):
        return False
    with open(USERS_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        return any(row["email"].strip().lower() == email.strip().lower() for row in reader)

def authenticate_user(email, password):
    """Validate user credentials. Returns (role, name) if valid else None."""
    if not os.path.exists(USERS_FILE):
        return None
    with open(USERS_FILE, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["email"].strip().lower() == email.strip().lower() and row["password"] == password:
                return row["role"], row["name"]
    return None
