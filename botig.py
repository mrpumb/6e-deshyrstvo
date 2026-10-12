import asyncio
from datetime import timedelta
from collections import defaultdict
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ChatPermissions

# -------------------------------------------------------------
# Вставьте сюда ваш ТОКЕН от @BotFather:
TOKEN = "8853030772:AAE5DWOyTLD11skfo5mzTPtKAe_CCjC5MgQ"
# -------------------------------------------------------------

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Хранилище счетчика гифок: {user_id: [time1, time2, ...]}
gif_tracker = defaultdict(list)

# Список матов и нецензурных слов для авто-удаления и предупреждения
# (базовый набор, можно дополнять)
BAD_WORDS = {
    "блять", "бля", "сука", "сучка", "ебать", "еблан", "пидор", "пидорас",
    "хуй", "хусос", "гондон", "мудак", "мразь", "урод", "суки", "ебучий",
    "залупа", "шлюха", "блять", "ебаный", "долбоеб", "даун"
}

RULES_TEXT = (
    "📜 **Правила группы класса 6Е**\n\n"
    "• **Докопание:** ограничение на 2 дня (команда `/dok` в ответ)\n"
    "• **Спам:** больше 10 гифок — авто-глушение на 1 день\n"
    "• **Ссоры:** разбор в ссоре — ограничение на 2 дня (команда `/ssora` в ответ)\n"
    "• **Буллинг:** ограничение на 4 дня (команда `/bulling` в ответ)\n"
    "• **Реклама небезопасного контента:** ограничение на 4 дня (команда `/reklama` в ответ)\n"
    "• **Небезопасные и неприличные фото:** ограничение на 6 дней 12 часов (команда `/photo` в ответ)\n"
    "• **Маты / Нецензурная лексика:** авто-удаление сообщений\n\n"
    "Соблюдайте правила, и все будет нормально 🙂"
)

# Вывод правил по команде /rules
@dp.message(Command("rules"))
async def send_rules(message: types.Message):
    await message.answer(RULES_TEXT, parse_mode="Markdown")

# Автоматическая проверка текстов на мат и спам гифками
@dp.message(F.text)
async def check_text_messages(message: types.Message):
    text_lower = message.text.lower()
    # Проверяем каждое слово в сообщении на совпадение с матами
    words = text_lower.split()
    if any(bad in word for bad in BAD_WORDS for word in words):
        try:
            await message.delete()
            warning = await message.answer(
                f"⚠️ @{message.from_user.username or message.from_user.first_name}, "
                f"использование нецензурной лексики запрещено правилами!"
            )
            # Удаляем предупреждение через 5 секунд, чтобы не засорять чат
            await asyncio.sleep(5)
            await warning.delete()
        except Exception:
            pass

# Автоматическая проверка на спам гифками (> 10 гифок за 2 минуты)
@dp.message(F.animation)
async def handle_gifs(message: types.Message):
    user_id = message.from_user.id
    now = message.date.timestamp()

    # Оставляем только гифки за последние 2 минуты
    gif_tracker[user_id] = [t for t in gif_tracker[user_id] if now - t < 120]
    gif_tracker[user_id].append(now)

    if len(gif_tracker[user_id]) > 10:
        until_date = timedelta(days=1)
        try:
            # Сразу глушим пользователя на 1 день
            await message.chat.restrict(
                user_id=user_id,
                permissions=ChatPermissions(can_send_messages=False),
                until_date=until_date
            )
            await message.reply(
                f"🚫 @{message.from_user.username or message.from_user.first_name}, "
                f"превышен лимит гифок (спам)! Выдан мут на **1 день**.",
                parse_mode="Markdown"
            )
            gif_tracker[user_id].clear()
        except Exception:
            await message.reply("Не удалось ограничить пользователя. Проверьте, что бот — администратор.")

# Функция-помощник для ограничения админами по текстовым командам
async def restrict_user(message: types.Message, duration: timedelta, reason: str):
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ["administrator", "creator"]:
        await message.reply("❌ Эта команда доступна только администраторам чата!")
        return

    if not message.reply_to_message:
        await message.reply("⚠️ Ответьте этой командой на сообщение нарушителя!")
        return

    target_user = message.reply_to_message.from_user
    
    try:
        await message.chat.restrict(
            user_id=target_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=duration
        )
        await message.answer(
            f"🚫 **Нарушение правил 6Е!**\n\n"
            f"Пользователь: [{target_user.first_name}](tg://user?id={target_user.id})\n"
            f"Причина: **{reason}**\n"
            f"Ограничение выдано на: **{duration.days} дн. {duration.seconds // 3600} ч.**",
            parse_mode="Markdown"
        )
    except Exception:
        await message.reply("❌ Ошибка. Убедитесь, что бот является администратором чата.")

# Команды модерации для админов
@dp.message(Command("dok"))
async def cmd_dok(message: types.Message):
    await restrict_user(message, timedelta(days=2), "Докопание")

@dp.message(Command("ssora"))
async def cmd_ssora(message: types.Message):
    await restrict_user(message, timedelta(days=2), "Ссоры / Разбор")

@dp.message(Command("bulling"))
async def cmd_bulling(message: types.Message):
    await restrict_user(message, timedelta(days=4), "Буллинг")

@dp.message(Command("reklama"))
async def cmd_reklama(message: types.Message):
    await restrict_user(message, timedelta(days=4), "Реклама небезопасного контента")

@dp.message(Command("photo"))
async def cmd_photo(message: types.Message):
    await restrict_user(message, timedelta(days=6, hours=12), "Небезопасные и неприличные фото")

async def main():
    print("Бот класса 6Е запущен и следит за порядком!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
