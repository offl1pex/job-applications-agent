import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes,
)
from pathlib import Path
from main import Agent  # класс Agent, без автозапуска консоли

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
HISTORY_DIR = Path(__file__).resolve().parent / "chat_histories"
HISTORY_DIR.mkdir(exist_ok=True)
APPS_DIR = Path(__file__).resolve().parent / "applications"
APPS_DIR.mkdir(exist_ok=True)
START_TEXT = """Job Applications Agent

Умею:
• вести отклики (добавить, список, статус, правка, удалить)
• статистику и follow-up
• отвечать по базе docs (Python, агенты, вакансии)

Примеры:
• добавь отклик в Yandex на Python Developer
• покажи отклики
• переведи 1 в interview
• что такое tool_calls

Команды:
/help — справка
/reset — сброс истории диалога
"""

HELP_TEXT = """Отклики:
• добавь отклик в Company на Position
• покажи отклики / покажи applied
• переведи 2 в interview
• измени заметку у 1 на …
• удали отклик 3
• статистика
• что напомнить

База знаний:
• что такое список в Python
• кто такой AI-агент

/reset — очистить историю этого чата
"""

agents = {}


def get_agent(chat_id):
    if chat_id not in agents:
        history = HISTORY_DIR / f"chat_{chat_id}.json"
        apps = APPS_DIR / f"apps_{chat_id}.json"
        a = Agent(history_path=str(history), apps_path=str(apps))
        a.load_messages()
        agents[chat_id] = a
    return agents[chat_id]


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_TEXT)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT)


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    agent = get_agent(chat_id)
    agent.clear()
    agent.messages = [agent.messages[0]]
    await update.message.reply_text("История сброшена. Можешь начать с «добавь отклик…» или /help.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    agent = get_agent(chat_id)
    text = (update.message.text or "").strip()
    if not text:
        await update.message.reply_text("Пустое сообщение.")
        return

    await update.message.chat.send_action("typing")

    try:
        answer = await agent.chat(text)
        if not answer:
            answer = "Пустой ответ модели."

        # лимит Telegram ~4096 символов
        if len(answer) > 4000:
            answer = answer[:4000] + "…"

        await update.message.reply_text(answer)
        agent.save()  # история + trim, как в консоли
    except Exception as e:
        print(f"Error chat_id={chat_id}: {e}")  # себе в терминал
        await update.message.reply_text(
            "Что-то пошло не так. Попробуй ещё раз или /reset.")


def main():
    if not TOKEN:
        raise SystemExit("Нет TELEGRAM_BOT_TOKEN в .env")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен. Ctrl+C — остановить.")
    app.run_polling()


if __name__ == "__main__":
    main()