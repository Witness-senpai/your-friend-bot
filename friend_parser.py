from bs4 import BeautifulSoup as bs
from secret_token import AutfData
import requests
import lxml.html
import time

class FParser:
    def __init__(self, setts):
        self.AGE_DIFF = 5 # Разница в большую сторону с минимальным возрастом
        self.STORE_LIMIT = 8 # Лимит хранения старых id для каждой ссылки поиска
        self.TOPIC_LIMIT = 20 # Максимальное количество топиков в одной странице(ограничение от ВК)

        if setts['old_links'] == {}:
            self.__old_links = {link: [] for link in setts['links']}
        else:
            self.__old_links = setts['old_links']


        #учтение настроек, переданые от бота
        self.__setts = dict() 
        self.__setts['key_words'] = setts['key_words']
        self.__setts['links'] = setts['links']
        self.__setts['ages'] = self.__genetate_ages(setts['age'])

    #создание списка возрастов [мин.,...,мин.+5]
    def __genetate_ages(self, age):
        min_age = int(age)
        ages = []
        for age in range(min_age, min_age + self.AGE_DIFF):
            ages.append(str(age))
        return ages

    def do_parse(self):
        # Список найденых сообщений и статистика, которые будут возвращены боту
        toBot = {
            'messages': [],
            'total': 0,
            'aim': 0,
            'old_links': {}
        }  

        for root_link in self.__setts['links']:
            # Имитация запроса
            request = requests.get(root_link)
            soup = bs(request.content, "lxml")
            
            # Если ошибка доступа, то скорее всего для страницы нужно авторизоваться
            if ('Ошибка доступа' in soup.text):
                try:
                    session = self.__autf(root_link, AutfData)
                except:
                    print("\nОшибка авторизации по адресу: " + root_link)
                    with open("botLog.txt", "a") as log:
                        log.write(str(time.ctime(time.time())) + "Ошибка авторизации по адресу: " + root_link + "\n")
                    break         
                if (session == "ErrorAuth"):
                    print("\nОшибка авторизации по адресу: " + root_link)
                    with open("botLog.txt", "a") as log:
                        log.write(str(time.ctime(time.time())) + "Ошибка авторизации по адресу: " + root_link + "\n")
                    break
                else:
                    request = session.get(root_link)
                    soup = bs(request.content, "lxml")    

            if 'wall' in root_link: #если это записи на стене группы
                # Берём самые новые посты в количестве лимита
                posts = soup.find_all('div', attrs={'class': 'wall_text'})[:self.STORE_LIMIT]

                # Если мы уже храним максимальное количество постов, то новые посты должны поступать
                # в обратном порядке, это поможет сохранить их последовательность от самых новых до старых
                if (len(self.__old_links[root_link]) == self.STORE_LIMIT):
                    posts = posts[::-1]

                # Проход по каждому посту от самого нового до лимита хранения
                for post in posts:
                    #генерируем ппрямую ссылку на пост из его уникального id
                    link = post.find('div', attrs={'class':'wall_post_cont _wall_post_cont'})['id'][3:]
                    full_link = 'https://vk.com/wall' + link

                    # Если старая ссылка, сразу пропускаем
                    if link in self.__old_links[root_link]:
                        continue

                    post_text = ""
                    try:
                        # Открываем пост полность в новой вкладке и анализируем полный текст
                        request = requests.get(full_link)
                        full_post = bs(request.content,"lxml")
                        post_text = full_post.find('div', attrs={'class': 'wall_post_text'}).text
                    except:
                        print("сбой при открытии " + full_link)
                        # Скорее всего пост не содержит текста и не нужный,
                        # но всё равно сохраняем его в старые ссылки, чтобы не пытаться
                        # открыть его при каждоый итерации.
                        self.__old_links[root_link].append(link)
                        with open("botLog.txt", "a") as log:
                            log.write(str(time.ctime(time.time())) + "сбой при открытии " + full_link + "\n")
                        continue
                    else:
                        self.__analize(toBot, post_text, link, full_link, root_link)

            elif 'topic' in root_link: # Если это записи в топике группы
                try:
                    topic_wall = soup.find('div', attrs={'id': 'content'})
                    topics = topic_wall.find_all('div', attrs={'class': 'bp_post clear_fix'})
                except:
                    print("сбой при доступе к топику: " + root_link)
                    continue
                else:
                    # Проход по последним записям в количесве ЛИМИТА либо по всем, если их меньше
                    nlist = (topics if len(topics) < self.STORE_LIMIT else topics[-self.STORE_LIMIT:])
                    for topic in nlist:
                        topic_text = topic.find('div', attrs={'class': 'bp_text'}).text
                        link = topic.find('a', attrs={'class': 'bp_date'})['href']
                        full_link = 'https://vk.com' + link

                        # Если старая ссылка, сразу пропускаем
                        if link in self.__old_links[root_link]:
                            continue

                        self.__analize(toBot, topic_text, link, full_link, root_link)         
            else:
                pass
            # Пауза в пару секунд между разными пабликами
            #time.sleep(1)
            toBot['old_links'] = self.__old_links
        return toBot

    # Анализ наличия ключевых слов и формировани ответа для бота
    def __analize(self, toBot, text, link, full_link, root_link):
        if link not in self.__old_links[root_link]:
            # Если пришла новая ссылка, то: если её ячейка уже заполнилась,
            # тогда добавляем её в начало, сдвинув все остальные вправо, при этом,
            # удалится наиболее старая запись
            if (len(self.__old_links[root_link]) == self.STORE_LIMIT):
                self.__old_links[root_link] = self.__push_queue(link, self.__old_links[root_link])
            else:
                self.__old_links[root_link].append(link)
            toBot['total'] += 1
        else:
            return # Пропуск старой ссылки, которая просматривалась
        if ( 
        any((age in text) for age in self.__setts['ages']) and 
        any((key.lower() in text.lower()) for key in self.__setts['key_words'])
        ):
            toBot['messages'].append(
                text[:200] + "...\n\n" + "ссылка: " + full_link 
            )
            toBot['aim'] = toBot['aim'] + 1

    # Метод для авторизации, если предполагается поиск в закрытом сообществе
    def __autf(self, url, autf_data):
        login_url = 'https://vk.com/login'
        login = autf_data[0]
        pwd = autf_data[1]

        session = requests.session()
        data = session.get(login_url)
        html = lxml.html.fromstring(data.content)

        form = html.forms[0]
        form.fields['email'] = login
        form.fields['pass'] = pwd

        response = session.post(form.action, data=form.form_values())

        if ('onLoginDone' in response.text):
            return session
        else:
            with open("botLog.txt", "a") as log:
                log.write(str(time.ctime(time.time())) + "ErrorAuth" + "\n")
            return "ErrorAuth"

    def __push_queue(self, el, array):
        return [el] + array[:-1]

