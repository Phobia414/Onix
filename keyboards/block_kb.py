from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def blocked_menu_kb(penalty: int = 0, order_id: int = 0):
    kb = []
    if penalty > 0:
        kb.append([InlineKeyboardButton(text=f"💳 Оплатить штраф ({penalty} ₽)",
                                        callback_data=f"pay_penalty_{order_id}_{penalty}")])

    if order_id > 0:
        kb.append([InlineKeyboardButton(text="🔗 Проверить подписку друга", callback_data=f"check_friend_{order_id}")])

    kb.append(
        [InlineKeyboardButton(text="💬 Связаться с Владельцем", url="https://t.me/твой_ник")])  # Замени на свой ник!
    return InlineKeyboardMarkup(inline_keyboard=kb)