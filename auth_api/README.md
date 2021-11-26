## AUTH Service

Ссылка на репозиторий: [https://github.com/simenshteyn/Auth_sprint_2](https://github.com/simenshteyn/Auth_sprint_2)

OpenAPI design: `/design/authservice_openapi.yaml`

SwaggerUI (in testing profile): [http://localhost:8080](http://localhost:8080)

JaegerUI (in testing profile): [http://localhost:16686](http://localhost:16686/)

**Setup**
1. Create .env file with sample (change the default passwords and secret keys!):

`$ mv env.sample .env`

`$ vi .env`

2. Create OAuth App to use in OAuth authorization process:

 - Vkontakte: [https://vk.com/editapp?act=create](https://vk.com/editapp?act=create)

3. Edit OAuth APP_ID and SECRET key at `.env` file with yours or use default.


4. At OAuth app options fill redirect URI for callbacks:

 - Vkontakte (for testing):
   - http://127.0.0.1:8000/api/v1/oauth/login/callback/vk
   - http://127.0.0.1:8000/api/v1/oauth/signup/callback/vk
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
 
 
 - Use [JaegerUI](http://localhost:16686) (in testing profile) and `@trac` decorator for tracing.
    

 - Clear docker containers with all data:
 
`$ docker-compose down -v`

**Execute superadmin console command:**

`$ docker exec --env FLASK_APP=main -it auth_app flask manage createsuperuser`
