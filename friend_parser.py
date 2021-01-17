import requests
import time
import lxml.html
import logging

from bs4 import BeautifulSoup as bs

from secret import AUTF_DATA


logger = logging.getLogger(__name__)
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(module)s: %(message)s',
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ],
    )

# Чтобы вк считал нас немобильным устройством 
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


class FParser:
    def __init__(self, setts):
        self.AGE_DIFF = 5 # Разница в большую сторону с минимальным возрастом
        self.STORE_LIMIT = 16 # Лимит хранения старых id для каждой ссылки поиска
        self.TOPIC_LIMIT = 20 # Максимальное количество топиков в одной странице(ограничение от ВК)
        self.TEXT_LIMIT = 200 # Максимальное кол-во символов от поста, выводящиеся ботом

        if setts['old_links'] == {}:
            self.__old_links = {link: [] for link in setts['links']}
        else:
            self.__old_links = setts['old_links']

        # Учтение настроек, переданые от бота
        self.__setts = dict() 
        self.__setts['key_words'] = setts['key_words']
        self.__setts['links'] = setts['links']
        self.__setts['ages'] = self.__genetate_ages(setts['age'])

    def __genetate_ages(self, age):
        """
        Cоздание списка возрастов [мин.,...,мин.+5]
        """
        min_age = int(age)
        ages = []
        for age in range(min_age, min_age + self.AGE_DIFF):
            ages.append(str(age))
        return ages

    def do_parse(self):
        """
        Список найденых сообщений и статистика, которые будут возвращены боту
        """
        to_bot = {
            'messages': [],
            'total': 0,
            'aim': 0,
            'old_links': {}
        }  

        for root_link in self.__setts['links']:
            # Имитация запроса
            request = requests.get(root_link, headers=HEADERS)
            soup = bs(request.content, "html.parser")
            
            # Если ошибка доступа, то скорее всего для страницы нужно авторизоваться
            if ('Ошибка доступа' in soup.text):
                try:
                    session = self.__autf(AUTF_DATA)
                except:
                    logger.warning("Ошибка авторизации по адресу: " + root_link)
                    break 

                if (session == "ErrorAuth"):
                    logger.warning("Ошибка авторизации по адресу: " + root_link)
                    break
                else:
                    request = session.get(root_link)
                    soup = bs(request.content, "html5lib")    

            # Если это записи на стене группы
            if 'wall' in root_link: 
                # Берём самые новые посты в количестве лимита
                with open('tt.html', 'w', encoding='utf-8') as f:
                    f.write(soup.prettify())
                posts = soup.find_all('div', attrs={'class': 'wall_text'})[:self.STORE_LIMIT]

                # Если мы уже храним максимальное количество постов, то новые посты должны поступать
                # в обратном порядке, это поможет сохранить их последовательность от самых новых до старых
                if (len(self.__old_links[root_link]) == self.STORE_LIMIT):
                    posts = posts[::-1]

                # Проход по каждому посту от самого нового до лимита хранения
                for post in posts:
                    # Генерируем ппрямую ссылку на пост из его уникального id
                    link = post.find('div', attrs={'class':'wall_post_cont _wall_post_cont'})['id'][3:]
                    full_link = 'https://vk.com/wall' + link

                    # Если старая ссылка, сразу пропускаем
                    if link in self.__old_links[root_link]:
                        continue

                    post_text = ""
                    try:
                        # Открываем пост полность в новой вкладке и анализируем полный текст
                        request = requests.get(full_link, headers=HEADERS)
                        full_post = bs(request.content, "lxml")
                        with open('full.html', 'w', encoding='utf-8') as f:
                            f.write(full_post.prettify())
                        post_text = full_post.find('div', attrs={'class': 'wall_post_text'}).text
                    except:
                        logger.warning("Cбой при открытии " + full_link)
                        # Скорее всего пост не содержит текста и может являться анкетой вовсе,
                        # но всё равно сохраняем его в старые ссылки, чтобы не пытаться
                        # открыть его при каждой итерации.
                        self.__old_links[root_link].append(link)
                        continue
                    else:
                        self.__analize(to_bot, post_text, link, full_link, root_link)
            elif 'topic' in root_link: # Если это записи в топике группы
                try:
                    topic_wall = soup.find('div', attrs={'id': 'content'})
                    topics = topic_wall.find_all('div', attrs={'class': 'bp_post clear_fix'})
                except:
                    logger.warning("Cбой при доступе к топику: " + root_link)
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

                        self.__analize(to_bot, topic_text, link, full_link, root_link)         
            else:
                pass
            to_bot['old_links'] = self.__old_links
        return to_bot

    def __analize(self, to_bot, text, link, full_link, root_link):
        """
        Анализ наличия ключевых слов и формировани ответа для бота
        """
        if link not in self.__old_links[root_link]:
            # Если пришла новая ссылка, то: если её ячейка уже заполнилась,
            # тогда добавляем её в начало, сдвинув все остальные вправо, при этом,
            # удалится наиболее старая запись
            if (len(self.__old_links[root_link]) == self.STORE_LIMIT):
                self.__old_links[root_link] = self.__push_queue(link, self.__old_links[root_link])
            else:
                self.__old_links[root_link].append(link)
            to_bot['total'] += 1
        else:
            return # Пропуск старой ссылки, которая просматривалась
        if ( 
            any((age in text) for age in self.__setts['ages']) and 
            any((key.lower() in text.lower()) for key in self.__setts['key_words'])
        ):
            logger.info("Ссылка подходит: " + full_link)
            to_bot['messages'].append(
                text[:self.TEXT_LIMIT] + "...\n\n" + "ссылка: " + full_link 
            )
            to_bot['aim'] = to_bot['aim'] + 1
        else:
            logger.info("Ссылка НЕ подходит: " + full_link)

    def __autf(self, autf_data):
        """
        Метод для авторизации, если предполагается поиск в закрытом сообществе
        """
        login_url = 'https://vk.com/login'

        session = requests.session()
        data = session.get(login_url)
        html = lxml.html.fromstring(data.content)

        form = html.forms[0]
        form.fields['email'] = autf_data['login']
        form.fields['pass'] = autf_data['pass']

        response = session.post(form.action, data=form.form_values())

        if ('onLoginDone' in response.text):
            return session
        else:
            logger.error("ErrorAuth")
            return "ErrorAuth"

    def __push_queue(self, el, array):
        return [el] + array[:-1]

