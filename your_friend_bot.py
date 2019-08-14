import friend_parser
import telebot
import time

settings = {
    'currCommand': None,
    'start_time': None,
    'is_stop': True,
    'age': '18',
    'key_words': ['Москва'],
    'links': [
        'https://vk.com/wall-78855837?own=1',
        'https://vk.com/wall-108037201?own=1',
        #'https://vk.com/topic-12125584_27005921?offset=600'
        ]
    }

TOKEN = '816487038:AAHvdUNJxvOlEKEaBthkDVMcHdGGsyrfVd0'
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def starting(message):
    settings['is_stop'] = True
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row("/new", "/stop")
    user_markup.row("/status", "/settings")
    bot.send_message(message.from_user.id, 
"Привет. Это YourFriendBot. Я помогаю находить анкеты в\
    пабликах по ключевым словам, тебе остаётся только\
    настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n\
Ты можешь использовать следующие команды:\n\
    /new - начало новой сессии поиска\n\
    /stop - прекращение действующей сессии\n\
    /status - информация о текущей сесcии\n\
    /settings - информация о текущих настройках поиска\n\n\
Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n\
    /age - искомый минимальный возраст\n\
    /key_words - искомые ключевые слова\n\
    /links - ссылки в ВК, где будет поиск",
    reply_markup=user_markup)

@bot.message_handler(commands=['new'])
def com_new(message):
    if settings['is_stop'] == True:
        if settings['links'] != None:
            bot.send_message(message.from_user.id, 
            "Отлично. Бот начал новый поиск с настройками:\n" +
            "Минимальный возраст: " + ('любой' if settings['age'] == None else str(settings['age'])) + 
            "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
            "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

            settings['is_stop'] = False
            messages = friend_parser.parse(settings)
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
def com_stoping(message):
    settings['is_stop'] = True
    bot.send_message(message.from_user.id, "Поиск прекращён. Бот остановлен.")   

@bot.message_handler(commands=['status'])
def com_status(message):
    if settings['is_stop'] == True:
        bot.send_message(message.from_user.id, 
        "Поиск не осуществляется. Текущие настройки:\n" +
        "Минимальный возраст: " + ('любой' if settings['age'] == None else str(settings['age'])) + 
        "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
        "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

@bot.message_handler(commands=['settings'])
def com_settings(message):
    if settings['is_stop'] == True:
        bot.send_message(message.from_user.id, "Поиск прекращён. Бот остановлен.")
    else:
        bot.send_message(message.from_user.id, "Чтобы изменить настройки, сначала необходимо " +
        "остановить текущий сеанс поиска командой /stop")

@bot.message_handler(commands=['age'])
def com_age(message):
    settings['currCommand'] = 'age'
    bot.send_message(message.from_user.id, "Введите минимальный возраст, по которому будут подбираться анкеты:")     

@bot.message_handler(commands=['key_words'])
def com_key_words(message):
    settings['currCommand'] = 'key_words'
    bot.send_message(message.from_user.id, "Введите через запятую ключевые слова, " +
    "по которым будут подбираться анкеты. Например: Москва, тян")

@bot.message_handler(commands=['links'])
def com_links(message):
    settings['currCommand'] = 'links'
    bot.send_message(message.from_user.id, "Введите через запятую ссылки, " +
    "по которым будут подбираться анкеты")  

@bot.message_handler(content_types=['text'])
def calcAnyText(message):
    if settings['currCommand'] == 'age':
        age = -1
        try:
            age = int(message.text)
        except:
            bot.send_message(message.from_user.id, 'Введён некорректный возраст!')
        
        if (age not in range(0, 99)):
            bot.send_message(message.from_user.id, 'Пожалуйства, введите корретное число от 0 до 99')
        else:
            bot.send_message(message.from_user.id, 'Принято. Новый минимальный возраст для поиска: ' + str(age))
            settings['age'] = age
    elif settings['currCommand'] == 'key_words':
        bot.send_message(message.from_user.id, 'Принято. Новые ключевые слова для поиска: ' + message.text)
        settings['key_words'] = message.text.replace(' ', '').split(',')
    elif settings['currCommand'] == 'links':
        bot.send_message(message.from_user.id, 'Принято. Новые ссылка для поиска: ' + message.text)
        settings['links'] = message.text.replace(' ', '').split(',')
    else:
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row("/new", "/stop")
        user_markup.row("/status", "/settings")
        bot.send_message(message.from_user.id, 
    "Привет. Это YourFriendBot. Я помогаю находить анкеты в\
        пабликах по ключевым словам, тебе остаётся только\
        настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n\
    Ты можешь использовать следующие команды:\n\
        /new - начало новой сессии поиска\n\
        /stop - прекращение действующей сессии\n\
        /status - информация о текущей сесcии\n\
        /settings - информация о текущих настройках поиска\n\n\
    Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n\
        /age - искомый минимальный возраст\n\
        /key_words - искомые ключевые слова\n\
        /links - ссылки в ВК, где будет поиск",
        reply_markup=user_markup)
    
    settings['currCommand'] = None


while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print('Some error: ' + str(e))
        time.sleep(5)