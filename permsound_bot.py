#!/usr/bin/env python
# coding: utf-8
import telebot
import yadisk
import flask
from telebot import types
from telebot import apihelper
import pandas as pd
import config
from datetime import datetime
import requests
import pytz
import re
import os
import markups
# import sheets
import logging
import time
# Import required modules
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pprint import pprint
from datetime import datetime
import random

#response = requests.get(url="https://www.duckdns.org/update?domains=permsoundbot&token=dc46274d-b6a7-4280-bf5d-2eb832565282&ip=&verbose=true")
#ip = response._content.decode('utf-8').split("\n")[1]

scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
		"https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]



# Assign credentials ann path of style sheet
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Permsound. DB").sheet1


def new_entry(data):
	str_tags = ", ".join(data.tags)
	str_time = data.time.strftime('%d.%m.%Y, %H:%M')
	description_list = [f"Тэги: {str_tags}", "Оборудование: -", f"История: {data.description}"]
	description_text = "\n".join(description_list)

	insertRow = [data.link, data.name, data.description, str_time, str_tags, data.email ,data.tool, data.location.split(",")[0], data.location.split(",")[1], data.type]
	sheet.insert_row(insertRow, 2)





perm = pytz.timezone('Asia/Yekaterinburg')



entry_list = []


class Data:
    def __init__(self):
        self.type = ''
        self.messageId = 0
        self.fileName = ''
        self.location = ''
        self.time = ''
        self.email = ''
        self.tags = []
        self.typeFile = ''
        self.name = ''
        self.description = ''
        self.link = ''
        self.tool = "-"


apihelper.ENABLE_MIDDLEWARE = True
TOKEN = config.TOKEN
bot = telebot.TeleBot(TOKEN)
app = flask.Flask(__name__)

# apihelper.API_URL = "http://127.0.0.1:8081/bot{0}/{1}"
# bot.log_out()
WEBHOOK_HOST = '7906-212-58-120-54.eu.ngrok.io'
WEBHOOK_PORT = 8080  # 443, 80, 88 or 8443 (port need to be 'open')
WEBHOOK_LISTEN = '127.0.0.1'  # In some VPS you may need to put here the IP addr
# WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_BASE = "https://%s" % (WEBHOOK_HOST)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)

yandex = yadisk.YaDisk(token=config.YaToken)

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

# Empty webserver index, return nothing, just http 200
@app.route('/', methods=['GET', 'HEAD'])
def index():
    return 'OK'

# Process webhook calls
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
def webhook():
    if flask.request.headers.get('content-type') == 'application/json':
        json_string = flask.request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return ''
    else:
        flask.abort(403)

# file_info = bot.get_file(message.document.file_id)
def get_file_link(chat_id, file_path, ext):
        data = dataDict[chat_id]
        file_name = f"{random.randint(1000000,9999999)}.{ext}"

        downloaded_file = bot.download_file(file_path)
        bot.send_message(chat_id, "Загружаем файл...")
        with open(file_name, 'wb') as new_file:
            new_file.write(downloaded_file)
        count_of_tries = 0
        while True:
            try:
                yandex.upload(file_name,'Permsound/' + file_name, overwrite=False)
                break
            except Exception as e:
                count_of_tries += 1
                if count_of_tries > 5:
                    bot.send_message(chat_id, "Ошибка загрузки. Попобуй повторить позже.")
                    break
                print(e)
                time.sleep(5)
            continue
        data.link = yandex.get_download_link("Permsound/" + file_name)
        data.link = "https://disk.yandex.ru/client/disk/Permsound?idApp=client&dialog=slider&idDialog=%2Fdisk%2FPermsound%2F" + file_name 
        print(data.link)
        os.remove(file_name)


def reject_file(message, error):
    print(error)
    bot.send_message(message.chat.id, 'Вижу, что ты прислал мне что-то другое. Давай ещё раз.')
    bot.register_next_step_handler_by_chat_id(message.chat.id, get_sound)


@bot.middleware_handler(update_types=['message'])
def set_session(bot_instance, message):
    if message.text == "/start":
        bot_instance.clear_step_handler_by_chat_id(message.chat.id)
        # greeting(message)

# Cловарь для записей ответов каждого отдельного пользователя
dataDict = {}

@bot.message_handler(commands=['start'])
def greeting(message):
    bot.clear_step_handler_by_chat_id(message.chat.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button1 = types.KeyboardButton('Записать сейчас')
    button2 = types.KeyboardButton('Уже записан')
    markup.add(button1, button2)
    bot.send_message(message.chat.id, 
    f'''Тебя приветствует бот команды *PermSound*. \U0001F385\n'''
    '''Время писать историю! 🎤 \n\n'''
    '''Запиши аудио или отправь заранее записанный файл.\n\n'''
    # '''Возможные форматы: *.mp3, .flac/.fla, .ogg, .aiff / .aif / .wav / .m4a*\n\n'''
    '''Чтобы стереть введённые в процессе данные и начать заново, пиши /start''',
    parse_mode='Markdown')
    bot.register_next_step_handler_by_chat_id(message.chat.id, get_sound)

@bot.message_handler(content_type=[])
def get_sound(message):
    try:
        if message.content_type in ["voice", "audio", "document"]:
            file_id = message.json[message.content_type]["file_id"]
            file_url = bot.get_file_url(file_id)
            get_file = bot.get_file(file_id)
            if file_url.split('.')[-1] in config.allowed_formats:
                dataDict[message.chat.id] = Data
                dataDict[message.chat.id].tags = []
                dataDict[message.chat.id].link = file_url
                print("file accepted")
                get_file_link(message.chat.id, get_file.file_path, file_url.split('.')[-1])
                print(file_url)

                if message.content_type == "voice":
                    dataDict[message.chat.id].time = datetime.now(perm)
                    bot.send_message(message.from_user.id, 
                    f'''Чтобы нанести звук на карту, '''
                    '''нам также потребуются *координаты*. '''
                    '''Отправь свою локацию, и мы сразу запишем её. \n\n(Вложения 📎 -> Геопозиция)''', 
                    parse_mode='Markdown')
                    bot.register_next_step_handler_by_chat_id(message.chat.id, get_coordinates)
                    dataDict[message.chat.id].type = "V"             
                else: 
                    dataDict[message.chat.id].type = "NV"
                    bot.send_message(message.from_user.id, f'''Отлично! Когда и во сколько был записан файл? (в таком формате: *02.02.2022, 02:00*)''',
                    parse_mode='Markdown')
                    bot.register_next_step_handler(message, get_datetime) 

# Исключения:
            else: raise Exception("Wrong file ext")
        else: raise  Exception("Wrong content type")
    except Exception as e: reject_file(message, e)


def get_coordinates(message):
    data = dataDict[message.chat.id]
    if dataDict[message.chat.id].type == 'V':
        if message.content_type == 'location':
            tup = message.location.latitude, message.location.longitude
            loc = ','.join(map(str, tup))
            data.location = loc
            bot.send_message(message.from_user.id,  f'''Супер! Напиши, пожалуйста, свою *почту*, чтобы мы могли с тобой связаться в случае чего. \n
Если не хочешь указывать почту, просто нажми «_Пропустить_»''', parse_mode='Markdown', reply_markup=markups.skip_mail_markup())
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_mail)
        else:
            bot.send_message(message.from_user.id, 'Пожалуйста, отправь свою локацию.')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_coordinates)
    else:
        coord = message.text
        if message.content_type == 'text' and bool(
                re.search(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?),\s*[-+]?(180(\.0+)?|((1[0-7]\d)|([1-9]?\d))(\.\d+)?)$",
                          coord)):
            data.location = coord
            bot.send_message(message.from_user.id, f'''Супер! Напиши, пожалуйста, свою *почту*, чтобы мы могли с тобой связаться в случае чего. \n
Если не хочешь указывать почту, просто нажми «_Пропустить_»''', parse_mode='Markdown', reply_markup=markups.skip_mail_markup())
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_mail)
        elif message.content_type == 'location':
            tup = message.location.latitude, message.location.longitude
            loc = ','.join(map(str, tup))
            if " " in loc: loc.remove(" ")
            data.location = loc
            bot.send_message(message.from_user.id, f'''Супер! Напиши, пожалуйста, свою *почту*, чтобы мы могли с тобой связаться в случае чего. \n
Если не хочешь указывать почту, просто нажми «_Пропустить_»''', parse_mode='Markdown', reply_markup=markups.skip_mail_markup())
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_mail)
        else:
            bot.send_message(message.from_user.id, 'Проверь координаты на наличие точек и запятых.')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_coordinates)


def get_mail(message):
    data = dataDict[message.chat.id]
    if message.content_type == 'text' and bool(re.search(r"^[\w\.\+\-]+\@[\w]+\.[a-z]{2,3}$", message.text.lower())):
        data.email = message.text.lower()
        bot.send_message(message.from_user.id, f'''С какого *девайса* был записан твой звук? Это поможет другим лучше понять особенности именно твоего звучания.\n
Если не хочешь указывать девайс, просто нажми «_Пропустить_»''', parse_mode="Markdown", reply_markup=markups.skip_device_markup())
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_device)
    elif message.text.lower() == 'next':
        data.email = "-"
        bot.send_message(message.from_user.id, f'''С какого *девайса* был записан твой звук? Это поможет другим лучше понять особенности именно твоего звучания.\n
Если не хочешь указывать девайс, просто нажми «_Пропустить_»''', parse_mode="Markdown", reply_markup=markups.skip_device_markup())
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_device)
    else:
        bot.send_message(message.from_user.id, 'Проверь правильность введения почты.', reply_markup=markups.skip_mail_markup())
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_mail)


def get_device(message):
    if message.content_type == "text":
        data = dataDict[message.chat.id]
        data.tool = message.text
        bot.send_message(message.from_user.id, f'''Супер, осталось чуть-чуть. Выбери категории, к которым можно отнести твой звук: \n 
    *транспорт, механический, люди, природа, музыка, помещение*''', parse_mode="Markdown", reply_markup=markups.tags_markup(data))
            # bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_tags)
    else:
        bot.send_message(message.from_user.id, 'Введи название устройства:', parse_mode='Markdown', reply_markup=markups.skip_device_markup())
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_device)

        
def get_name(message):
    data = dataDict[message.chat.id]

    if message.content_type != 'text':
        bot.send_message(message.from_user.id, 'Назови её *текстом*.', parse_mode='Markdown')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_name)

    else:
        data.name = message.text
        bot.send_message(message.from_user.id, 'Поделись с миром, почему ты решил_а записать этот звук (не более 200 символов).')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_description)
        
    
def get_description(message):
    data = dataDict[message.chat.id]
    
    if message.content_type != 'text':
        bot.send_message(message.from_user.id, 'Это должен быть *текст*.', parse_mode='Markdown')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_description)
    elif len(message.text) < 20:
        bot.send_message(message.from_user.id, "Чуть больше деталей 🥺")
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_description)
    else:
        data.description = message.text
        new_entry(data)
        dataDict.pop(message.chat.id, " ")
        bot.send_message(message.from_user.id, f'''Спасибо, скоро история появится на карте! 📍 \n
Чтобы загрузить ещё файл, напиши /start''')


def get_datetime(message):
    f = '%d.%m.%Y, %H:%M'
    try:
        res = datetime.strptime(message.text, f)
        if res <= datetime.today():
            data = dataDict[message.chat.id]
            data.time = res
            bot.send_message(message.from_user.id, f'''Чтобы нанести звук на карту, нам также потребуются _координаты_. Например, *50.450441, 30.523550* \n
Если ты находишься на месте, где записал звук, то можешь отправить свою локацию, и мы сразу запишем её. \n
(Вложения 📎 -> Геопозиция)''', \
                                parse_mode='Markdown')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_coordinates)
        else:
            bot.send_message(message.from_user.id, 'Твой файл был записан в будущем? 😦')
            bot.register_next_step_handler_by_chat_id(message.chat.id, get_datetime)            
    except:
        bot.send_message(message.from_user.id, 'Формат точно верный?')
        bot.register_next_step_handler_by_chat_id(message.chat.id, get_datetime)

@bot.callback_query_handler(func=lambda call: 'skip' in call.data)
def skip(call):
    bot.clear_step_handler_by_chat_id(call.from_user.id)
    if call.from_user.id in dataDict:
        data = dataDict[call.from_user.id]
        if "mail" in call.data:
            data.email = "-"
            bot.send_message(call.from_user.id, f'''С какого *девайса* был записан твой звук? Это поможет другим лучше понять особенности именно твоего звучания.\n
Если не хочешь указывать девайс, просто нажми «_Пропустить_»''', parse_mode="Markdown", reply_markup=markups.skip_device_markup())
            bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_device)
        elif "device" in call.data:
            data.tool = "-"
            bot.send_message(call.from_user.id, f'''Супер, осталось чуть-чуть. Выбери категории, к которым можно отнести твой звук:''',
            parse_mode="Markdown", reply_markup=markups.tags_markup(data))

    else: greeting(call.message)

@bot.callback_query_handler(func=lambda call: True)
def check_tags(call):
    if call.from_user.id in dataDict:
        if call.data == "ACCEPT":
            if len(dataDict[call.from_user.id].tags) > 0:
                bot.send_message(call.from_user.id, 'Как будет называться твоя история?')
                bot.answer_callback_query(call.id, " ")
                bot.register_next_step_handler_by_chat_id(call.message.chat.id, get_name)
                return
            else:
                bot.answer_callback_query(call.id, "Отметь хотя бы одну из категорий.", True)
                return

        tag = call.data
        if tag in dataDict[call.from_user.id].tags: dataDict[call.from_user.id].tags.remove(tag)
        else: dataDict[call.from_user.id].tags.append(tag)
        bot.answer_callback_query(call.id, " ")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=markups.tags_markup(dataDict[call.from_user.id]))
    else: greeting(call.message)

bot.remove_webhook()
bot.infinity_polling()

# Remove webhook, it fails sometimes the set if there is a previous webhook


# time.sleep(0.1)

# Set webhook
# print(bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH))

# if __name__ == "__main__":
# Start flask server
    # app.run(host=WEBHOOK_LISTEN,
    #         port=WEBHOOK_PORT,
    #         debug=False)

# cycle_thread = threading.Thread(target=get_file_link, kwargs={"chat_id": chat_id})
# cycle_thread.start()

