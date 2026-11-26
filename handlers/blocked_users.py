from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from database import block_user, get_order
from keyboards.client_kb import main_menu_kb
from config import CHANNEL_ID

router = Router()


@router.callback_query(F.data.startswith("pay_penalty_"))
async def pay_penalty(callback: CallbackQuery):
    # В реальности тут будет интеграция с ЮKassa. Сейчас - имитация.
    parts = callback.data.split("_")
    order_id = int(parts[2])

    # Разблокируем пользователя
    await block_user(callback.from_user.id, False)

    await callback.message.edit_text(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        "Ваш доступ к боту полностью восстановлен. Спасибо за честность!",
        reply_markup=main_menu_kb()
    )
    await callback.answer("Оплата принята!")


@router.callback_query(F.data.startswith("check_friend_"))
async def check_friend_sub(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split("_")
    order_id = int(parts[2])

    # Получаем инфу о заказе, чтобы узнать ID друга
    order = await get_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    friend_id = order[8]  # friend_id хранится в orders

    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=friend_id)
        if member.status in ["member", "administrator", "creator"]:
            # Друг снова подписан! Снимаем блок
            await block_user(callback.from_user.id, False)
            await callback.message.edit_text(
                "✅ <b>Проверка пройдена!</b>\n\n"
                "Ваш друг снова подписан на канал. Штраф отменен, доступ восстановлен.",
                reply_markup=main_menu_kb()
            )
        else:
            await callback.answer("❌ Ваш друг все еще не подписан на канал!", show_alert=True)
    except Exception:
        await callback.answer("Ошибка проверки. Свяжитесь с админом.", show_alert=True)