-- Создаем представления для загрузки в Power BI:

-- Таблицу skill можно использовать без изменений

-- Объединяем таблицы vacancy и company
-- В таблице вакансий пересчитываем зарплату на рубли и находим среднее, если указана вилка
-- В таблице компаний убираем дубликаты
CREATE OR REPLACE VIEW vacancy_company_info AS 
SELECT v.id vac_id, v.name vac_name, experience, v.salary_avg, c.id comp_id, c.name comp_name
FROM
(
WITH a AS (
SELECT *,
(CASE
	WHEN salary_currency = 'RUR' THEN salary_from
	WHEN salary_currency = 'EUR' THEN salary_from * 83
	WHEN salary_currency = 'USD' THEN salary_from * 77
END) salary_from_RUR,
(CASE
	WHEN salary_currency = 'RUR' THEN salary_to
	WHEN salary_currency = 'EUR' THEN salary_to * 83
	WHEN salary_currency = 'USD' THEN salary_to * 77
END) salary_to_RUR
FROM vacancy
)
SELECT id, name, experience, company_id,
(CASE 
	WHEN salary_from_RUR IS NOT NULL AND salary_to_RUR IS NOT NULL THEN (salary_to_RUR + salary_from_RUR) / 2
	WHEN salary_from_RUR IS NOT NULL AND salary_to_RUR IS NULL THEN salary_from_RUR
	WHEN salary_from_RUR IS NULL AND salary_to_RUR IS NOT NULL THEN salary_to_RUR
END) salary_avg
FROM a
) v
JOIN
(
SELECT id, name
FROM company
GROUP BY id, name
) c
ON c.id = v.company_id
ORDER BY v.id;

SELECT * FROM vacancy_company_info vci;


-- Чтобы получилось красивое облако слов, чистим таблицу description_word от неподходящих слов
-- Просмотреть топ-200 будет достаточно. Это представление будет выгружаться в Python-код
CREATE OR REPLACE VIEW description_word_clean AS
SELECT *
FROM description_word dw
WHERE word NOT IN
('наш', 'быть', 'который', 'and', 'год', 'to', '1', '2', '3', '5', 'больший',
'другой', 'свой', 'the', 'весь', 'один', 'of', 'a', 'тот', 'так', 'in', 'тк')
ORDER BY amount DESC;

SELECT * FROM description_word_clean;


