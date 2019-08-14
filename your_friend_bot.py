import friend_finder
import telebot
import time

settings = {
    'start_time': None,
    'is_stop': True,
    'age': '18',
    'key_words': ['Москва'],
    'links': [
        'https://vk.com/wall-78855837?own=1'
        #'https://vk.com/wall-108037201?own=1',
        #'https://vk.com/topic-12125584_27005921?offset=600'
        ]
    }

TOKEN = '444'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def starting(message):
    settings['is_stop'] = True
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row("/new", "/stop")
    user_markup.row("/status", "/settings")
    bot.send_message(message.from_user.id, 
    "Привет. Это Your Friend BOT.",
    reply_markup=user_markup
    )

@bot.message_handler(commands=['new'])
def new(message):
    if settings['is_stop'] == True:
        if settings['links'] != None:
            bot.send_message(message.from_user.id, 
            "Отлично. Бот начал новый поиск с настройками:\n" +
            "Минимальный возраст: " + ('любой' if settings['age'] == None else settings['age']) + 
            "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
            "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

            settings['is_stop'] = False
            messages = friend_finder.parse(settings)
            if (messages != None): #TODO сделать бскончный цикл чтобы не мешал работе но постоянно вызывал метод parse
                for messg in messages:
                    bot.send_message(message.from_user.id, messg)
            else:
                bot.send_message(message.from_user.id, "Ничего...")
        else:
            bot.send_message(message.from_user.id, "Чтобы начать новый поиск," +
            "необходимо добавить хотя бы 1 страницу для поиска.")
    else:
        bot.send_message(message.from_user.id, "Чтобы начать новый поиск," +
        "остановите текущий поиск командой /stop")

@bot.message_handler(commands=['stop'])
def stopingg(message):
    settings['is_stop'] = True
    bot.send_message(message.from_user.id, "Поиск прекращён. Бот остановлен.")   

@bot.message_handler(commands=['status'])
def status(message):
    if settings['is_stop'] == True:
        bot.send_message(message.from_user.id, 
        "Поиск не осуществляется. Текущие настройки:\n" +
        "Минимальный возраст: " + ('любой' if settings['age'] == None else settings['age']) + 
        "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
        "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

@bot.message_handler(commands=['settings'])
def setings(message):
    bot.send_message(message.from_user.id, "Поиск прекращён. Бот остановлен.")  

@bot.message_handler(content_types=['text'])
def setSettings(message):
    bot.send_message(message.from_user.id, 
"Привет. Это YourFriendBot. Я помогаю находить анкеты в\
    пабликах по ключевым словам, тебе остаётся только\
    настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n\
Ты можешь исппользовать следующие команды:\n\
    /new - начало новой сессии поиска\n\
    /stop - прекращение действующей сессии\n\
    /status - информация о текущей сесcии\n\
    /settings - информация о текущих настройках поиска\n\n\
Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n\
    /age - искомый минимальный возраст\n\
    /key_words - искомые ключевые слова\n\
    /links - ссылки в ВК, где будет поиск"
    )

bot.polling(timeout=10)