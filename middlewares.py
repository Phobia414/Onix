from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from database import get_user_block_info
from keyboards.block_kb import blocked_menu_kb
from config import ADMIN_ID


class CheckBlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user_id = event.from_user.id

        if user_id == ADMIN_ID:
            return await handler(event, data)

        is_blocked, penalty, order_id = await get_user_block_info(user_id)

        if is_blocked:
            if isinstance(event, CallbackQuery):
                # Разрешаем нажимать на кнопки оплаты и проверки подписки
                if event.data.startswith("pay_penalty_") or event.data.startswith("check_friend_"):
                    return await handler(event, data)
                await event.answer("⚠️ Доступ ограничен. Выберите действие на клавиатуре.", show_alert=True)
            elif isinstance(event, Message):
                await event.answer(
                    f"⚠️ <b>Доступ ограничен.</b>\n\nДля разблокировки необходимо доплатить <b>{penalty} ₽</b>.",
                    reply_markup=blocked_menu_kb(penalty, order_id)
                )
            return
        return await handler(event, data)