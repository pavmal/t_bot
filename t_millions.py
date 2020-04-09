import telebot
from telebot import types
import random
import time
from itertools import permutations
import requests

from config import token, URL_QUESTIONS

bot = telebot.TeleBot(token)

bot_users = []
user_states = {}
user_results = {}
user_faults = {}
user_complex = {}
user_data = {}

GREETINGS = ['hi', 'привет']
GO_TO_QUESTION = ['спроси меня вопрос', 'спроси меня', 'следущий вопрос', 'ещё', 'давай вопрос', 'да', '?', 'вопрос']
QUESTION_LEVEL = ['1 - разминочный', '2 - средний', '3 - для эрудитов']
CANCEL_QUESTION = ['не хочу', 'нет', 'надоело', 'достал', 'отвали']
SHOW_RESULTS = ['покажи счёт', 'какой счёт', 'результат игры', 'счет', 'счёт', 'итог']

ANSWER_BASE = 'Я тебя не понял :('
NEW_USER = 'new'
BASE_STATE = 'base'
ASK_QUESTION_STATE = 'ask_question'

QUESTIONS = [
    {'id': 0, 'question': 'Туристы, приезжающие на Майорку, обязаны заплатить налог на …?',
     'answers': ['солнце', 'купальник', 'пальмы', 'песок'], 'right_answer': 'солнце'},
    {'id': 1, 'question': 'Что является символом Копенгагена?',
     'answers': ['лебедь', 'кот в мешке', 'русалочка', 'лев'], 'right_answer': 'русалочка'},
    {'id': 2, 'question': 'Высота Останкинской башни ... метров',
     'answers': ['120', '540', '360', '610'], 'right_answer': '540'},
    {'id': 3, 'question': 'Какая птица олицетворяет символ мудрости?',
     'answers': ['сова', 'жар-птица', 'орёл', 'птица феникс'], 'right_answer': 'сова'},
    {'id': 4, 'question': 'Народное собрание в древней и средневековой Руси?',
     'answers': ['сходка', 'вече', 'базар', 'дума'], 'right_answer': 'вече'},
    {'id': 5, 'question': 'Самый большой материк на Земле?',
     'answers': ['Европа', 'Австралия', 'Азия', 'Антарктида'], 'right_answer': 'Азия'}
]

""""
настройка для обхода блокировки Telegram
#telebot.apihelper.proxy = {'https': 'socks5://stepik.akentev.com:1080'}

простой возврат сообщения пользователя
@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, message.text)
"""


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    """
    Диспетчер перехвата сообщений игрока
    :param message: сообщение игрока
    :return: вызов необходимого обработчика с учетом статуса игрока в дереве вопросов
    """
    user_id = message.from_user.id

    user_state = user_states.get(user_id, BASE_STATE)
    #    user_state = user_states.get(user_id, NEW_USER)

    if user_id not in bot_users:
        bot_users.append(user_id)
    if user_id not in user_results:
        user_results[user_id] = [0, 0]
    if user_id not in user_complex:
        user_complex[user_id] = 0


    if user_state == NEW_USER:
        handler_new_member(message)
    elif user_state == BASE_STATE:
        base_handler(message)
    elif user_state == ASK_QUESTION_STATE:
        ask_question(message)
    else:
        bot.reply_to(message, ANSWER_BASE)

    # def new_user_handler(message):
    """
    Обработка входа нового участника игры
    :param message: сообщение игрока
    :return: Приветствие игрока, перевод в статус BASE_STATE
    """


@bot.message_handler(content_types=["new_chat_members"])
def handler_new_member(message):
    #    user_name = message.new_chat_member.first_name
    #    bot.send_message(message.chat.id, "Добро пожаловать, {0}!".format(user_name))
    print('new member')
    #    print(bot.get_chat_member())
    bot.send_message(message.chat.id, "Добро пожаловать")
    user_states[message.from_user.id] = BASE_STATE

    user_id = message.from_user.id
    if message.from_user.first_name is not None:
        u_name = str(message.from_user.first_name)
    else:
        u_name = 'Незнакомец(ка)'
    mess = 'Привет, ' + u_name + '!\nЭто бот-игра "Кто хочет стать миллионером"\n' + \
           'Если хочешь поиграть, напиши: "давай вопрос"'
    bot.send_message(message, mess)
    user_states[user_id] = BASE_STATE
    print(bot_users)


def get_question(q_complex):
    response = requests.get(URL_QUESTIONS, params=q_complex).json()
    qes = response['question']
    ans = response['answers']
    print(ans)
    ans_ok = response['answers'][0]
    perm = permutations(ans)
    ans_dop = [list(el) for el in list(perm)]
    ans = random.choices(ans_dop)[0]
    print(ans)
    res = {'question': qes, 'answers': ans, 'right_answer': ans_ok}
    print(res)
    return res


def base_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = message.from_user.id
    if message.text.lower().strip() == '/start':
        bot.reply_to(message, 'Это бот-игра "Кто хочет стать миллионером"' + '\n' + \
                     'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in GREETINGS:
        if message.from_user.first_name is not None:
            bot.reply_to(message, 'Ну, Привет, ' + str(message.from_user.first_name) + '!\n' + \
                         'Если хочешь поиграть, напиши: "давай вопрос"')
        else:
            bot.reply_to(message, 'Ну, Привет, Незнакомец(ка)!' + '\n' + \
                         'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in CANCEL_QUESTION:
        bot.reply_to(message, str(message.from_user.first_name) + ' уже нет сил ??? :(' + '\n' + \
                     'Результат игры: Твоих Побед - ' + str(user_results[user_id][1]) + \
                     '; Поражений - ' + str(user_results[user_id][0]) + \
                     '\nКак надумаешь - возвращайся.\nЯ буду ждать тебя... :)')
    elif message.text.lower().strip() in SHOW_RESULTS:
        bot.reply_to(message, 'Текущий счет: Твоих Побед - ' + str(user_results[user_id][1]) + \
                     '; Поражений - ' + str(user_results[user_id][0]))
    elif message.text.lower().strip() in GO_TO_QUESTION or message.text.lower().strip() in QUESTION_LEVEL:
        # проверка того, что это первый вопрос в сессии. Предлагаем выбрать уровень сложности
        if message.text.lower().strip() == QUESTION_LEVEL[0]:
            user_complex[user_id] = 1
        if message.text.lower().strip() == QUESTION_LEVEL[1]:
            user_complex[user_id] = 2
        if message.text.lower().strip() == QUESTION_LEVEL[2]:
            user_complex[user_id] = 3

        if user_complex[user_id] == 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(QUESTION_LEVEL[0]),
                         types.KeyboardButton(QUESTION_LEVEL[1]),
                         types.KeyboardButton(QUESTION_LEVEL[2]))
            bot.reply_to(message, 'Выбери уровень сложности вопросов', reply_markup=keyboard)
        else:
            user_data[user_id] = get_question(str(user_complex[user_id]))
            print(user_data)
            #           user_data[user_id] = QUESTIONS[random.choice([id for id in range(len(QUESTIONS))])]

            #    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(user_data[user_id]['answers'][0]),
                         types.KeyboardButton(user_data[user_id]['answers'][1]),
                         types.KeyboardButton(user_data[user_id]['answers'][2]),
                         types.KeyboardButton(user_data[user_id]['answers'][3]))
            bot.reply_to(message, str(user_data[user_id]['question']) + '\nВыбери варианты ответов',
                         reply_markup=keyboard)
            user_states[message.from_user.id] = ASK_QUESTION_STATE
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Если хочешь поиграть, напиши: "давай вопрос"')


def ask_question(message):
    """
    Обработка ответов игрока на вопрос
    :param message: сообщение игрока - ответ на вопрос
    :return: Результат обработки ответа на вопрос
    """
    user_id = message.from_user.id
    if user_id not in user_faults:
        user_faults[user_id] = 0

    #    print(user_data)
    if (message.text.lower().strip() == user_data[user_id]['right_answer']) or (
            message.text.lower().strip().capitalize() == user_data[user_id]['right_answer']):
        bot.send_chat_action(user_id, 'typing')
        time.sleep(1)
        bot.reply_to(message, 'Правильно!' + '\n' + \
                     'Если хочешь сыграть ещё, напиши: "да", если уже устал, напиши: "нет"',
                     reply_markup=types.ReplyKeyboardRemove())
        user_faults[user_id] = 0
        user_results[user_id][1] += 1
        user_states[message.from_user.id] = BASE_STATE
    elif (message.text.lower().strip() in user_data[user_id]['answers']) or (
            message.text.lower().strip().capitalize() in user_data[user_id]['answers']):
        user_faults[user_id] += 1
        if (user_faults[user_id] == 2):
            bot.reply_to(message, 'Неправильно... Увы, ты проиграл :(' + '\n' + \
                         'Если ты готов победить, напиши: "да", если уже устал, напиши: "нет"',
                         reply_markup=types.ReplyKeyboardRemove())
            user_faults[user_id] = 0
            user_results[user_id][0] += 1
            user_states[message.from_user.id] = BASE_STATE
        else:
            bot.send_chat_action(user_id, 'typing')
            time.sleep(1)
            bot.reply_to(message, 'Неправильно :( У тебя ещё одна попытка')
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Выбери один из вариантов ответов')


if __name__ == '__main__':
    bot.polling()
