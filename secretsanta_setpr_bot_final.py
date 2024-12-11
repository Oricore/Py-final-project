import random
import redis

from typing import Final
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN: Final = '7821094644:AAHcQ84QSZSKWMFDLUKSWuOXZ5EJd2f7Q5Y'
BOT_USERNAME: Final = '@SecretSanta_SETpr_Bot'
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Щасливих свят! Щоб додати учасників, введіть /add <name>.\n"
        "Побачити список учасників: введіть /list.\n"
        "Видалити учасника із списка: введіть /remove.\n"
        "Зробити розподіл: введіть /assign."
    )

participants = []

async def add_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Додайте нового учасника за допомогою команди /add <name>")
        return
    user_id = update.effective_user.id
    name = ' '.join(context.args)
    if redis_client.sismember(f"participants:{user_id}", name):
        await update.message.reply_text(f"{name} Учасник з таким імʼям вже в списку. Введіть нове імʼя.")
    else:
        redis_client.sadd(f"participants:{user_id}", name)
        await update.message.reply_text(f"Учасника {name} було додано до списку.")

async def remove_participant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(f"Введіть імʼя учасника, якого ви хочете видалити із списка, за допомогою команди /remove <name>")
        return
    name = ' '.join(context.args)
    user_id = update.effective_user.id
    if redis_client.sismember(f"participants:{user_id}", name):
        redis_client.srem(f"participants:{user_id}", name)
        await update.message.reply_text(f"Учасника {name} було видалено із списку.")
    else:
        await udpate.message.reply_text(f"Учасника з таким імʼям немає у списку.")

async def list_participants(update: Update, context):
    user_id = update.effective_user.id
    participants = redis_client.smembers(f"participants:{user_id}")
    if not participants:
        await update.message.reply_text("В списку поки немає учасників. Будь ласка, додайте учасників.")
    else:
        participants_list = [p.decode('utf-8') if isinstance(p, bytes) else p for p in participants]
        await update.message.reply_text("Учасники:\n" + "\n".join(participants_list))

async def assign_pairs(update: Update, context):
    user_id = update.effective_user.id
    participants = list(redis_client.smembers(f"participants:{user_id}"))
    try:
        if len(participants) < 2:
            raise ValueError("Занадто мало учасників для розподілу")
    except ValueError:
        await update.message.reply_text("Для правильного розподілу потрібно хоча б два учасника.")
        return
    except Exception as e:
        await update.message.reply_text(f"Сталася несподівана помилка: {e}")
        return

    santas = participants[:]
    recipients = participants[:]
    while True:
        random.shuffle(recipients)
        if all(santa != recipient for santa, recipient in zip(santas, recipients)):
            break

    for i in range(len(santas)):
        if santas[i] == recipients[i]:
            random.shuffle(recipients)
            break

    pairs = list(zip(santas, recipients))
    result = "\n".join([f"{santa} → {recipient}" for santa, recipient in pairs])
    await update.message.reply_text("Secret Santa пари:\n" + result)


if __name__ == "__main__":
    application = Application.builder().token("7821094644:AAHcQ84QSZSKWMFDLUKSWuOXZ5EJd2f7Q5Y").build()

    # Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_participant))
    application.add_handler(CommandHandler("remove", remove_participant))
    application.add_handler(CommandHandler("list", list_participants))
    application.add_handler(CommandHandler("assign", assign_pairs))

    application.run_polling(poll_interval=3)