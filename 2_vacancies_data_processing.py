import json                 # Для работы с форматом json
import os                   # Для работы с ОС (для создания файлов)
import pandas as pd         # Для удобной загрузки данных в БД
import sqlalchemy           # Для подключения к СУБД

# Создание списков для столбцов таблицы vacancy
vacancy_id = []
vacancy_name = []
experience = []
description = []
salary_from = []
salary_to = []
salary_currency = []

# Создание списков для столбцов таблицы company
company_id = []
company_name = []

# Создание списков для столбцов таблицы skill
skill_vacancy_id = []      # Список идентификаторов вакансий
skill_name = []            # Список названий навыков

# Перебор всех файлов в папке vacancies
for fl in os.listdir('./docs/vacancies'):
    # Открытие, чтение, закрытие файла
    f = open(f'./docs/vacancies/{fl}', encoding='utf8')
    json_text = f.read()
    f.close()
    # Перевод текста файла в словарь
    json_dict = json.loads(json_text)

    # Заполнение списков для таблиц
    vacancy_id.append(json_dict['id'])
    vacancy_name.append(json_dict['name'])
    experience.append(json_dict['experience']['name'])
    description.append(json_dict['description'])
    company_id.append(json_dict['employer']['id'])
    company_name.append(json_dict['employer']['name'])

    # Условие для проверки, указана зарплата или нет
    if json_dict['salary'] is not None:
        salary_from.append(json_dict['salary']['from'])
        salary_to.append(json_dict['salary']['to'])
        salary_currency.append(json_dict['salary']['currency'])
    else:
        salary_from.append(None)
        salary_to.append(None)
        salary_currency.append(None)

    # Навыки хранятся в виде массива -> перебор массивов
    for skl in json_dict['key_skills']:
        skill_vacancy_id.append(json_dict['id'])
        skill_name.append(skl['name'])
print('Файлы обработаны')

# Создание дата-фреймов pandas
df_vacancy = pd.DataFrame({'id': vacancy_id,
                           'name': vacancy_name,
                           'experience': experience,
                           'description': description,
                           'salary_from': salary_from,
                           'salary_to': salary_to,
                           'salary_currency': salary_currency,
                           'company_id': company_id})

df_company = pd.DataFrame({'id': company_id,
                           'name': company_name})

df_skill = pd.DataFrame({'name': skill_name,
                         'vacancy_id': skill_vacancy_id})

print('Дата-фреймы созданы')


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

# Создание таблиц в БД
df_vacancy.to_sql('vacancy', eng, if_exists='replace', index=False)
df_company.to_sql('company', eng, if_exists='replace', index=False)
df_skill.to_sql('skill', eng, if_exists='replace', index=False)
print('Данные загружены в БД')

# Закрытие соединения с БД
conn.close()
print('Соединение с БД закрыто')
