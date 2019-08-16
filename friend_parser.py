from bs4 import BeautifulSoup as bs
import requests
import lxml.html
from fake_useragent import UserAgent


age_diff = 5 #разница в большую сторону с минимальным возрастом
old_links = [] #список для временного хранение id постов
store_limit = 100 #лимит хранения старых id

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
        #Имитация запроса с разных браузеров
        us = UserAgent()
        request = requests.get(link, headers={'User-Agent': str(us.random)})
        soup = bs(request.content, "lxml")

        if 'wall' in link: #если это записи на стене группы
            main_wall = soup.find('div', attrs={'id': 'page_wall_posts'})
            posts = main_wall.find_all('div', attrs={'class': '_post_content'})

            for post in posts:
                date = post.find("div", attrs={'class': 'post_date'})
                #проверка, что это именно пост, а не комментарий по наличию селектора даты поста
                if date != None:
                    link = post.find('a', attrs={'class':'post_link'})['href']
                    full_link = 'https://vk.com' + link

                    #открываем пост полность в новой вкладке и анализируем полный текст
                    request = requests.get(full_link, headers={'User-Agent': str(us.random)})
                    full_post = bs(request.content,"lxml")

                    #f = open('test.txt', 'w', encoding='utf-8')
                    #f.write(str(full_post.prettify))
                    #f.close()
                    
                    #Если вдруг текста в посте нет(только картинки и тд), то на следующую итерацию
                    post_text = full_post.find('div', attrs={'class': 'wall_post_text'})
                    if (post_text == None):
                        continue
                    else:
                        post_text = post_text.text

                    if link not in old_links:
                        toBot['total_forms'] += 1
             
                    if (
                    link not in old_links and
                    any((age in post_text) for age in setts['ages']) and 
                    any((key in post_text) for key in setts['key_words'])
                    ):
                        toBot['messages'].append(
                            "Время публикации: " + date.text + "\n\n" + 
                            post_text[:200] + "...\n\n" + "ссылка: " + full_link 
                        )
                        toBot['aim_forms'] = toBot['aim_forms'] + 1

                        old_links.append(link)
                        #при привышении лимита на хранение удаляем начиная со старых
                        while(len(old_links) > store_limit):    
                            old_links.pop(0)
                        
                else: 
                    continue

        elif 'topic' in link: #если это записи в топике группы
            pass

    return toBot

def parse(settings):
    new(settings)
    return do_parse()       
