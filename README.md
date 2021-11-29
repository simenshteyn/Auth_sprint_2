## AUTH Service

Ссылка на репозиторий: [https://github.com/simenshteyn/Auth_sprint_2](https://github.com/simenshteyn/Auth_sprint_2)

OpenAPI design: `/design/authservice_openapi.yaml`

SwaggerUI (in testing profile): [http://localhost:8081](http://localhost:8081)

JaegerUI (in testing profile): [http://localhost:16686](http://localhost:16686/)

**Before Setup you should start AsyncAPI Service for integration tests**

`$ cd async_api/`

1.  Make build:

`$ docker network create videoserv_net`

`$ docker-compose -f docker-compose.stor.yml build`

`$ docker-compose build`

`$ docker-compose -f docker-compose.test.yml build`

2.  Start storage: Elasticsearch and Redis:

`$ docker-compose -f docker-compose.stor.yml up -d`

3. Load data from dump for testing (take some time):

`$ docker-compose -f docker-compose.dump.yml run --rm load_elastic_dump`

4. Start Async API service:

`$ docker-compose up -d`

**Setup Auth Service**

`$ cd auth_api/`

1. Create .env file with sample (change the default passwords and secret keys!):

`$ mv env.sample .env`

`$ vi .env`

2. Create OAuth App to use in OAuth authorization process:

 - vk: [https://vk.com/editapp?act=create](https://vk.com/editapp?act=create) (scope: email)
 - yandex: [https://oauth.yandex.ru/client/new](https://oauth.yandex.ru/client/new) (scopes: email; login, name, gender)

3. Edit OAuth APP_ID and SECRET key at `.env` file with yours or use default.


4. At OAuth app options fill redirect URI for callbacks with provider name (`vk` or `yandex`):

   - http://localhost:8000/api/v1/oauth/login/callback/vk
   - http://localhost:8000/api/v1/oauth/signup/callback/vk


**Run project without tests**

 - standard Flask app:

`$ docker-compose up --build`

 - gevent-based Flask app:

`$ docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build`


**Testing**
 - Running tests against the *standard* Flask app:
   
`$ docker-compose --profile=testing up --build`
   
 - Running tests against *gevent-based* Flask app:

`$  docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile=testing up --build`

 - OAuth testing (manual for security):
   - Vkontakte:
     1. Login: [http://localhost:8000/api/v1/oauth/login/vk](http://localhost:8000/api/v1/oauth/login/vk) (no account, will fail)
     2. Signup: [http://localhost:8000/api/v1/oauth/signup/vk](http://localhost:8000/api/v1/oauth/signup/vk) (will create account)
     3. Login again: [http://localhost:8000/api/v1/oauth/login/vk](http://localhost:8000/api/v1/oauth/login/vk) (will succeed)
   - Yandex:
     1. Login: [http://localhost:8000/api/v1/oauth/login/yandex](http://localhost:8000/api/v1/oauth/login/yandex) (no account, will fail)
     2. Signup: [http://localhost:8000/api/v1/oauth/signup/yandex](http://localhost:8000/api/v1/oauth/signup/yandex) (will create account)
     3. Login again: [http://localhost:8000/api/v1/oauth/login/yandex](http://localhost:8000/api/v1/oauth/login/yandex) (will succeed)

 
 
 - Use [JaegerUI](http://localhost:16686) (in testing profile) and `@trac` decorator for tracing.
    

 - Clear docker containers with all data:
 
`$ docker-compose down -v`

**Execute superadmin console command to create superuser:**

`$ docker exec --env FLASK_APP=main -it auth_app flask manage createsuperuser`
