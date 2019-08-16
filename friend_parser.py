from bs4 import BeautifulSoup as bs
import requests
import lxml.html
from fake_useragent import UserAgent
from secret_token import AutfData

AGE_DIFF = 5 #разница в большую сторону с минимальным возрастом
STORE_LIMIT = 8 #лимит хранения старых id для каждой ссылки поиска

#нужные настройки для поиска, получамые от бота
setts = {
    'ages': [],
    'key_words': [],
    'links': []
    }

old_links = {}

def new(settings):
    setts['key_words'] = settings['key_words']
    setts['links'] = settings['links']

    old_links = {link: [] for link in setts['links']}

    #создание списка возрастов [мин.,...,мин.+5]
    min_age = int(settings['age'])
    ages = []
    for age in range(min_age, min_age + AGE_DIFF):
        ages.append(str(age))
    setts['ages'] = ages

def do_parse():
    #cписок найденых сообщений и статистика, которые будут возвращены боту
    toBot = {
        'messages': [],
        'total_forms': 0,
        'aim_forms': 0
    }

    for root_link in setts['links']:
        #Имитация запроса с разных браузеров
        us = UserAgent()
        request = requests.get(root_link, headers={'User-Agent': str(us.random)})
        soup = bs(request.content, "lxml")
        
        #Если ошибка доступа, то скорее всего для страницы нужно авторизоваться
        if ('Ошибка доступа' in soup.text):
            session = autf(root_link, AutfData)
            if (session == "ErrorAuth"):
                print("\nОшибка авторизации по адресу: " + root_link)
                break
            else:
                request = session.get(root_link, headers={'User-Agent': str(us.random)})
                soup = bs(request.content, "lxml")    

        if 'wall' in root_link: #если это записи на стене группы
            main_wall = soup.find('div', attrs={'id': 'page_wall_posts'})
            posts = main_wall.find_all('div', attrs={'class': 'wall_text'})

            #проход по каждому посту от самого нового до лимита хранения
            #прорускаем 0 пост, так как он всегда закреплён и носит информационный характер
            for post in posts[1:STORE_LIMIT]:
                #генерируем ппрямую ссылку на пост из его уникального id
                link = post.find('div', attrs={'class':'wall_post_cont _wall_post_cont'})['id'][3:]
                full_link = 'https://vk.com/wall' + link

                #открываем пост полность в новой вкладке и анализируем полный текст
                request = requests.get(full_link, headers={'User-Agent': str(us.random)})
                full_post = bs(request.content,"lxml")
                
                #Если вдруг текста в посте нет(только картинки и тд), то на следующую итерацию
                post_text = full_post.find('div', attrs={'class': 'wall_post_text'})
                if (post_text == None):
                    continue
                else:
                    post_text = post_text.text

                if link not in old_links[root_link]:
                    toBot['total_forms'] += 1
                else:
                    continue #пропуск старой ссылки, которая просматривалась
             
                if (
                any((age in post_text) for age in setts['ages']) and 
                any((key in post_text) for key in setts['key_words'])
                ):
                    toBot['messages'].append(
                        post_text[:200] + "...\n\n" + "ссылка: " + full_link 
                    )
                    toBot['aim_forms'] = toBot['aim_forms'] + 1

                    old_links[root_link].append(link)
                    #при привышении лимита на хранение удаляем начиная со старых
                    while(len(old_links[root_link]) > STORE_LIMIT):    
                        old_links[root_link].pop()                      

        elif 'topic' in root_link: #если это записи в топике группы
            topic_wall = soup.find('div', attrs={'id': 'content'})
            topics = topic_wall.find_all('div', attrs={'class': 'bp_post clear_fix'})

            for topic in topics:
                topic_text = topic.find('div', attrs={'class': 'bp_text'}).text
                link = topic.find('a', attrs={'class': 'bp_date'})['href']
                full_link = 'https://vk.com' + link
                


    return toBot

#Метод для авторизации, если предполагается поиск в закрытом сообществе
def autf(url, autf_data):
    login_url = 'https://vk.com/login'
    login = autf_data[0]
    pwd = autf_data[1]

    session = requests.session()
    us = UserAgent()
    data = session.get(login_url, headers={'User-Agent': str(us.random)})
    html = lxml.html.fromstring(data.content)

    form = html.forms[0]
    form.fields['email'] = login
    form.fields['pass'] = pwd

    response = session.post(form.action, data=form.form_values())

    if ('onLoginDone' in response.text):
        return session
    else:
        return "ErrorAuth"

def parse(settings):
    new(settings)
    return do_parse()       
