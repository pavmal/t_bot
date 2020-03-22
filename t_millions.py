import telebot
token = '1064357091:AAHg0oamqbvoDmRL7Nu7gGEZvi_W7aeHSjg'

bot = telebot.TeleBot(token)
result = {'victories': 0, 'defeats': 0}
""""
настройка для обхода блокировки Telegram
#telebot.apihelper.proxy = {'https': 'socks5://stepik.akentev.com:1080'}

простой возврат сообщения пользователя
@bot.message_handler(func=lambda message: True)
def echo(message):
    bot.reply_to(message, message.text)
"""

@bot.message_handler(func=lambda message: True)
def echo(message):
    if message.text == '/start':
        bot.reply_to(message,'Это бот-игра в "Кто хочет стать миллионером"')
    elif message.text == 'Привет':
#        bot.reply_to(message, 'Ну привет! ' + message.from_user.user_name)
        bot.reply_to(message, 'Ну привет!')
    elif message.text == 'Спроси меня вопрос':
        bot.reply_to(message, 'Какую площадь имеет клетка стандартной школьной тетрадки: 0,25; 1,00; 0,5; 1,25')
    elif message.text == '0,25':
        bot.reply_to(message, 'Правильно!')
        result['victories'] += 1
    elif message.text == '1,0':
        bot.reply_to(message, 'Неправильно :(')
        result['defeats'] += 1
    elif message.text == '1,25':
        bot.reply_to(message, 'Неправильно :(')
        result['defeats'] += 1
    elif message.text == '0,5':
        bot.reply_to(message, 'Неправильно :(')
        result['defeats'] += 1
    elif message.text == 'Покажи счёт':
        bot.reply_to(message, 'Текущий счет: Побед - '  + str(result['victories']) + \
                                            ' Поражений - ' + str(result['defeats']))
    else:
        bot.reply_to(message, 'Я тебя не понял :(')
#    else:
#        bot.reply_to(message, message.text)

bot.polling()