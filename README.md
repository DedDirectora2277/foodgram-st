# Foodgram Project

Foodgram - это веб-приложение для публикации рецептов. Пользователи могут создавать свои рецепты, подписываться на других авторов, добавлять рецепты в избранное и создавать списки покупок. Проект состоит из Django REST API бэкенда и React фронтенда, контейнеризованных с использованием Docker Compose.

## Технологический стек

*   **Бэкенд:** Python 3.11, Django 4.x, Django REST Framework, Gunicorn, Psycopg2
*   **Фронтенд:** React, Node.js 21, npm
*   **База данных:** PostgreSQL 13.3
*   **Веб-сервер/Прокси:** Nginx 1.25
*   **Контейнеризация:** Docker, Docker Compose
*   **CI:** GitHub Actions

## Установка и Запуск

Следуйте этим шагам для локального развертывания проекта:

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/DedDirectora2277/foodgram-st.git
    cd foodgram-st
    ```

2.  **Создайте файл окружения (`.env`):**
    Перейдите в директорию бэкенда (например, `cd backend/foodgram_backend/`) и создайте файл `.env`. Вы можете скопировать его из `.env.example`, если он существует (`cp .env.example .env`). Заполните необходимые переменные:
    *   `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Данные для доступа к БД (должны совпадать с теми, что использует сервис `db` в `docker-compose.yml`).
    *   `POSTGRES_HOST=db`
    *   `POSTGRES_PORT=5432`
    *   `SECRET_KEY`: Секретный ключ Django (сгенерируйте надежный ключ).
    *   `DEBUG`: `True` для разработки, `False` для продакшена.
    *   `ALLOWED_HOSTS`: Например, `localhost,127.0.0.1`.
    *   **(Для автоматического создания суперпользователя)** Добавьте:
        ```dotenv
        DJANGO_SUPERUSER_USERNAME=admin
        DJANGO_SUPERUSER_EMAIL=admin@example.com
        DJANGO_SUPERUSER_PASSWORD=ваш_надежный_пароль
        ```
    *   *(Добавьте другие необходимые переменные)*
    Вернитесь в корневую директорию проекта (`cd ../..`).

4.  **Соберите Docker-образы:**
    ```bash
    docker-compose build
    ```

5.  **Запустите сервис базы данных:**
    ```bash
    docker-compose up -d db
    ```
    Подождите 15-30 секунд для инициализации БД.

6.  **Запустите сервис бэкенда:**
    *(Этот шаг нужен, чтобы контейнер существовал для следующих команд `exec` и `cp`)*
    ```bash
    docker-compose up -d backend
    ```

7.  **Восстановите медиафайлы (если есть дамп):**
    Скопируйте медиафайлы из вашей папки `fixtures/media_dump/` в volume, используемый контейнером `backend`.
    ```bash
    # Убедимся, что папка /app/media существует в контейнере
    docker-compose exec backend mkdir -p /app/media

    docker cp ./fixtures/media_dump/. backend:/app/media/
    ```

8.  **Примените миграции Django:**
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

9.  **Загрузите начальные данные из фикстуры (если есть):**
    ```bash
    docker-compose exec backend python manage.py loaddata fixtures/foodgram_data.json
    ```

10. **Создайте суперпользователя:**
    *   **Вариант А (Автоматически через .env):** Если вы добавили `DJANGO_SUPERUSER_` переменные в `.env` и используете стандартный `createsuperuser`:
        ```bash
        # Используем стандартную команду
        docker-compose exec backend python manage.py createsuperuser --first_name "Ivan" --last_name "Demin" --noinput
        ```
        *(Флаг `--noinput` заставит команду использовать переменные окружения. Проверьте вашу модель пользователя - если email обязателен, он тоже должен быть в переменных окружения).*
    *   **Вариант Б (Интерактивно):** Если фикстура не содержит админа или вы предпочитаете создать его вручную:
        ```bash
        docker-compose exec backend python manage.py createsuperuser
        ```
        *(Следуйте инструкциям в терминале)*.

11. **Запустите все сервисы:**
    ```bash
    docker-compose up -d
    ```

## Использование

*   **Веб-приложение:** Откройте в браузере `http://localhost` или `http://127.0.0.1`.
*   **Админ-панель Django:** `http://localhost/admin/`.
*   **API Документация:** `http://localhost/api/docs/`.

## Команды управления Django

*   **Загрузка ингредиентов:**
    Для загрузки ингредиентов из файла (например, `ingredients.json` или `ingredients.csv`) в папке `data/`:
    ```bash
    # Убедитесь, что файл существует в ./data/ на хосте
    # и volume (../data:/app/fixtures) настроен в docker-compose.yml
    docker-compose exec backend python manage.py load_ingredients ingredients.json
    ```

## CI/CD

Проект использует GitHub Actions для автоматической проверки кода (linting), сборки Docker-образов и их отправки в Docker Hub при push в ветку `main`. Конфигурацию можно найти в файле `.github/workflows/main.yml`.

## Автор

*   [DedDirectora]
