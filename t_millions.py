import telebot
from telebot import types
import random, time, os, json
import requests
import redis
import config

# from PIL import Image
# from itertools import permutations

# bot = telebot.TeleBot(config.token)
bot = telebot.TeleBot(os.environ['BOT_TOKEN'])
REDIS_URL = os.environ.get('REDIS_URL')
all_user_data = {}

GREETINGS = ['hi', 'привет']
GO_TO_QUESTION = ['спроси меня вопрос', 'спроси меня', 'следущий вопрос', 'ещё', 'давай вопрос', 'да', '?', 'вопрос']
QUESTION_LEVEL = ['выбери уровень сложности вопросов', '1 - разминочный', '2 - средний', '3 - для эрудитов']
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


def save_data(key, value):
    """
    Сохранение данных по игроку в базу redis
    """
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        redis_db.set(key, value)


def load_data(key):
    """
    Загрузка сохраненных данных по игроку
    :param key: id игрока в базе
    :return: строка со словарем
    """
    if REDIS_URL:
        redis_db = redis.from_url(REDIS_URL)
        if redis_db.get(key):
            return redis_db.get(key).decode("utf-8")
    else:
        return all_user_data.get(key)


@bot.message_handler(func=lambda message: True)
def dispatcher(message):
    """
    Диспетчер перехвата сообщений игрока
    :param message: сообщение игрока
    :return: вызов необходимого обработчика с учетом статуса игрока в дереве вопросов
    """
    if message.text.lower().strip() == '/start':
        bot.reply_to(message, 'Это бот-игра "Кто хочет стать миллионером"' + '\n' +
                     'Если хочешь поиграть, напиши: "давай вопрос" или "?"')

    user_id = str(message.from_user.id)
    if REDIS_URL:  # если подключена база redis
        val_str = load_data(user_id)
        if val_str:
            all_user_data[str(user_id)] = json.loads(val_str)

    if (user_id not in all_user_data) or (all_user_data[user_id] == None):
        all_user_data[user_id] = {}
        all_user_data[user_id]['state'] = BASE_STATE
        all_user_data[user_id]['results'] = [0, 0]
        all_user_data[user_id]['faults'] = 0
        all_user_data[user_id]['complex'] = 0
        all_user_data[user_id]['questions'] = {}

    print('Состояние до вопроса:\n{}'.format(all_user_data))
    if all_user_data[user_id]['state'] == NEW_USER:
        handler_new_member(message)
    elif all_user_data[user_id]['state'] == BASE_STATE:
        base_handler(message)
    elif all_user_data[user_id]['state'] == ASK_QUESTION_STATE:
        ask_question(message)
    else:
        bot.reply_to(message, ANSWER_BASE)
    """ Оставил для возможной обработки фото и стикетов """
    #    photo_handler(message)
    #sticker_handler(message)

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

    print(message.sticker.file_id)
    bot.send_sticker(message.from_user.id, message.sticker.file_id)
#    config.OLAF_X = message.sticker.file_id
#    config.OLAF_X = 'CAACAgIAAxkBAAIBqV6a_wVmXbJkxJK_SY9kJrzdEIzAAAK_AAMrXlMLZByzdc6EyDkYBA'
#    print(config.OLAF_X)
#    bot.send_sticker(message.from_user.id, config.OLAF_X)


def get_question(q_complex):
    response = requests.get(config.URL_QUESTIONS, params=q_complex).json()
    qes = response['question']
    ans = response['answers']
    ans_ok = response['answers'][0]
    random.shuffle(ans)
    #    perm = permutations(ans)
    #    ans_dop = [list(el) for el in list(perm)]
    #    ans = random.choices(ans_dop)[0]
    res = {'question': qes, 'answers': ans, 'right_answer': ans_ok}
    print('Вопрос:\n{}'.format(res))
    return res


def reward_winners(wins):
    """
    Выбор картинки в зависимости от количества побед игрока
    :param wins: количество побед
    :return: ссылка на картинку
    """
    stik_url = config.STICK_URL_00
    if wins == 3:
        stik_url = config.STICK_URL_03
    if wins == 10:
        stik_url = config.STICK_URL_10
    if wins == 25:
        stik_url = config.STICK_URL_25
    return str(stik_url)


def olaf_reward_winners(wins):
    """
    Выбор стика в зависимости от количества побед игрока
    :param wins: количество побед
    :return: ссылка на картинку
    """
    olaf_id = config.OLAF_00
    if wins == 3:
        olaf_id = config.OLAF_03
    if wins == 10:
        olaf_id = config.OLAF_10
    if wins == 25:
        olaf_id = config.OLAF_25
    return olaf_id


def base_handler(message):
    """
    Обработка сообщений на базовом уровне (вход пользователя или после результата игры)
    :param message: сообщение игрока
    :return: Ответ игроку в зависимости от обработки сообщения
    """
    user_id = str(message.from_user.id)
    result_mess = 'Текущий счет для выбранного уровня:\n' \
                  'Твоих Побед - {}\n' \
                  'Поражений - {}'.format(str(all_user_data[user_id]['results'][1]),
                                          str(all_user_data[user_id]['results'][0]))

    if message.text.lower().strip() == '/start':
        pass  # обрабатывается в процедуре диспетчера
    elif message.text.lower().strip() in GREETINGS:
        bot.reply_to(message, 'Ну, Привет, {}!\nЕсли хочешь поиграть, напиши: "давай вопрос" или "?"'.format(
            str(message.from_user.first_name)))

    elif message.text.lower().strip() in CANCEL_QUESTION:
        bot.reply_to(message, str(message.from_user.first_name) + ' уже нет сил ??? :(' + '\n' + result_mess +
                     '\nКак надумаешь - возвращайся.\nЯ буду ждать тебя... :)')
        bot.send_sticker(message.from_user.id, config.OLAF_00)

    elif message.text.lower().strip() in SHOW_RESULTS:
        bot.reply_to(message, result_mess)

    elif message.text.lower().strip() in GO_TO_QUESTION or message.text.lower().strip() in QUESTION_LEVEL:
        # проверка того, что это первый вопрос в сессии. Предлагаем выбрать уровень сложности
        if message.text.lower().strip() == QUESTION_LEVEL[1]:
            all_user_data[user_id]['complex'] = 1
        if message.text.lower().strip() == QUESTION_LEVEL[2]:
            all_user_data[user_id]['complex'] = 2
        if message.text.lower().strip() == QUESTION_LEVEL[3]:
            all_user_data[user_id]['complex'] = 3

        if all_user_data[user_id]['complex'] == 0 or message.text.lower().strip() == QUESTION_LEVEL[0]:
            all_user_data[user_id]['results'][0] = 0  # обнуляем число поражений
            all_user_data[user_id]['results'][1] = 0  # обнуляем число побед
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
            keyboard.add(types.KeyboardButton(QUESTION_LEVEL[1]),
                         types.KeyboardButton(QUESTION_LEVEL[2]),
                         types.KeyboardButton(QUESTION_LEVEL[3]))
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
            print('Состояние после выбора вопроса:\n{}'.format(all_user_data))
    else:
        bot.reply_to(message, ANSWER_BASE + '\n' + 'Если хочешь поиграть, напиши: "давай вопрос"')

    save_data(user_id, json.dumps(all_user_data[user_id]))


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
        if all_user_data[user_id]['results'][1] in [3, 10, 25]:
            time.sleep(1)
            str_mess = 'Правильно! \nУже взяты подряд ' + str(
                all_user_data[user_id]['results'][1]) + ' вопросов!!!\nТак держать!'
            if all_user_data[user_id]['results'][1] == 25:
                str_mess = str_mess + '\nОбъявляю тебя ПОБЕДИТЕЛЕМ ИГРЫ !!!'
            bot.reply_to(message, str_mess, reply_markup=types.ReplyKeyboardRemove())
            # str_url = reward_winners(all_user_data[user_id]['results'][1])  # ссылки на кота Кузю
            olaf_id = olaf_reward_winners(all_user_data[user_id]['results'][1])
            bot.send_sticker(message.from_user.id, olaf_id)
        #     bot.send_sticker(message.from_user.id, 'FILEID')
        else:
            bot.reply_to(message, 'Правильно! Молодец!!!', reply_markup=types.ReplyKeyboardRemove())

    elif (message.text.lower().strip() in str(all_user_data[user_id]['questions']['answers']).lower().strip()):
        all_user_data[user_id]['faults'] += 1
        if (all_user_data[user_id]['faults'] == 2):
            bot.reply_to(message, 'Неправильно... Увы, ты проиграл :(', reply_markup=types.ReplyKeyboardRemove())
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
    print('Состояние после ответа на вопрос:\n{}'.format(all_user_data))
    save_data(user_id, json.dumps(all_user_data[user_id]))

    #   если ошибочных ответов ноль, то игрок или выйграл или проиграл.
    #   Предлагаем продолжить, завершить игру или выбрать сложность вопросов
    if all_user_data[user_id]['faults'] == 0:
        keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
        keyboard.add(types.KeyboardButton('Да'),
                     types.KeyboardButton('Нет'),
                     types.KeyboardButton(QUESTION_LEVEL[0].capitalize()))
        bot.reply_to(message, 'Продолжаем играть ?', reply_markup=keyboard)


if __name__ == '__main__':
#    if REDIS_URL:
#        redis_db = redis.from_url(REDIS_URL)
#        redis_db.delete('409088886')
    bot.polling()
