## Создание дампов Elasticsearch

*Используется утилита `elasticdump`: https://github.com/elasticsearch-dump/elasticsearch-dump#elasticdump*

Elasticsearch должен быть запущен. В системе должен быть установлен Node.js. Дампы сохраняем в `./data`. Утилита NPX позволяет запускать пакеты Node.js без инсталляции в систему (имеет смысл для редких задач, чтоб не замусоривать локальный диск). Далее подразуемевается, что мы находимся в корневом каталоге проекта (не в `./data`).

Hа примере индекса `movies` (повторять для каждого индекса):

        npx elasticdump --type data --input http://localhost:9200/movies --output ./data/movies_data.json --overwrite

**Также не забываем сделать вручную json-файл со структурой индекса. См. для примера `./data/movies_index.json`.**
