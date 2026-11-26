import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import CHANNEL_ID
from database import get_orders_to_check, block_user
from keyboards.block_kb import blocked_menu_kb

scheduler = AsyncIOScheduler()


async def check_referrals(bot: Bot):
    logging.info("Запуск проверки рефералов (7 дней)...")
    orders = await get_orders_to_check()
    for order_id, client_id, friend_id, current_price in orders:
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=friend_id)
            if member.status not in ["member", "administrator", "creator"]:
                # Считаем штраф (10% от полной цены). Полная цена = текущая * 1.1
                # Или просто 10% от текущей цены делить на 0.9.
                # Проще: штраф = (текущая_цена / 9). (4500 / 9 = 500)
                penalty = int(current_price / 9)
                if penalty == 0: penalty = 50  # минимальный штраф

                await block_user(client_id, True, penalty, order_id)

                await bot.send_message(
                    client_id,
                    f"⚠️ <b>Ваш друг отписался от нашего канала!</b>\n\n"
                    f"Скидка по заявке №{order_id} аннулирована. Ваш доступ ограничен.\n"
                    f"Чтобы разблокироваться, вам нужно доплатить скидку: <b>{penalty} ₽</b>.",
                    reply_markup=blocked_menu_kb(penalty, order_id)
                )
                logging.info(f"Клиент {client_id} заблокирован. Штраф: {penalty} руб.")
        except Exception as e:
            logging.error(f"Ошибка проверки {friend_id}: {e}")


def setup_scheduler(bot: Bot):
    scheduler.add_job(check_referrals, 'interval', hours=1, args=(bot,))
    scheduler.start()