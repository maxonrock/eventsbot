# -*- coding: utf-8 -*-
from enum import Enum

token = ''
db_name = "events.db"

class Answers(Enum):
    ACCEPT = "Accept"
    DECLINE = "Decline"
    WAIT = "Wait"
    STOP = "Stop"
    START = "Start"

class Events(Enum):
    SMOKE = "smoke"
    EAT = "eat"
    WORKHOME = "workhome"
    DIMA = "dima"
    SUGGEST = "suggest"

button_labels = {
    Answers.ACCEPT: "Принять",
    Answers.DECLINE: "Отклонить",
    Answers.WAIT: "Позже",
    Answers.STOP: "Завершить",
    Answers.START: "Начать",
}

event_labels = {
    Events.SMOKE.value: "предлагает сходить на перекур",
    Events.EAT.value: "предлагает покушать",
    Events.WORKHOME.value: "интересуется кто в хате",
    Events.DIMA.value: "интересуется в офисе ли Дима",
}

event_inline_suggestions = {
    Events.SMOKE: "Го курить",
    Events.EAT: "Го кушать",
    Events.WORKHOME: "Узнать кто в хате",
    Events.DIMA: "Дима в здании?",
    Events.SUGGEST: "Предложить",
}