from friend_parser import FParser
import telebot
import time
import json
import threading
from secret_token import TOKEN
import logging

def saveSetts(settings): 
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=4)

def start():

    bot = telebot.TeleBot(TOKEN)    

    @bot.message_handler(commands=['start'])
    def starting(message):
        settings['id'] = message.from_user.id
        settings['is_stop'] = True
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        user_markup.row("/go", "/stop")
        user_markup.row("/status", "/settings")
        bot.send_message(message.from_user.id, 
                        "Привет. Это YourFriendBot. Я помогаю находить анкеты в" + 
                        "пабликах по ключевым словам, тебе остаётся только" +
                        "настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n" +
                        "Ты можешь использовать следующие команды:\n" +
                        "\t/go - начало новой сессии поиска\n" +
                        "\t/stop - прекращение действующей сессии\n" +
                        "\t/status - информация о текущей сесcии\n" +
                        "\t/settings - информация о текущих настройках поиска\n\n" +
                        "Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n" +
                        "\t/age - искомый минимальный возраст\n" +
                        "\t/key_words - искомые ключевые слова\n" +
                        "\t/links - ссылки в ВК, где будет поиск",
                        reply_markup=user_markup)

    @bot.message_handler(commands=['go'])
    def com_go(message):
        if settings['is_stop'] == True or settings['currCommand'] == 'restart':
            if settings['links'] != None:
                #при restart в получаем id пользователя из настроек
                user_id = settings['id']
                if settings['currCommand'] != 'restart':
                    settings['id'] = message.from_user.id
                    user_id = message.from_user.id

                    bot.send_message(user_id, 
                                    "Отлично. Бот начал новый поиск с настройками:\n" +
                                    "Минимальный возраст: " + ('любой' if settings['age'] == None else str(settings['age'])) + 
                                    "\nКлючевые слова: " + ('нет' if settings['key_words'] == None else str(settings['key_words'])) + 
                                    "\nСсылки для поиска: " + ('нет' if settings['links'] == None else str(settings['links'])) )

                    #фиксируем время начала поиска
                    settings['start_time'] = time.time()

                    #бесконечный мониторинг, пока не остановят внешней командой stop
                    settings['is_stop'] = False
                    settings['total'] = 0
                    settings['aim'] = 0
                
                fParser = FParser(settings)
                while settings['is_stop'] == False:
                    data = fParser.do_parse()

                    if (data != None and settings['is_stop'] == False):
                        settings['total'] += data['total']
                        settings['aim'] += data['aim'] 
                        for messg in data['messages']:
                            bot.send_message(user_id, messg)

                    #Фиксируем данные после каждой итерации на случай сбоев по время парсинга
                    saveSetts(settings)

                    time.sleep(5)
            else:
                bot.send_message(user_id, "Чтобы начать новый поиск," +
                "необходимо добавить хотя бы 1 страницу для поиска.")
        else:
            bot.send_message(user_id, "Чтобы начать новый поиск," +
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
                            "\nВсего свежих анкет: " + str(settings['total']) +
                            "\nИз них подходящих: " + str(settings['aim']))


    @bot.message_handler(commands=['settings'])
    def com_settings(message):
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        if settings['is_stop'] == True:
            user_markup.row("/age", "/key_words", "/links")
            user_markup.row("/tomenu")
            bot.send_message(message.from_user.id,
                            "Вы можете настроить критерии поиска следующими командами:\n" +
                            "\t/age - искомый минимальный возраст\n" +
                            "\t/key_words - искомые ключевые слова\n" +
                            "\t/links - ссылки в ВК, где будет поиск",
                            reply_markup=user_markup)
        else:
            bot.send_message(message.from_user.id, 
                            "Чтобы изменить настройки, сначала необходимо " +
                            "остановить текущий сеанс поиска командой /stop")

    @bot.message_handler(commands=['tomenu'])
    def tomenu(message):
        user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
        settings['currCommand'] = None
        user_markup.row("/go", "/stop")
        user_markup.row("/status", "/settings")
        bot.send_message(message.from_user.id, 'Настройки учтены', reply_markup=user_markup)
        saveSetts(settings)

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
        links_text = ''
        num = 1
        for ltext in settings['links']:
            links_text += str(num) + ") " + ltext + "\n"
            num += 1
        bot.send_message(message.from_user.id, 
                        "Введите через ПРОБЕЛ ссылки,по которым будут подбираться анкеты. " +
                        "\n    ВАЖНО: ссылка должна быть именно на стену сообщества, например:" +
                        "'vk.com/wall-ID_СООБЩЕСТВА'.\n    ЕСЛИ вы хотите добавить новую ссылку к " +
                        "существующим пришлите '+' в начале ссылки, например: '+vk.com/wall-ID_СООБЩЕСТВА'" +
                        "\n    ЕСЛИ хотите удалить ссылку, то пришлите '-НОМЕР_ССЫЛКИ'\n" + links_text) 

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
            if (message.text != None):
                bot.send_message(message.from_user.id, 'Принято. Новые ключевые слова для поиска: ' + message.text)
                settings['key_words'] = message.text.split(' ')
        elif settings['currCommand'] == 'links':
            if (message.text != None):
                if (message.text[0] == '+'):
                    bot.send_message(message.from_user.id, 'Принято. Добавлена новая ссылка: ' + message.text[1:])
                    settings['links'].append(message.text[1:])
                elif(message.text[0] == '-'):
                    try:
                       settings['links'].pop(int(message.text[1:]) - 1)
                    except:
                        bot.send_message(message.from_user.id, 'Не удалось удалить...проверьте корректность.')
                    else:
                        bot.send_message(message.from_user.id, 'Принято, указанная ссылка удалена.')
                else:
                    bot.send_message(message.from_user.id, 'Принято. Новые ссылки для поиска: ' + message.text)
                    settings['links'] = message.text.split(' ')
        else:
            user_markup = telebot.types.ReplyKeyboardMarkup(True, False)
            user_markup.row("/go", "/stop")
            user_markup.row("/status", "/settings")
            bot.send_message(message.from_user.id, 
                            "Привет. Это YourFriendBot. Я помогаю находить анкеты в" +
                            "пабликах по ключевым словам, тебе остаётся только" +
                            "настроить, запустить и ждать, когда я отпправлю тебе первые анкеты ;)\n\n" +
                            "Ты можешь использовать следующие команды:\n" +
                            "\t/go - начало новой сессии поиска\n" +
                            "\t/stop - прекращение действующей сессии\n" +
                            "\t/status - информация о текущей сесcии\n" +
                            "\t/settings - информация о текущих настройках поиска\n\n" +
                            "Перед запуском новой сессии можно применить настройки поиска по ключевым словам:\n" +
                            "\t/age - искомый минимальный возраст\n" +
                            "\t/key_words - искомые ключевые слова\n" +
                            "\t/links - ссылки в ВК, где будет поиск",
                            reply_markup=user_markup)
        
        settings['currCommand'] = None

    logging.basicConfig(
                        filename="botError.log",
                        level=logging.ERROR,
                        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )

    #=======C этого момента стартует бот======

    settings = {
                'id': -1,
                'total': 0,
                'aim': 0,
                'currCommand': None,
                'start_time': 0,
                'is_stop': True,
                'age': '18',
                'key_words': ['Москва'],
                'links': [
                    'https://vk.com/topic-12125584_27005921?offset=600',
                    'https://vk.com/wall-108037201?own=1',
                    'https://vk.com/wall-78855837?own=1',
                    'https://vk.com/wall-102911028?own=1',
                    'https://vk.com/topic-12125584_33046615?offset=1080'
                    ]
                }
    json_obj = None
    t = threading.Thread(target=com_go, args=(None,))
    try:
        #Начинаем работу с попытки загрузить данные, если таковые имеюся
        with open('data.json', 'r', encoding='utf-8') as f:
            json_obj = json.load(f)

        #загрузка настроек после перезапуска или сбоя
        if json_obj: 
            settings = json_obj
            if (json_obj['is_stop'] == False):
                settings['currCommand'] = 'restart'
                bot.send_message(settings['id'], "Бот перезапустился, информация о сессии сохранена.")

                #запускаем в другом потоке парсер
                t.daemon = True
                t.start()

        elif json_obj == None:
            saveSetts(settings)

    except Exception as ex:
        with open("botLog.txt", "a") as log:
            log.write(str(time.ctime(time.time())) + " - " + str(ex))
        print(ex)

    try:
        with open("botLog.txt", "a") as log:
            log.write(str(time.ctime(time.time())) + " - Запуск Bot Polling")
        bot.polling(none_stop=True, timeout=300)  
    except Exception as e:
        print('Some error: ' + str(e))
        with open("botLog.txt", "a") as log:
            log.write(str(time.ctime(time.time())) + " - " + str(e))
        time.sleep(10)