import telebot
import random

from config import token

# token = '1064357077:AAHg0oamqbvoDmRL7Nu7gGEZvi_W7aeHSjg'

bot = telebot.TeleBot(token)

user_states = {}
user_results = {}
user_faults = {}

GREETINGS = ['hi', 'привет']
GO_TO_QUESTION = ['спроси меня вопрос', 'спроси меня', 'следущий вопрос', 'ещё', 'давай вопрос', 'да']
CANCEL_QUESTION = ['не хочу', 'нет', 'надоело', 'достал', 'отвали']
SHOW_RESULTS = ['покажи счёт', 'какой счёт', 'результат игры', 'счет', 'счёт']

ANSWER_BASE = 'Я тебя не понял :('
BASE_STATE = 'base'
ASK_QUESTION_STATE = 'ask_question'

global QUESTION_ID
QUESTION_ID = 0
global VAR_ANSWERS
VAR_ANSWERS = []
global ANS_RIGHT
ANS_RIGHT = ''
global QUESTIONS
QUESTIONS = [
    {'id': 1, 'question': 'Туристы, приезжающие на Майорку, обязаны заплатить налог на …?',
     'answers': ['солнце', 'купальник', 'пальмы', 'песок'], 'right_answer': 'солнце'},
    {'id': 2, 'question': 'что является символом Копенгагена?',
     'answers': ['лебедь', 'кот в мешке', 'русалочка', 'лев'], 'right_answer': 'русалочка'},
    {'id': 3, 'question': 'Высота Останкинской башни ... метров',
     'answers': ['120', '540', '360', '610'], 'right_answer': '540'},
    {'id': 4, 'question': 'Какая птица олицетворяет символ мудрости?',
     'answers': ['сова', 'жар-птица', 'орёл', 'птица феникс'], 'right_answer': 'сова'},
    {'id': 5, 'question': 'Народное собрание в древней и средневековой Руси?',
     'answers': ['сходка', 'вече', 'базар', 'дума'], 'right_answer': 'вече'}
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
    if user_id not in user_results:
        user_results[user_id] = [0, 0]

    if user_state == BASE_STATE:
        base_handler(message)
    elif user_state == ASK_QUESTION_STATE:
        ask_question(message)
    else:
        bot.reply_to(message, ANSWER_BASE)


def base_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = message.from_user.id
    if message.text.lower().strip() == '/start':
        bot.reply_to(message, 'Это бот-игра в "Кто хочет стать миллионером"' + '\n' + \
                     'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in GREETINGS:
        bot.reply_to(message, 'Ну, Привет! ' + str(message.from_user.first_name) + '\n' + \
                     'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in CANCEL_QUESTION:
        bot.reply_to(message, str(message.from_user.first_name) + ' уже нет сил ??? :(' + '\n' + \
                     'Как надумаешь - возвращайся. Я буду ждать вечно... :)')
    elif message.text.lower().strip() in SHOW_RESULTS:
        bot.reply_to(message, 'Текущий счет: Твоих Побед - ' + str(user_results[user_id][1]) + \
                     '; Поражений - ' + str(user_results[user_id][0]))
    elif message.text.lower().strip() in GO_TO_QUESTION:
        global QUESTION_ID
        QUESTION_ID = random.choice([id for id in range(1, len(QUESTIONS))])
        global VAR_ANSWERS
        VAR_ANSWERS = QUESTIONS[QUESTION_ID]['answers']
        global ANS_RIGHT
        ANS_RIGHT = QUESTIONS[QUESTION_ID]['right_answer']
        print(QUESTION_ID, VAR_ANSWERS, ANS_RIGHT)
        bot.reply_to(message, str(QUESTIONS[QUESTION_ID]['question']) + ': ' + str(QUESTIONS[QUESTION_ID]['answers']))
        # bot.reply_to(message, 'Какую площадь имеет клетка стандартной школьной тетрадки: 0,25; 1,0; 0,5; 1,25')
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
    print(QUESTION_ID, VAR_ANSWERS, ANS_RIGHT)
    print(message.text.lower().strip(), ANS_RIGHT)
    if (message.text.lower().strip() == ANS_RIGHT): # '0,25':
        bot.reply_to(message, 'Правильно!' + '\n' + \
                     'Если хочешь сыграть ещё, напиши: "да", если уже устал, напиши: "нет"')
        user_faults[user_id] = 0
        user_results[user_id][1] += 1
        user_states[message.from_user.id] = BASE_STATE
    elif (message.text.lower().strip() in VAR_ANSWERS):
    # elif (message.text.lower().strip() == '1,0') or (message.text.lower().strip() == '1,25') \
    #         or (message.text.lower().strip() == '0,5'):
        user_faults[user_id] += 1
        if (user_faults[user_id] == 2):
            bot.reply_to(message, 'Неправильно... Увы, ты проиграл :(' + '\n' + \
                         'Если ты готов победить, напиши: "да", если уже устал, напиши: "нет"')
            user_faults[user_id] = 0
            user_results[user_id][0] += 1
            user_states[message.from_user.id] = BASE_STATE
        else:
            bot.reply_to(message, 'Неправильно :( У тебя ещё одна попытка')
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Выбери один из вариантов ответов')


if __name__ == '__main__':
    bot.polling()
