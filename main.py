from your_friend_bot import start

def main():
    #Бесконеный запуск парсера из главного файла
    #В случае сбоя он полностью перезапустится на новой итерации
    #А данные считает из json бекапа
    while (True):
        start()

if __name__ == '__main__':
    main()
    
    