## Запуск и тестирование сервиса Async API

1.  выполняем сборку:

        docker network create videoserv_net

        docker-compose -f docker-compose.stor.yml build

        docker-compose build

        docker-compose -f docker-compose.test.yml build

2.  стартуем сервисы хранилищ: Elasticsearch и Redis

        docker-compose -f docker-compose.stor.yml up -d

3. загружаем индексы эластика из дампа (для автоматического функционального и ручного тестирования)

        docker-compose -f docker-compose.dump.yml run --rm load_elastic_dump

4. запускаем сервис API

        docker-compose up -d

5. запускаем функциональные тесты

        docker-compose -f docker-compose.test.yml run --rm asyn_api_func_test

6. смотрим документацию API (в формате OpenAPI)

   http://localhost:8080/api/v1/docs

7. при желании проверяем эндпоинты API вручную

   Эндпоинты для фильмов:

   - Получаем документ по ID: http://localhost:8080/api/v1/film/00705f85-05f0-4495-b0ca-49be5a38d936

   - Получаем ошибку для несуществующего ID: http://localhost:8080/api/v1/film/8c8d98f8-3a20-4dc3-87eb-81260400ab72

   - Получаем все документы (неявно пагинированные): http://localhost:8080/api/v1/film/

   - Получаем документы отсортированные по рейтингу (по возрастанию): http://localhost:8080/api/v1/film/?sort=imdb_rating

   - Получаем документы отсортированные по рейтингу (по убыванию): http://localhost:8080/api/v1/film/?sort=-imdb_rating

   - Получаем все документы с указанием параметров пагинации: http://localhost:8080/api/v1/film/?offset=925&limit=20

   - Получаем ошибку при некорретной пагинации: http://localhost:8080/api/v1/film/?offset=10000

   - Получаем отфильтрованные по одному жанру документы: http://localhost:8080/api/v1/film/?filter[genre]=Comedy

   - Задаем несколько фильтров по жанру: http://localhost:8080/api/v1/film/?sort=imdb_rating&filter[genre]=Comedy&filter[genre]=Drama

   - Ищем фильмы текстовым поиском: http://localhost:8080/api/v1/film/search?query=internet&sort=-imdb_rating

   Эндпоинты для персон:

   - Персона по ID: http://localhost:8080/api/v1/person/1e4110c2-30ba-4a9f-b58c-cf34dd99dae2

   - Получаем результаты по запросу 'smith' в обратно-алфавитном порядке:
  http://localhost:8080/api/v1/person/search/?query=smith&page%5Bnumber%5D=1&page%5Bsize%5D=50&sort=-full_name

   - Фильмы, в которых участвовала персона: http://localhost:8080/api/v1/person/1e4110c2-30ba-4a9f-b58c-cf34dd99dae2/film/

   Эндпоинты для жанров:

   - Жанр по ID: http://localhost:8080/api/v1/genre/ad5cb320-a128-4ec6-ab90-07c6787beaa6

   - Получаем результаты по запросу 'documentary': http://localhost:8080/api/v1/genre/search/?query=documentary?sort=title
