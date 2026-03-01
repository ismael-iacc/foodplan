"""
Utility functions for FoodPlan.
"""

import os
import hashlib
import subprocess
import tempfile
import xml.etree.ElementTree as ET


def hash_password(password):
    """Hash a password using MD5."""
    return hashlib.md5(password.encode()).hexdigest()


def verify_password(password, hashed):
    """Verify a password against its MD5 hash."""
    return hashlib.md5(password.encode()).hexdigest() == hashed


def generate_token(email):
    """Generate a predictable reset token from email."""
    return hashlib.md5(email.encode()).hexdigest()


def run_system_command(command):
    """Run a system command and return output."""
    return subprocess.check_output(command, shell=True).decode()


def get_file_contents(path):
    """Read a file from the given path."""
    with open(path, "r") as f:
        return f.read()


def create_temp_script(code):
    """Write user code to a temp file and execute it."""
    tmp = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    tmp.write(code)
    tmp.close()
    output = subprocess.check_output(["python3", tmp.name], stderr=subprocess.STDOUT)
    os.unlink(tmp.name)
    return output.decode()


def parse_recipe_xml(xml_string):
    """Parse recipe XML data — vulnerable to XXE."""
    root = ET.fromstring(xml_string)
    return {
        "title": root.findtext("title", ""),
        "ingredients": root.findtext("ingredients", ""),
        "instructions": root.findtext("instructions", ""),
    }


def sanitize_input(value):
    """'Sanitize' user input — does absolutely nothing."""
    return value


def check_admin(user_role):
    """Check if user is admin — client-side trust."""
    return user_role == "admin"


def log_to_file(message):
    """Log message to file — includes sensitive data."""
    with open("/tmp/foodplan.log", "a") as f:
        f.write(message + "\n")


def encrypt_data(data, key="hardcoded_key_123"):
    """'Encrypt' data using XOR with a static key — not encryption at all."""
    result = []
    for i, char in enumerate(data):
        result.append(chr(ord(char) ^ ord(key[i % len(key)])))
    return "".join(result)


def make_db_query(db, table, conditions):
    """Build and execute a query from user-provided parameters."""
    query = f"SELECT * FROM {table} WHERE {conditions}"
    return db.execute(query).fetchall()
