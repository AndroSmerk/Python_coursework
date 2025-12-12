# Finance Tracker API

API для учета личных финансов: категории доходов/расходов и операции (FastAPI + async SQLAlchemy + JWT). Документация доступна на `/docs`. Мини-фронт доступен на `/ui`.

## Запуск локально
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
База создается автоматически в файле `app.db`. Переменные окружения:
- `DATABASE_URL` — строка подключения (по умолчанию `sqlite+aiosqlite:///./app.db`)
- `JWT_SECRET` — секрет для подписи токенов (обязательно переопределить в продакшене)

## Пример использования
1. `POST /auth/register` — регистрация (JSON: `login`, `password`, `full_name`).
2. `POST /auth/token` — получить JWT (форма `username`, `password`).
3. Работать с защищенными эндпоинтами, передавая `Authorization: Bearer <token>`.

### CRUD
- `POST /categories` — создать категорию (`kind`: income/expense)
- `GET /categories`, `GET /categories/{id}`, `PUT/DELETE /categories/{id}`
- `POST /transactions` — создать операцию (сумма, категория, дата, описание)
- `GET /transactions`, `GET /transactions/{id}`, `PUT/DELETE /transactions/{id}`
- `GET /transactions/summary` — итог по категориям и типам

### Простой фронт
Откройте `http://127.0.0.1:8000/ui`: формы регистрации/логина, создание/удаление категорий, создание/удаление операций и их список.

## Деплой на PythonAnywhere (кратко)
1. Создайте новое веб-приложение с опцией Manual config.
2. Виртуальное окружение: `python -m venv ~/.virtualenvs/myapp && source ~/.virtualenvs/myapp/bin/activate`.
3. Скопируйте код (git clone или upload), установите зависимости: `pip install -r requirements.txt`.
4. Укажите WSGI config на `app.main:app` через `uvicorn.workers.UvicornWorker` (см. образец в документации PythonAnywhere).
5. Задайте переменные окружения `DATABASE_URL`, `JWT_SECRET` в веб-настройках.
6. Перезапустите веб-приложение.

## Примечания
- Используется bcrypt для хеширования паролей.
- Все DB-операции асинхронны.
- Pydantic v2 + FastAPI 0.115+.

