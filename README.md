# Foodgram Project

Foodgram - это веб-приложение для публикации рецептов. Пользователи могут создавать свои рецепты, подписываться на других авторов, добавлять рецепты в избранное и создавать списки покупок. Проект состоит из Django REST API бэкенда и React фронтенда, контейнеризованных с использованием Docker Compose.

## Технологический стек

*   **Бэкенд:** Python 3.11, Django 4.x, Django REST Framework
*   **Фронтенд:** React, Node.js 21
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
    Перейдите в директорию бэкенда (`cd backend/foodgram_backend/`) и создайте файл `.env`. Заполните необходимые переменные:
    *   `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: Данные для доступа к БД (должны совпадать с теми, что использует сервис `db` в `docker-compose.yml`).
    *   `POSTGRES_HOST=db`
    *   `POSTGRES_PORT=5432`
    *   `SECRET_KEY`: Секретный ключ Django (сгенерируйте надежный ключ).
    *   `DEBUG`: `True` для разработки, `False` для продакшена.
    *   **(Для автоматического создания суперпользователя)** Добавьте:
        ```dotenv
        DJANGO_SUPERUSER_USERNAME=admin
        DJANGO_SUPERUSER_EMAIL=admin@example.com
        DJANGO_SUPERUSER_PASSWORD=ваш_надежный_пароль
        ```
    Вернитесь в корневую директорию проекта (`cd ../..`).

4.  **Соберите Docker-образы:**
    Перейдите в директорию infra (`cd infra`) и запустите сборку образов
    ```bash
    docker-compose build
    ```

6.  **Запустите сервис базы данных:**
    ```bash
    docker-compose up -d db
    ```
    Подождите немного для инициализации БД.

7.  **Запустите сервис бэкенда:**
    *(Этот шаг нужен, чтобы контейнер существовал для следующих команд `exec` и `cp`)*
    ```bash
    docker-compose up -d backend
    ```

8.  **Восстановите медиафайлы (если есть дамп):**
    Скопируйте медиафайлы из вашей папки `data/media_dump/` в volume, используемый контейнером `backend`.
    ```bash
    # Убедимся, что папка /app/media существует в контейнере
    docker-compose exec backend mkdir -p /app/media

    docker-compose cp ./fixtures/media_dump/. backend:/app/media/
    ```

9.  **Примените миграции Django (обязательно):**
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

10.  **Загрузите начальные данные из фикстуры (если есть):**
    ```bash
    docker-compose exec backend python manage.py loaddata ../data/foodgram_data.json
    ```

11. **Создайте суперпользователя:**
    *   **Вариант А (Автоматически через .env):** Если вы добавили `DJANGO_SUPERUSER_` переменные в `.env`:
        ```bash
        docker-compose exec backend python manage.py createsuperuser --first_name "Ivan" --last_name "Demin" --noinput
        ```
        *(Флаг `--noinput` заставит команду использовать переменные окружения.*
    *   **Вариант Б (Интерактивно):** Если фикстура не содержит админа или вы хотите создать его вручную:
        ```bash
        docker-compose exec backend python manage.py createsuperuser
        ```
        *(Следуйте инструкциям в терминале)*.

12. **Запустите все сервисы:**
    ```bash
    docker-compose up -d
    ```
## Данные пользователей из фикстуры
*   **DirectorDeda**:
    email: `director@deda.ru`
    password: `passwordDirectora123!`
*   **Admin (администратор)**:
    email: `admin@example.com`
    password: `adminPassword123!`
*   **DedDirectora**:
    email: `ded@directora.com`
    password: `passwordDeda123!`

## Использование

*   **Веб-приложение:** Откройте в браузере `http://localhost` или `http://127.0.0.1`.
*   **Админ-панель Django:** `http://localhost/admin/`.
*   **API Документация:** `http://localhost/api/docs/`.

## Команды управления Django

*   **Загрузка ингредиентов:**
    Для загрузки ингредиентов из файла (например, `ingredients.json` или `ingredients.csv`) в папке `data/` (эта директория монтирована в контейнер с Django):
    ```bash
    docker-compose exec backend python manage.py load_ingredients ingredients.json
    ```

## CI/CD

Проект использует GitHub Actions для автоматической проверки кода (linting), сборки Docker-образов и их отправки в Docker Hub при push в ветку `main`. Конфигурацию можно найти в файле `.github/workflows/main.yml`.

## Автор

*   [DedDirectora](https://github.com/DedDirectora2277/)
