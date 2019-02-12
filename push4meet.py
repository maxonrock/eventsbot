# -*- coding: utf-8 -*-
import config
import telebot
from telebot import types
from config import Answers
from config import Events
from config import button_labels
from config import event_labels
from config import event_inline_suggestions
from db import Db

bot = telebot.TeleBot(config.token)


def getKeyboardButton(answer, event=None):
    data = answer.value
    if event:
        data = "inline"+event + data
    return types.InlineKeyboardButton(text=button_labels[answer], callback_data=data)


def getKeyboard():
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.row(
        getKeyboardButton(Answers.ACCEPT),
        getKeyboardButton(Answers.DECLINE),
        getKeyboardButton(Answers.WAIT),
    )
    keyboard.add(getKeyboardButton(Answers.STOP))
    return keyboard


def getUsername(from_user):
    name = ""
    if from_user.last_name:
        if from_user.first_name:
            name = name + from_user.first_name
        if from_user.last_name:
            name = name + " " + from_user.last_name
        return name
    else:
        if from_user.username:
            name = name + from_user.username
        return name


def createEvent(text, message):
    keyboard = getKeyboard()
    username = getUsername(message.from_user)
    reply = bot.send_message(
        message.chat.id,  username + " " + text + "\n", reply_markup=keyboard)
    db = Db()
    db.create_event(reply.chat.id, reply.message_id,
                    message.from_user.id, username, text)


@bot.message_handler(commands=[Events.SMOKE.value])
def smoke(message):
    createEvent(event_labels[Events.SMOKE.value], message)


@bot.message_handler(commands=[Events.EAT.value])
def eat(message):
    createEvent(event_labels[Events.EAT.value], message)


@bot.message_handler(commands=[Events.WORKHOME.value])
def workhome(message):
    createEvent(event_labels[Events.WORKHOME.value], message)

@bot.message_handler(commands=[Events.DIMA.value])
def workhome(message):
    createEvent(event_labels[Events.DIMA.value], message)

@bot.message_handler(commands=[Events.SUGGEST.value])
def suggest(message):
    createEvent("предлагает" + (message.text).replace("/suggest", ""), message)


def getInlineQueryResultArticle(id, event, text, query_text=None):
    title = title = event_inline_suggestions[event]
    if query_text:
        title = title + " " + query_text
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    keyboard.add(getKeyboardButton(Answers.START, event=text))
    return types.InlineQueryResultArticle(
        id=id, title=title,
        input_message_content=types.InputTextMessageContent(
            message_text=text + "\n"),
        reply_markup=keyboard
    )


@bot.inline_handler(lambda query: True)
def query_text(query):
    results = []
    results.append(getInlineQueryResultArticle(
        1, Events.SMOKE, "Предлагаю сходить на перекур"))
    results.append(getInlineQueryResultArticle(
        2, Events.EAT, "Предлагаю покушать"))
    results.append(getInlineQueryResultArticle(
        3, Events.WORKHOME, "Кто пойдет в хату?"))
    results.append(getInlineQueryResultArticle(
        4, Events.DIMA, "Узнать про Диму"))
    if len((query.query).strip()) > 2 and len(query.query) < 19:
        results.append(getInlineQueryResultArticle(
            5, Events.SUGGEST, "Предлагаю " + query.query, query.query))
    bot.answer_inline_query(query.id, results, cache_time=1)


def stopEvent(db, owner_id, user_id, inline_message_id, chat_id, message_id, call_id):
    if owner_id and owner_id == user_id:
        if inline_message_id:
            newText = getEventInfo(
                db, chat_id, inline_message_id) + "\nЭтот опрос завершен"
            bot.edit_message_text(
                inline_message_id=inline_message_id, text=newText, reply_markup=None)
            db.delete_event(chat_id, inline_message_id)
        else:
            bot.delete_message(chat_id=chat_id, message_id=message_id)
            db.delete_event(chat_id, message_id)
    else:
        bot.answer_callback_query(
            callback_query_id=call_id, text="Завершение опроса доступно только его создателю")


def createAnswer(db, owner_id, user_id, chat_id, message_id, call):
    if owner_id == user_id and call.data != Answers.WAIT.value:
       bot.answer_callback_query(
           callback_query_id=call.id, text="Голосование недоступно создателю опроса")
       return False
    exists = db.select_answer(chat_id, message_id, user_id)
    if exists:
        bot.answer_callback_query(
            callback_query_id=call.id, text="Вы уже голосовали")
        return False
    else:
        username = getUsername(call.from_user)
        db.create_answer(chat_id, message_id, user_id, username, call.data)
        bot.answer_callback_query(
            callback_query_id=call.id, text="Ваш ответ принят")
        return True


def getGroupAnswers(group, title):
    if len(group) > 0:
        return title + ": " + group + "\n"
    return ""


def getEventInfo(db, chat_id, message_id):
    event = db.select_event(chat_id, message_id)
    if event:
        event = event[0]
        if "inline" in event[1]:
            text = event[1].replace("inline", "") + "\n"
        else:
            text = event[0] + " " + event[1] + "\n"
        accepted = ""
        declined = ""
        waited = ""
        answers = db.select_answers(chat_id, message_id)
        for answer in answers:
            if Answers.ACCEPT.value in answer[0]:
                accepted = accepted + answer[1] + " "
            if Answers.DECLINE.value in answer[0]:
                declined = declined + answer[1] + " "
            if Answers.WAIT.value in answer[0]:
                waited = waited + answer[1] + " "
        return text + getGroupAnswers(accepted, "Приняли") + getGroupAnswers(declined, "Отклонили") + getGroupAnswers(waited, "Просили подождать")
    return "Опрос завершен"


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    keyboard = getKeyboard()

    db = Db()
    user_id = call.from_user.id
    if call.message:
        chat_id = call.message.chat.id
        message_id = call.message.message_id
        owner_id = db.get_owner(chat_id, message_id)
        if Answers.STOP.value in call.data:
            stopEvent(db, owner_id, user_id, None,
                      chat_id, message_id, call.id)
        else:
            needUpdate = createAnswer(
                db, owner_id, user_id, chat_id, message_id, call)
            if needUpdate:
                newText = getEventInfo(db, chat_id, message_id)
                bot.edit_message_text(
                    newText, chat_id=chat_id, message_id=message_id, reply_markup=keyboard)
            # Если сообщение из инлайн-режима
    elif call.inline_message_id:
        message_id = call.inline_message_id
        chat_id = call.chat_instance
        owner_id = db.get_owner(chat_id, message_id)
        if Answers.STOP.value in call.data:
            stopEvent(db, owner_id, user_id, message_id,
                      chat_id, None, call.id)
        elif Answers.START.value in call.data:
            db.create_event(chat_id, message_id, user_id, getUsername(call.from_user),
                            (call.data).replace(Answers.START.value, ""))
            bot.edit_message_reply_markup(
                inline_message_id=message_id, reply_markup=keyboard)
        else:
            needUpdate = createAnswer(
                db, owner_id, user_id, chat_id, message_id, call)
            if needUpdate:
                newText = getEventInfo(db, chat_id, message_id)
                bot.edit_message_text(
                    newText, inline_message_id=message_id, reply_markup=keyboard)


#@bot.message_handler(content_types=["text"])
def any_msg(message):
    usertext = getUsername(message.from_user) + \
        ", иди нахуй со своим " + message.text + " "
    bot.send_message(message.chat.id, usertext)


if __name__ == '__main__':
    bot.polling(none_stop=True)
