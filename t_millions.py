import telebot
from telebot import types
import random, time, os, json
import requests
import redis
import config
# from itertools import permutations

#bot = telebot.TeleBot(config.token)
bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
REDIS_URL = os.environ.get('REDIS_URL')
all_user_data = {}
#all_user_data_str = ''
# s = ''
# with open('temp_data.txt', 'r', encoding='utf-8') as f:
#     s = f.readline()
# all_user_data = json.loads(s)
# print(all_user_data)

def save_data(key, value):
#    data_str = '{"' + key + '": ' + json.dumps(all_user_data[key]) + '}'
#    all_user_data_str = json.dumps(all_user_data[key])
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        redis_db.set(key, value)
#    else:
#        all_user_data[key] = value
#        open('temp_data.txt', 'w', encoding='utf-8').write(data_str)
#    print(key, value)
#    print(all_user_data)

def load_data(key):
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        return redis_db.get(key)
    else:
#        s = json.load(open('temp_data.txt', 'r', encoding='utf-8'))
#        data = json.loads(s)
#        print(type(s), s)
        return all_user_data.get(key)


#IS_HEROKU = os.environ.get('HEROKU', False)



GREETINGS = ['hi', 'привет']
GO_TO_QUESTION = ['спроси меня вопрос', 'спроси меня', 'следущий вопрос', 'ещё', 'давай вопрос', 'да', '?', 'вопрос']
QUESTION_LEVEL = ['1 - разминочный', '2 - средний', '3 - для эрудитов']
CANCEL_QUESTION = ['не хочу', 'нет', 'надоело', 'достал', 'отвали']
SHOW_RESULTS = ['покажи счёт', 'какой счёт', 'результат игры', 'счет', 'счёт', 'итог']

ANSWER_BASE = 'Я тебя не понял :('
NEW_USER = 'new'
BASE_STATE = 'base'
ASK_QUESTION_STATE = 'ask_question'

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
    user_id = str(message.from_user.id)
    all_user_data[user_id] = load_data(user_id)
    print(all_user_data)
#    if user_id not in all_user_data:
    if all_user_data[user_id] == None:
        all_user_data[user_id] = {}
        all_user_data[user_id]['state'] = BASE_STATE
        all_user_data[user_id]['results'] = [0, 0]
        all_user_data[user_id]['faults'] = 0
        all_user_data[user_id]['complex'] = 0
        all_user_data[user_id]['questions'] = {}
#    else:
#        pass
#        all_user_data[user_id] = load_data(user_id)
#    print(all_user_data)

    if all_user_data[user_id]['state'] == NEW_USER:
        handler_new_member(message)
    elif all_user_data[user_id]['state'] == BASE_STATE:
        base_handler(message)
    elif all_user_data[user_id]['state'] == ASK_QUESTION_STATE:
        ask_question(message)
    else:
        bot.reply_to(message, ANSWER_BASE)
    #    photo_handler(message)
    #    sticker_handler(message)

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
    user_id = str(message.from_user.id)
    print('new member')
    #    print(bot.get_chat_member())
    bot.send_message(message.chat.id, "Добро пожаловать")
    all_user_data[user_id]['state'] = BASE_STATE

    if message.from_user.first_name is not None:
        u_name = str(message.from_user.first_name)
    else:
        u_name = 'Незнакомец(ка)'
    mess = 'Привет, ' + u_name + '!\nЭто бот-игра "Кто хочет стать миллионером"\n' + \
           'Если хочешь поиграть, напиши: "давай вопрос"'
    bot.send_message(message, mess)
    all_user_data[user_id]['state'] = BASE_STATE


@bot.message_handler(content_types=["photo"])
def photo_handler(message):
    #    bot.send_sticker(message.sticker.file_id)
    print(message.from_user.id, message.photo[-1].file_id)


#    bot.send_photo(message.from_user.id, message.photo[-1].file_id)

@bot.message_handler(content_types=["sticker"])
def sticker_handler(message):
    user_id = str(message.from_user.id)
    #    if user_results[user_id][1] == 1:
    if all_user_data[user_id]['results'][1] == 3:
        bot.send_message(message, 'Уже взяты подряд 3 вопроса!!!\nТак держать!')
        time.sleep(1)
        bot.send_sticker(message.from_user.id, config.STICK_URL_03)


def get_question(q_complex):
    response = requests.get(config.URL_QUESTIONS, params=q_complex).json()
    qes = response['question']
    ans = response['answers']
    print(ans)
    ans_ok = response['answers'][0]
    random.shuffle(ans)
    #    perm = permutations(ans)
    #    ans_dop = [list(el) for el in list(perm)]
    #    ans = random.choices(ans_dop)[0]
    print(ans)
    res = {'question': qes, 'answers': ans, 'right_answer': ans_ok}
    print(res)
    return res


def reward_winners(wins):
    stik_url = config.STICK_URL_00
    print(stik_url)
    if wins == 3:
        stik_url = config.STICK_URL_03
    if wins == 10:
        stik_url = config.STICK_URL_10
    if wins == 25:
        stik_url = config.STICK_URL_25
    return str(stik_url)


def base_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = str(message.from_user.id)
    if message.text.lower().strip() == '/start':
        bot.reply_to(message, 'Это бот-игра "Кто хочет стать миллионером"' + '\n' +
                     'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in GREETINGS:
        if message.from_user.first_name is not None:
            bot.reply_to(message, 'Ну, Привет, ' + str(message.from_user.first_name) + '!\n' +
                         'Если хочешь поиграть, напиши: "давай вопрос"')
        else:
            bot.reply_to(message, 'Ну, Привет, Незнакомец(ка)!' + '\n' +
                         'Если хочешь поиграть, напиши: "давай вопрос"')
    elif message.text.lower().strip() in CANCEL_QUESTION:
        bot.reply_to(message, str(message.from_user.first_name) + ' уже нет сил ??? :(' + '\n' +
                     'Результат игры: Твоих Побед - ' + str(all_user_data[user_id]['results'][1]) +
                     '; Поражений - ' + str(all_user_data[user_id]['results'][0]) +
                     '\nКак надумаешь - возвращайся.\nЯ буду ждать тебя... :)')
    elif message.text.lower().strip() in SHOW_RESULTS:
        bot.reply_to(message, 'Текущий счет: Твоих Побед - ' + str(all_user_data[user_id]['results'][1]) +
                     '; Поражений - ' + str(all_user_data[user_id]['results'][0]))
    elif message.text.lower().strip() in GO_TO_QUESTION or message.text.lower().strip() in QUESTION_LEVEL:
        # проверка того, что это первый вопрос в сессии. Предлагаем выбрать уровень сложности
        if message.text.lower().strip() == QUESTION_LEVEL[0]:
            all_user_data[user_id]['complex'] = 1
        if message.text.lower().strip() == QUESTION_LEVEL[1]:
            all_user_data[user_id]['complex'] = 2
        if message.text.lower().strip() == QUESTION_LEVEL[2]:
            all_user_data[user_id]['complex'] = 3

        if all_user_data[user_id]['complex'] == 0:
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(QUESTION_LEVEL[0]),
                         types.KeyboardButton(QUESTION_LEVEL[1]),
                         types.KeyboardButton(QUESTION_LEVEL[2]))
            bot.reply_to(message, 'Выбери уровень сложности вопросов', reply_markup=keyboard)
        else:
            all_user_data[user_id]['questions'] = get_question(str(all_user_data[user_id]['complex']))

            #    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(all_user_data[user_id]['questions']['answers'][0]),
                         types.KeyboardButton(all_user_data[user_id]['questions']['answers'][1]),
                         types.KeyboardButton(all_user_data[user_id]['questions']['answers'][2]),
                         types.KeyboardButton(all_user_data[user_id]['questions']['answers'][3]))
            bot.reply_to(message, str(all_user_data[user_id]['questions']['question']) + '\nВыбери варианты ответов',
                         reply_markup=keyboard)
            all_user_data[user_id]['state'] = ASK_QUESTION_STATE
            save_data(user_id, json.dumps(all_user_data[user_id]))
            print(all_user_data)
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Если хочешь поиграть, напиши: "давай вопрос"')


def ask_question(message):
    """
    Обработка ответов игрока на вопрос
    :param message: сообщение игрока - ответ на вопрос
    :return: Результат обработки ответа на вопрос
    """
    user_id = str(message.from_user.id)
    if (message.text.lower().strip() == (str(all_user_data[user_id]['questions']['right_answer']).lower().strip())):
        bot.send_chat_action(user_id, 'typing')
        time.sleep(1)
        all_user_data[user_id]['faults'] = 0
        all_user_data[user_id]['results'][1] += 1
        all_user_data[user_id]['state'] = BASE_STATE
        save_data(user_id, json.dumps(all_user_data[user_id]))
        # check for user reward
        if all_user_data[user_id]['results'][1] in [1, 3, 10, 25]:
            str_url = reward_winners(all_user_data[user_id]['results'][1])
            time.sleep(1)
            str_mess = 'Правильно! \nУже взяты подряд ' + str(
                all_user_data[user_id]['results'][1]) + ' вопросов!!!\nТак держать!'
            if all_user_data[user_id]['results'][1] == 25:
                str_mess = str_mess + '\nОбъявляю тебя ПОБЕДИТЕЛЕМ ИГРЫ !!!'
            bot.reply_to(message, str_mess)
            #            sti = open(str_url, 'rb')
            #            bot.send_sticker(message.from_user.id, sti)
            bot.send_sticker(message.from_user.id, str_url)
        #            bot.send_sticker(message.from_user.id, 'FILEID')
        else:
            bot.reply_to(message, 'Правильно! Молодец!!!')
        # general message for right answer
        bot.reply_to(message, 'Если хочешь сыграть ещё, напиши: "да", \nесли уже устал, напиши: "нет"',
                     reply_markup=types.ReplyKeyboardRemove())

    elif (message.text.lower().strip() in str(all_user_data[user_id]['questions']['answers']).lower().strip()):
        all_user_data[user_id]['faults'] += 1
        if (all_user_data[user_id]['faults'] == 2):
            bot.reply_to(message, 'Неправильно... Увы, ты проиграл :(' + '\n' +
                         'Если ты готов победить, напиши: "да", \nесли уже устал, напиши: "нет"',
                         reply_markup=types.ReplyKeyboardRemove())
            all_user_data[user_id]['faults'] = 0
            all_user_data[user_id]['results'][0] += 1
            # user_results[user_id][1] = 0  # обнуление выйгрышей N подряд вопросов
            all_user_data[user_id]['state'] = BASE_STATE
            save_data(user_id, json.dumps(all_user_data[user_id]))
        else:
            bot.send_chat_action(user_id, 'typing')
            time.sleep(1)
            bot.reply_to(message, 'Неправильно :( У тебя ещё одна попытка')
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Выбери один из вариантов ответов')
#    save_data('user_id')


if __name__ == '__main__':
    bot.polling()

