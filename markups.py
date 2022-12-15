from telebot import types
import config
import json

def moderate_markup(user):
    markup = types.InlineKeyboardMarkup()
    btn_accept = types.InlineKeyboardButton("Принять", callback_data=f"accept/{user.id}")
    btn_decline = types.InlineKeyboardButton("Отклонить", callback_data=f"decline/{user.id}")
    markup.add(btn_accept, btn_decline)
    return markup


def skip_mail_markup():
    markup = types.InlineKeyboardMarkup()
    btn_skip = types.InlineKeyboardButton("Пропустить", callback_data=f"skip_mail")
    markup.add(btn_skip)
    return markup

def skip_device_markup():
    markup = types.InlineKeyboardMarkup()
    btn_skip = types.InlineKeyboardButton("Пропустить", callback_data=f"skip_device")
    markup.add(btn_skip)
    return markup


def tags_markup(userdata):
    time_markup = {"inline_keyboard": [[]]}
    selected_tags = userdata.tags


    for option in config.tags:

        if option in selected_tags: option_name = f"{option} ☑️"
        else: option_name = option
        if len(time_markup["inline_keyboard"][-1]) < 2:
            time_markup["inline_keyboard"][-1].append({"text": option_name, "callback_data": option})
        else:
            time_markup["inline_keyboard"].append([{"text": option_name, "callback_data": option}])
    time_markup["inline_keyboard"].append([{"text": "Принять", "callback_data":'ACCEPT'}])
    return json.dumps(time_markup)