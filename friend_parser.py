from bs4 import BeautifulSoup as bs
import requests
import selenium
from selenium import webdriver

age_diff = 5 #разница в большую сторону с минимальным возрастом
old_ids = [] #список для временного хранение id постов
store_limit = 20 #лимит хранения старых id

#cписок найденых сообщений и статистика, которые будут возвращены боту
toBot = {
    'messages': [],
    'total_forms': 0,
    'aim_forms': 0
    }

setts = {
    'ages': [],
    'key_words': [],
    'links': []
    }

def new(settings):
    setts['key_words'] = settings['key_words']
    setts['links'] = settings['links']

    #создание списка [мин.,...,мин.+5]
    min_age = int(settings['age'])
    ages = []
    for age in range(min_age, min_age + age_diff):
        ages.append(str(age))
    setts['ages'] = ages

def do_parse():
    toBot['messages'] = []
    toBot['total_forms'] = 0
    toBot['aim_forms'] = 0

    for link in setts['links']:
        #Имитация браузера
        browser = webdriver.PhantomJS(executable_path="F:/phantomjs-2.1.1-windows/bin/phantomjs.exe")
        browser.get(link)
        html = browser.page_source

        soup = bs(html, "html.parser")

        if 'wall' in link: #если это записи на стене группы
            main_wall = soup.find('div', attrs={'id': 'page_wall_posts'})
            posts = main_wall.find_all('div', attrs={'class': '_post_content'})

            for post in posts:
                date = post.find("div", attrs={'class': 'post_date'})
                #проверка, что это именно пост, а не про комментарий и тд
                if date != None:
                    link = post.find('a', attrs={'class':'post_link'})['href']
                    full_link = 'https://vk.com' + link

                    #открываем пост полностью и анализируем полный текст
                    session = requests.session()
                    request = session.get(full_link)

                    full_post = bs(request.content,"html.parser")

                    #f = open('test.txt', 'w', encoding='utf-8')
                    #f.write(str(full_post.prettify))
                    #f.close()
                    
                    #Если вдруг текста в посте нет, то на следующую итерацию
                    try:
                        post_text = full_post.find('div', attrs={'class': 'wall_post_text'}).text
                    except:
                        continue

                    post_id = link #id = уникальная ссылка
                    if post_id not in old_ids:
                        toBot['total_forms'] += 1
             
                    if (
                    post_id not in old_ids and
                    any((age in post_text) for age in setts['ages']) and 
                    any((key in post_text) for key in setts['key_words'])
                    ):
                        toBot['messages'].append(
                            "Время публикации: " + date.text + "\n\n" + 
                            post_text + "\n\n" + "ссылка: " + full_link 
                        )
                        toBot['aim_forms'] = toBot['aim_forms'] + 1

                        old_ids.append(post_id)
                        #при привышении лимита на хранение удаляем начиная со старых
                        while(len(old_ids) > store_limit):    
                            old_ids.pop(0)
                        
                else: 
                    continue

        elif 'topic' in link: #если это записи в топике группы
            pass

    return toBot

def parse(settings):
    new(settings)
    return do_parse()       
