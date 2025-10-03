-- Direct SQL solution for flat JSON structure
-- This works immediately without any JSON transformation

SELECT 
    candidate_email,
    weighted_values,
    interview_shared_link,
    
    -- Extract each field directly using jsonb_each
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Город проживания' 
     LIMIT 1) AS "город_проживания",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Ваше имя' 
     LIMIT 1) AS "ваше_имя",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Ожидаемая месячная заработная в рублях до вычета НДФЛ' 
     LIMIT 1) AS "ожидаемая_зарплата",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Максимальный бюджет по окладу на позицию: 100 000 руб. ' 
     LIMIT 1) AS "бюджет_позиции",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Quiz Score' 
     LIMIT 1) AS "quiz_score",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Ссылка на резюме' 
     LIMIT 1) AS "ссылка_на_резюме",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Опыт работы в управленческих финансах' 
     LIMIT 1) AS "опыт_управленческих_финансов",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'С какими аспектами управленческой отчётности есть опыт работы?' 
     LIMIT 1) AS "опыт_управленческой_отчетности",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'С какими регулярными процессами есть опыт?' 
     LIMIT 1) AS "опыт_регулярных_процессов",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'В каких проектных задачах участвовали?' 
     LIMIT 1) AS "проектные_задачи",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'С какими инструментами бюджетирования работали?' 
     LIMIT 1) AS "инструменты_бюджетирования",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Какие элементы налогового учёта знакомы на практике?' 
     LIMIT 1) AS "налоговый_учет",
     
    (SELECT value->>'value_text' 
     FROM jsonb_each(answers_json) AS entry(key, value) 
     WHERE value->>'question_title' = 'Ваш Telegram никнейм' 
     LIMIT 1) AS "telegram_никнейм",
     
    first_answer_datetime

FROM public_marts.candidates
WHERE position_name ILIKE '%додо%';
