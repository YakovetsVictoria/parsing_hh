import requests                 # Для работы с http-запросами
import fake_useragent           # Для создания заголовков
import os                       # Для работы с ОС (для создания файлов)
import json                     # Для работы с форматом json
import time                     # Для задержки между запросами

# Функция для создания рандомных заголовков
def get_headers():
    user_ag = fake_useragent.UserAgent().random
    headers = {'user-agent': user_ag}
    return headers


# Функция для получения страницы со списком вакансий (pg - индекс страницы)
def get_page(text, pg=0):
    # Справочник параметров GET-запроса
    params = {
        'text': text,               # Текст поискового запроса
        'area': 1,                  # Индекс города Москва
        'page': pg,                 # Индекс страницы поиска на HH
        'per_page': 100             # Кол-во вакансий на 1 странице
    }
    # Чтобы спарсить вакансии со страницы, нужно выполнить методом GET http-запрос,
    # включая параметры фильтра поиска (ответ приходит в формате json):
    url = 'https://api.hh.ru/vacancies'
    req = requests.get(url, params, headers=get_headers())  # Запрос к API
    data = req.content.decode()                             # Декодирование ответа (для Кириллицы)
    req.close()
    return data


# Текст поискового запроса
text_filter = '"Data Engineer" OR "ML Engineer" OR "ETL Developer"'

# Считывание 1000 вакансий (10 страниц по 100 вакансий)
for page in range(0, 10):
    # Преобразование текстового ответа запроса в словарь
    page_dict = json.loads(get_page(text_filter, page))

    # Сохранение файлов страниц в папку {путь до текущего файла}/docs/pagination
    # Формирование имени документа (количество файлов в папке - len(...))
    file_name = './docs/pagination/{}.json'.format(len(os.listdir('./docs/pagination')))

    # Создание нового документа, запись ответа запроса, закрытие документа
    f = open(file_name, mode='w', encoding='utf8')
    f.write(json.dumps(page_dict, ensure_ascii=False))
    f.close()

    # Условие выхода из цикла (если страниц окажется меньше 10)
    if (page_dict['pages'] - page) <= 1:
        break
    # Задержка, чтобы не нагружать сервисы hh
    time.sleep(0.25)
print('Страницы поиска собраны')

# Перебор файлов страниц, в которых указаны списки вакансий на одной странице
i = 0               # Счетчик для вывода информации о количестве вакансий
for fl in os.listdir('./docs/pagination'):
    # Открытие, чтение, закрытие файла
    f = open(f'./docs/pagination/{fl}', encoding='utf8')
    json_text = f.read()
    f.close()
    # Перевод текста файла в словарь
    json_dict = json.loads(json_text)

    vac_count = json_dict['found']      # Общее количество вакансий
    # Перебор списка вакансий, указанных на одной странице
    for vac in json_dict['items']:
        # Обращение к API и получение детальной информации по каждой конкретной вакансии (на основе её url)
        req = requests.get(vac['url'], headers=get_headers())
        data = req.content.decode()
        req.close()

        # Сохранение файлов вакансий в папку {путь до текущего файла}/docs/vacancies
        # id вакансии в качестве названия
        file_name = f"./docs/vacancies/{vac['id']}.json"

        # Создание нового документа, запись ответа запроса, закрытие документа
        f = open(file_name, mode='w', encoding='utf8')
        f.write(data)
        f.close()

        time.sleep(0.25)
        i += 1
        print(f'Обработано {i} из {vac_count} вакансий')
print('Вакансии собраны')
