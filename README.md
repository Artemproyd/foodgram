### Проект Foodgram

**Foodgram** - продуктовый помощник.

Пользователи **Foodgram** могут публиковать рецепты (**Recipes**), подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а перед походом в магазин скачивать в формате .txt сводный список продуктов (**Ingredients**), необходимых для приготовления одного или нескольких выбранных блюд.

Для удобства навигации по сайту рецепты размечены тэгами (**Tags**)

### Технологии

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/nginx-%23009639.svg?style=for-the-badge&logo=nginx&logoColor=white)
![Gunicorn](https://img.shields.io/badge/gunicorn-%298729.svg?style=for-the-badge&logo=gunicorn&logoColor=white)
![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![DjangoREST](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)

### Инструкция для разворачивания проекта на удаленном сервере:

- Склонируйте проект из репозитория:

```sh
$ git clone https://github.com/Artemproyd/foodgram.git
```

- Выполните вход на удаленный сервер

- Установите DOCKER на сервер:
```sh
apt install docker.io 
```

- Установитe docker-compose на сервер:
```sh
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

- Отредактируйте конфигурацию сервера NGNIX:
```sh
Локально измените файл ..infra/nginx.conf - замените данные в строке server_name на IP-адрес удаленного сервера
```

- Скопируйте файлы docker-compose.yml и nginx.conf из директории ../infra/ на удаленный сервер:
```sh
scp docker-compose.yml <username>@<host>:/home/<username>/docker-compose.yaml
scp nginx.conf <username>@<host>:/home/<username>/nginx.conf
```
- Создайте переменные окружения (указаны в файле ../infra/env.example) и добавьте их в Secrets GitHub Actions

- Установите и активируйте виртуальное окружение (для Windows):

```sh
python -m venv venv 
source venv/Scripts/activate
python -m pip install --upgrade pip
``` 

- Запустите приложение в контейнерах:

```sh
docker-compose up -d --build
```

- Выполните миграции:

```sh
docker-compose exec backend python manage.py migrate
```

- Создайте суперпользователя:

```sh
docker-compose exec backend python manage.py createsuperuser
```

- Выполните команду для сбора статики:

```sh
docker-compose exec backend python manage.py collectstatic --no-input
```

- Команда для остановки приложения в контейнерах:

```sh
docker-compose down -v
```

### Для запуска на локальной машине:

- Склонируйте проект из репозитория:

```sh
$ git clone https://github.com/Artemproyd/foodgram.git
```

- В папке ../infra/ переименуйте файл example.env в .env и заполните своими данными:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432
SECRET_KEY=<...> # секретный ключ django-проекта из settings.py
```

- Создайте и запустите контейнеры Docker (по инструкции выше).

После запуска проект будут доступен по адресу: [http://localhost/](http://localhost/)

Проект развернут по IP [158.160.4.212](http://158.160.4.212/)

Доступ в админ-панель:
```sh
http://kik0f00dgram.ddns.net/admin
login: admin (ap@list.ru)
pass: 1234
```

### Автор

Артём Пройдаков
