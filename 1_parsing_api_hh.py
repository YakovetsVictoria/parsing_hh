import requests                 # Для работы с http-запросами
import fake_useragent           # Для создания заголовков
import json                     # Для работы с форматом json
import time                     # Для задержки между запросами
import pandas as pd             # Для удобной загрузки данных в БД
import sqlalchemy               # Для подключения к СУБД
from pycbrf.toolbox import ExchangeRates    # Для курса валют
import datetime


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
    req = requests.get(url, params, headers=get_headers(), timeout=20)  # Запрос к API
    data = req.content.decode()                 # Декодирование ответа (для Кириллицы)
    return data


# Текст поискового запроса
text_filter = '"Data Engineer" OR "ML Engineer" OR "ETL Developer"'

page_result_list = []
# Считывание 10000 вакансий (100 страниц по 100 вакансий)
for page in range(0, 100):
    # Преобразование текстового ответа запроса в словарь
    page_dict = json.loads(get_page(text_filter, page))

    # Сохранение страниц в список
    page_result_list.append(json.dumps(page_dict, ensure_ascii=False))

    # Условие выхода из цикла (если страниц окажется меньше 100)
    if (page_dict['pages'] - page) <= 1:
        break
    # Задержка, чтобы не нагружать сервисы hh
    time.sleep(0.25)
print('Страницы поиска собраны')

# Перебор списка страниц, в которых указаны списки вакансий на одной странице
vacancies_result_list = []
vac_cnt = json.loads(page_result_list[0])['found']  # Общее количество вакансий
cnt = 0  # Счетчик для вывода информации о количестве вакансий
for fl in page_result_list:
    # Перевод текста страницы в словарь
    json_dict = json.loads(fl)

    # Перебор списка вакансий, указанных на одной странице
    for vac in json_dict['items']:
        # Обращение к API и получение детальной информации по каждой конкретной вакансии (на основе её url)
        req = requests.get(vac['url'], headers=get_headers())
        data = req.content.decode()

        # Сохранение вакансии в список
        vacancies_result_list.append(data)

        time.sleep(0.25)
        cnt += 1
        print(f'Обработано {cnt} из {vac_cnt} вакансий')
print('Вакансии собраны')


###########################################################################

# Для случаев, когда обращение по ключу возвращает None, и нужно законтрить следующий get
def if_dict_returns_none(key):
    if json_dict.get(key) is None:
        return dict()
    else:
        return json_dict.get(key, dict())


# Для случаев, когда обращение по ключу возвращает None, и нужно оформить цикл по пустому списку вместо None
def if_dict_returns_none_lst(key):
    if json_dict.get(key) is None:
        return []
    else:
        return json_dict.get(key, [])


# Создание списков словарей для таблиц vacancy, company, skill
vacancy, company, skill = [], [], []

# Перебор всех вакансий в списке vacancies_result_list
for fl in vacancies_result_list:
    # Перевод текста в словарь
    json_dict = json.loads(fl)

    # Заполнение словарей для таблиц
    vacancy_fl = {'id': json_dict.get('id'),
                  'name': json_dict.get('name'),
                  'experience': if_dict_returns_none('experience').get('name'),
                  'description': json_dict.get('description'),
                  'salary_from': if_dict_returns_none('salary').get('from'),
                  'salary_to': if_dict_returns_none('salary').get('to'),
                  'salary_currency': if_dict_returns_none('salary').get('currency'),
                  'company_id': if_dict_returns_none('employer').get('id')}
    vacancy.append(vacancy_fl)

    company_fl = {'id': if_dict_returns_none('employer').get('id'),
                  'name': if_dict_returns_none('employer').get('name')}
    company.append(company_fl)

    # Пример хранения скиллов: json_dict['key_skills'] = [{"name":"Python"},{"name":"Bash"},{"name":"Docker"}...]
    for skl in if_dict_returns_none_lst('key_skills'):
        skill_fl = {'vacancy_id': json_dict.get('id'),
                    'name': skl.get('name')}
        skill.append(skill_fl)
print('Вакансии обработаны')

# Результаты заносим в дата-фреймы
vac = pd.DataFrame(vacancy)
comp = pd.DataFrame(company).drop_duplicates()
skll = pd.DataFrame(skill)

# Находим среднюю зарплату между "от" и "до"
vac['sal_avg'] = (vac['salary_to'].fillna(vac['salary_from']) + vac['salary_from'].fillna(vac['salary_to'])) / 2

# Получаем курсы валют
current_date = datetime.date.today().isoformat()
rates = ExchangeRates(current_date) # задаем дату, за которую хотим получить данные валют
usd = int(rates['USD'].value)
eur = int(rates['EUR'].value)


# Функция для конвертации средней зарплаты в рубли
def convert_currency(row):
    if row['salary_currency'] == 'RUR':
        res = row['sal_avg']
    elif row['salary_currency'] == 'EUR':
        res = row['sal_avg'] * eur
    elif row['salary_currency'] == 'USD':
        res = row['sal_avg'] * usd
    else:
        res = None
    return res


vac['sal2rub'] = vac.apply(convert_currency, axis=1)
vac_fin = vac[['vacancy_id', 'vacancy_name', 'experience', 'description', 'company_id', 'sal2rub']]
vac_comp = vac_fin.merge(comp, how='left', on='company_id')

###########################################################################

# Данные для подключения к БД
user = '**********'
password = '**********'
host = 'localhost'
port = 5432
database = 'parsing_hh'

# Создание подключения к БД
eng = sqlalchemy.engine.create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}')
conn = eng.connect()
print('Подключение к БД создано')

# Создание дата-фреймов pandas и таблиц в БД
vac_comp.to_sql('vacancy', eng, if_exists='replace', index=False)
skll.to_sql('skill', eng, if_exists='replace', index=False)
print('Данные загружены в БД')

# Закрытие соединения с БД
conn.close()
print('Соединение с БД закрыто')
