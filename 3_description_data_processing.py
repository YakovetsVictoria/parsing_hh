import sqlalchemy                   # Для подключения к СУБД
import pandas as pd                 # Для удобной загрузки данных в БД
import re                           # Для удаления лишних символов в тексте
import pymorphy3                    # Для морфологического анализа

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

# Выполнение запроса, который достанет из БД описание всех вакансий
query = "SELECT description FROM vacancy"
t = sqlalchemy.text(query)
result = list(conn.execute(t))         # Результат - в виде списка кортежей (каждый с единственным элементом)
print('Запрос выполнен')

# Перебор кортежей результата и обработка текста
words = {}                                                              # Словарь для подсчета слов
functors_pos = {'INTJ', 'PRCL', 'CONJ', 'PREP', 'NPRO', 'NUMR'}         # Тэги служебных и др. частей речи
# functors_pos = {междометие, частица, союз, предлог, местоимение, числительное}
i = 0               # Счетчик для вывода информации о количестве обработанных строк
for tpl in result:
    row = tpl[0]
    # Удаление тэгов разметки HTML <> и других лишних символов
    row = re.sub(r'<.*?>|[^\w ]', ' ', row.lower())
    # Подсчет количества для каждого слова и добавление их в словарь
    for word in row.split():
        # Подробная информация о форме слова (его атрибуты - часть речи, лемма и т.д.):
        word = pymorphy3.MorphAnalyzer().parse(word)[0]
        word_pos = word.tag.POS                     # Тэг части речи слова (Part Of Speech)
        word_norm_form = word.normal_form           # Лемма слова / нормальная форма
        # Условие для фильтрации частей речи
        if word_pos not in functors_pos:
            words[word_norm_form] = words.get(word_norm_form, 0) + 1
    i += 1
    print(f'Обработано {i} из {len(result)} строк')


# Оформление результата подсчета (словаря) в дата-фрейм
df_words = pd.DataFrame({'word': words.keys(), 'amount': words.values()})
# Создание таблицы в БД
df_words.to_sql('description_word', eng, if_exists='replace', index=False)
print('Данные загружены в БД')

# Закрытие соединения с БД
conn.close()
print('Соединение с БД закрыто')
