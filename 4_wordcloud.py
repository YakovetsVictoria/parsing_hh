import sqlalchemy                   # Для подключения к СУБД
import matplotlib.pyplot as plt     # Для визуализации облака
from wordcloud import WordCloud     # Для создания облака слов
from PIL import Image               # Для открытия изображения
import numpy as np                  # Для преобразования изображения

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

# Выполнение запроса, который достанет из БД слова и частоту их появления в описаниях вакансий
query = "SELECT * FROM description_word_clean"
t = sqlalchemy.text(query)
result = dict(list(conn.execute(t)))
print('Запрос выполнен')

# Загрузка маски для облака в формате массива нампай
wordcloud_image = np.array(Image.open('cloud.png'))

# Создание облака слов
wordcloud = WordCloud(background_color=None,
                      mode='RGBA',              # Для прозрачного фона
                      max_words=200,
                      max_font_size=80,
                      mask=wordcloud_image,
                      colormap='summer').fit_words(result)

plt.figure(figsize=(40, 30))            # Размер картинки
plt.axis("off")                         # Без подписей на осях

# Отображение облака
plt.imshow(wordcloud, interpolation='bilinear')
plt.show()

# Сохранение в виде картинки
wordcloud.to_file('wordcloud.png')

# Закрытие соединения с БД
conn.close()
print('Соединение с БД закрыто')

