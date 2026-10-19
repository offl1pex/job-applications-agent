# Job Applications Agent

Консольный и Telegram AI-агент для учёта откликов на вакансии.

Модель сама выбирает инструменты: добавить/изменить/удалить отклик, сменить статус, статистика, follow-up.  
Дополнительно отвечает по локальной базе документов (RAG: chunks + embeddings).

## Возможности

**Отклики**
- Добавление (компания, должность, ссылка, заметка)
- Список (все или по статусу)
- Редактирование и удаление по id
- Статусы: `applied` → `interview` → `offer` / `rejected` / `ghosted`
- Статистика и follow-up (давно без движения)

**База знаний (RAG)**
- Поиск по файлам в `docs/`
- Нарезка на chunks, embeddings (`text-embedding-3-small`), кэш в `embeddings.json`
- Tool `search_docs` — ответы только по найденному контексту

**Интерфейсы**
- Консоль: `python main.py`
- Telegram-бот: `python bot.py`
- В боте у каждого пользователя своя история чата и свои заявки

## Стек

- Python 3
- OpenAI API (chat + tools + embeddings)
- python-telegram-bot
- python-dotenv
- JSON-хранилище

## Структура

```text
job_agent/
├── main.py              # класс Agent (консоль + логика)
├── bot.py               # Telegram-интерфейс
├── applications.py      # CRUD откликов
├── search.py            # RAG: chunks, embeddings, поиск
├── docs/                # текстовая база знаний
├── requirements.txt
├── README.md
├── .gitignore
├── .env                 # локально, не в git
├── chat_histories/      # истории TG-чатов (не в git)
└── applications/        # заявки по пользователям TG (не в git)