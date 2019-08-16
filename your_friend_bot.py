from friend_parser import FParser
import telebot
import time
from secret_token import TOKEN

settings = {
    'total': 0,
    'aim': 0,
    'currCommand': None,
    'start_time': 0,
    'is_stop': True,
    'age': '18',
    'key_words': ['Москва'],
    'links': [
        'https://vk.com/wall-26014521?own=1'
        ]
    }

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def starting(message):
    settings['is_stop'] = True
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row("/go", "/stop")
    user_markup.row("/status", "/settings")
    bot.send_message(message.from_user.id, 
"Привет. Это YourFriendBot. Я помогаю находить анкеты в\
    пабликах по ключевым словам, тебе остаётся только\
    настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n\
Ты можешь использовать следующие команды:\n\
    /go - начало новой сессии поиска\n\
    /stop - прекращение действующей сессии\n\
    /status - информация о текущей сесcии\n\
    /settings - информация о текущих настройках поиска\n\n\
Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n\
    /age - искомый минимальный возраст\n\
    /key_words - искомые ключевые слова\n\
    /links - ссылки в ВК, где будет поиск",
    reply_markup=user_markup)

@bot.message_handler(commands=['go'])
def com_go(message):
    if settings['is_stop'] == True:
        if settings['links'] != None:
            bot.send_message(message.from_user.id, 
            "Отлично. Бот начал новый поиск с настройками:\n" +
            "Минимальный возраст: " + ('любой' if settings['age'] == None else str(settings['age'])) + 
            "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
            "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

            #фиксируем время начала поиска
            settings['start_time'] = time.time()

            #бесконечный мониторинг, пока не остановят внешней командой stop
            settings['is_stop'] = False
            fParser = FParser(settings)
            while settings['is_stop'] == False:
                if (settings['is_stop'] == True):
                    break
                data = fParser.do_parse()

                settings['total'] += data['total']
                settings['aim'] += data['aim']
                if (data != None): 
                    for messg in data['messages']:
                        bot.send_message(message.from_user.id, messg)
                time.sleep(5)
        else:
            bot.send_message(message.from_user.id, "Чтобы начать новый поиск," +
            "необходимо добавить хотя бы 1 страницу для поиска.")
    else:
        bot.send_message(message.from_user.id, "Чтобы начать новый поиск," +
        "остановите текущий поиск командой /stop")

@bot.message_handler(commands=['stop'])
def com_stoping(message):
    if settings['is_stop'] == True:
        bot.send_message(message.from_user.id, "Бот уже остановлен и ждёт новых указаний.")   
    else:
        settings['is_stop'] = True
        bot.send_message(message.from_user.id, "Поиск прекращён. Бот остановлен.")   

@bot.message_handler(commands=['status'])
def com_status(message):
    if settings['is_stop'] == True:
        bot.send_message(message.from_user.id, 
        "Поиск не осуществляется.\nТекущие настройки:" +
        "\nМинимальный возраст: " + ('любой' if settings['age'] == None else str(settings['age'])) + 
        "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
        "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )
    else:
        tot_time = time.time() - settings['start_time']
        seconds = tot_time % 60
        minutes = (tot_time // 60) % 60
        hours = (tot_time // 3600) % 24
        days = (tot_time // (3600 * 24))
        bot.send_message(message.from_user.id,
        "Бот работает уже: " + str(tot_time) + " секунд, то есть уже: " +
        "\nДней: " + str(int(days)) + 
        "\nЧасов: " + str(int(hours)) +
        "\nМинут: " + str(int(minutes)) + 
        "\nСекунд: " + str(int(seconds)) +
        "\n\nЗа это время было обработано:" + 
        "\nНовых анкет: " + str(settings['total']) +
        "\nПодходящих анкет: " + str(settings['aim']))


@bot.message_handler(commands=['settings'])
def com_settings(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    if settings['is_stop'] == True:
        user_markup.row("/age", "/key_words", "/links")
        user_markup.row("/tomenu")
        bot.send_message(message.from_user.id,
        "Вы можете настроить критерии поиска следующими командами:\n \
        /age - искомый минимальный возраст\n \
        /key_words - искомые ключевые слова\n \
        /links - ссылки в ВК, где будет поиск",
        reply_markup=user_markup)
    else:
        bot.send_message(message.from_user.id, 
        "Чтобы изменить настройки, сначала необходимо " +
        "остановить текущий сеанс поиска командой /stop")

@bot.message_handler(commands=['tomenu'])
def tomenu(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
    user_markup.row("/go", "/stop")
    user_markup.row("/status", "/settings")
    bot.send_message(message.from_user.id, 'Настройки учтены', reply_markup=user_markup)

@bot.message_handler(commands=['age'])
def com_age(message):
    settings['currCommand'] = 'age'
    bot.send_message(message.from_user.id, "Введите минимальный возраст, по которому будут подбираться анкеты:")     

@bot.message_handler(commands=['key_words'])
def com_key_words(message):
    settings['currCommand'] = 'key_words'
    bot.send_message(message.from_user.id, "Введите через ПРОБЕЛ ключевые слова, " +
    "по которым будут подбираться анкеты. Например: Москва тян")

@bot.message_handler(commands=['links'])
def com_links(message):
    settings['currCommand'] = 'links'
    bot.send_message(message.from_user.id, "Введите через ПРОБЕЛ ссылки, " +
    "по которым будут подбираться анкеты. \nВАЖНО: ссылка должна быть именно на стену сообщества, например 'vk.com/wall-ID_СООБЩЕСТВА'")  

@bot.message_handler(content_types=['text'])
def calcAnyText(message):
    if settings['currCommand'] == 'age':
        age = -1
        try:
            age = int(message.text)
        except:
            bot.send_message(message.from_user.id, 'Введён некорректный возраст!')
        
        if (age not in range(1, 99)):
            bot.send_message(message.from_user.id, 'Пожалуйства, введите корретное число от 1 до 99')
        else:
            bot.send_message(message.from_user.id, 'Принято. Новый минимальный возраст для поиска: ' + str(age))
            settings['age'] = age
    elif settings['currCommand'] == 'key_words':
        bot.send_message(message.from_user.id, 'Принято. Новые ключевые слова для поиска: ' + message.text)
        settings['key_words'] = message.text.split(' ')
    elif settings['currCommand'] == 'links':
        bot.send_message(message.from_user.id, 'Принято. Новые ссылки для поиска: ' + message.text)
        settings['links'] = message.text.split(' ')
    else:
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row("/go", "/stop")
        user_markup.row("/status", "/settings")
        bot.send_message(message.from_user.id, 
    "Привет. Это YourFriendBot. Я помогаю находить анкеты в\
        пабликах по ключевым словам, тебе остаётся только\
        настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n\
    Ты можешь использовать следующие команды:\n\
        /go - начало новой сессии поиска\n\
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
        time.sleep(10)