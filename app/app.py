import os, io, subprocess, random, string, re, json, ast, emoji, requests, telegram, configparser, logging
import speech_recognition as sr
from flask import Flask, request
from datetime import datetime
from conf.projects import tasks_id_map

app = Flask(__name__)

# Configurazione dei log
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Definiamo le emoji da utilizzare
clock_icon = emoji.emojize(":alarm_clock:")
category_icon = emoji.emojize(":bookmark:")
description_icon = emoji.emojize(":memo:")

# Carica il token dal file di configurazione
config = configparser.ConfigParser()
config.read('conf/app.conf')

# Carica gli utenti autorizzati da JSON
with open('conf/authorized_users.json', 'r') as f:
    authorized_users = json.load(f)

platform_user_id = -1

bot_token = config.get('telegram', 'token')

bot = telegram.Bot(token=bot_token)

def generate_random_path(length=8):
    return '/tmp/audio_' + ''.join(random.choices(string.digits, k=length)) + '.wav'

def process_timesheet(text):
    pattern = r"(\d+(\.\d+)?)\s+([\w-]+|\d+)\s+(.*)"
    match = re.match(pattern, text)

    if match:
        number = round(float(match.group(1)) / 60, 2)
        task_key = match.group(3)
        task_id, task_summary = convert_to_task_id(task_key)
        description = match.group(4)
        return number, task_key, task_id, task_summary, description
    else:
        return None, None, None, None, None

def convert_to_task_id(string):

    upString = string.upper()
    pattern = r"^\d+$"
    if 'BVTL-' in upString or re.match(pattern, upString):

        if not upString.startswith('BVTL-'):
            upString = 'BVTL-' + upString

        api_base_url = config.get('api', 'base_url')
        task_api_url = f"{api_base_url}/task/jira/{upString}"
        api_token = config.get('api', 'token')
        headers = {'Authorization': f'{api_token}'}
        response = requests.get(task_api_url, headers=headers)

        if response.status_code == 200:
            if response.json().get("data", {}).get("task", {}) is not None:
                taskInfo = response.json().get("data", {}).get("task", {})
                return taskInfo.get("id"), taskInfo.get("summary")
            else:
                raise Exception(f"Task not found: {upString}")
        else:
            raise Exception(f"Error calling the task API: {response.status_code}")

    else:
        for name, value in tasks_id_map.items():
            if upString == name.upper():
                return tasks_id_map[name], string
    return '', ''

def insert_timesheet_in_external_system(duration, task_id, description, platform_user_id):

    data = {
        'duration': duration,
        'task_id': task_id,
        'description': description,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'completion_percentage': 100,
        'task_state': 'Done',
        'commit_id': 'no_commit',
        'user_id': platform_user_id
    }

    api_base_url = config.get('api', 'base_url')
    api_token = config.get('api', 'token')

    headers = {'Authorization': f'{api_token}'}

    response = requests.post(api_base_url + '/timesheets', data=data, headers=headers)

def process_voice_message(update):
    file_id = update.message.voice.file_id
    file = bot.get_file(file_id)
    audio_bytes = io.BytesIO(file.download_as_bytearray())

    wav_path = generate_random_path()
    ffmpeg_command = ['ffmpeg', '-i', '-', '-acodec', 'pcm_s16le', '-ac', '1', '-ar', '16000', wav_path]

    try:
        subprocess.run(ffmpeg_command, input=audio_bytes.read(), check=True)
    except subprocess.CalledProcessError as e:
        update.message.reply_text(f"Error during audio conversion with ffmpeg: {e}.")
        return

    recognizer = sr.Recognizer()

    with sr.AudioFile(wav_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language='it-IT')
        number, project, task_id, task_summary, description = process_timesheet(text)

        if number and project and task_id and description:
            platform_user_id = get_platform_user_id(update.message.from_user.id)
            insert_timesheet_in_external_system(number, task_id, description, platform_user_id)
            update.message.reply_text(f"<b>Inserted timesheet</b>\n\n"
                                      f"{clock_icon}  {number} h\n"
                                      f"{category_icon}  {task_summary} (task_id: {task_id})\n"
                                      f"{description_icon}  {description}"
                                      , parse_mode="HTML")
        else:
            update.message.reply_text(f"Invalid message: {text}")

    except sr.UnknownValueError:
        update.message.reply_text("Failed to convert audio to text.")
    except sr.RequestError:
        update.message.reply_text("Error occurred during audio conversion.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

    os.remove(wav_path)

def process_text_message(update):

    text = update.message.text

    try:
        if text.lower() == '/get_my_telegram_id':
            get_my_telegram_id(update)
        elif text.lower() == '/get_projects_list':
            get_projects_list(update)
        else:
            number, project, task_id, task_summary, description = process_timesheet(text)

            if number and project and task_id and description:
                platform_user_id = get_platform_user_id(update.message.from_user.id)
                insert_timesheet_in_external_system(number, task_id, description, platform_user_id)
                update.message.reply_text(f"<b>Inserted timesheet</b>\n\n"
                                          f"{clock_icon}  {number} h\n"
                                          f"{category_icon}  {task_summary} (task_id: {task_id})\n"
                                          f"{description_icon}  {description}"
                                          , parse_mode="HTML")
            else:
                update.message.reply_text(f"Invalid message: {text}")

    except sr.UnknownValueError:
        update.message.reply_text("Failed to convert audio to text.")
    except sr.RequestError:
        update.message.reply_text("Error occurred during audio conversion.")
    except Exception as e:
        update.message.reply_text(f"An error occurred: {str(e)}")

# COMMAND get_my_telegram_id
def get_my_telegram_id(update):
    user_id = update.message.from_user.id
    update.message.reply_text(f"This is your Telegram ID: {user_id}")

# COMMAND get_projects_list
def get_projects_list(update):
    project_list = '\n'.join(tasks_id_map.keys())
    update.message.reply_text(f"{project_list}")

@app.route('/{}'.format(bot.token), methods=['POST'])
def telegram_webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    if not update.message:
        logger.info(update)
        return 'OK'

    user_id = update.message.from_user.id

    if str(user_id) not in authorized_users and update.message.text.lower() != '/get_my_telegram_id':
        update.message.reply_text("Unauthorized")
        return 'Unauthorized'

    if update.message.voice:
        process_voice_message(update)
    elif update.message.text:
        process_text_message(update)

    return 'OK'

def get_platform_user_id(user_id):
    return authorized_users.get(str(user_id), '')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
