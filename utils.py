import hashlib
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def hash_string(input_string):
    # Use a fixed salt value for determinism
    salt = "83475tsc348tsise4tyv8etne84tvyek4tgynse4tb5yu"

    # Combine the input string and the salt
    salted_string = input_string + salt

    # Calculate the SHA-256 hash
    hashed_string = hashlib.sha256(salted_string.encode()).hexdigest()

    # Filter out non-alphanumeric characters
    alphanumeric_hash = ''.join(char for char in hashed_string if char.isalnum())

    return alphanumeric_hash


def format_email_for_filename(email):
    """
    Formats an email address to be used as a valid filename.

    :param email: The email address to format.
    :return: A string that is safe to use as a filename.
    """
    return hash_string(email) + ".json"


def send_email(subject, body, recipient):
    # Your email and password
    sender_email = 'info@xn--hrberg-wxa.net'
    password = os.environ.get('INFO_EMAIL_PASSWORD')
    # Create a message object
    message = MIMEMultipart()
    message['From'] = sender_email
    message['To'] = recipient
    message['Subject'] = subject

    # Email content
    message.attach(MIMEText(body, 'plain'))

    # SMTP server configuration
    smtp_server = 'localhost'
    smtp_port = 587  # Use port 587 for STARTTLS

    # Connect to the SMTP server with STARTTLS encryption
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Start TLS encryption
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, recipient, message.as_string())
    except Exception as e:
        print('Error:', e)
    finally:
        server.quit()

def string_format_modifier(modifier: int):
    if modifier > 0:
        return f"+{modifier}"
    elif modifier == 0:
        return f"+/-{modifier}"
    else:
        return f"-{modifier}"

def read_savefile_and_pop_events(save_file):
    with open(save_file, 'r') as f:
        json_data = json.load(f)

    if 'events' in json_data.keys():
        events = json_data['events']
    else:
        events = ""
    json_data['events'] = ""

    with open(save_file, 'w') as f:
        json.dump(json_data, f)

    return json_data, events

def update_savefile(save_file, key, value):
    with open(save_file, 'r') as f:
        json_data = json.load(f)

    json_data[key] = value

    with open(save_file, 'w') as f:
        json.dump(json_data, f)
