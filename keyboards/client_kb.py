from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="new_order")],
        [InlineKeyboardButton(text="💰 Услуги и цены", callback_data="price_list")],
        [InlineKeyboardButton(text="💳 Оплата и гарантии", callback_data="payment_info")],
        [InlineKeyboardButton(text="💼 Портфолио", callback_data="portfolio")],
        [InlineKeyboardButton(text="ℹ️ Как это работает", callback_data="how_it_works")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="leave_review")],
        [InlineKeyboardButton(text="📊 Мои заявки", callback_data="my_orders")],
        [InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral_menu")],
        [InlineKeyboardButton(text="💬 Связь со мной", callback_data="contact_me")]
    ])


def back_to_main_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")]])


# 1. Выбор сложности
def complexity_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Легкие (от 500 ₽)", callback_data="comp_Легкий")],
        [InlineKeyboardButton(text="🟡 Средние (от 1500 ₽)", callback_data="comp_Средний")],
        [InlineKeyboardButton(text="🔴 Сложные (от 6000 ₽)", callback_data="comp_Сложный")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]
    ])


# 2. Кнопки для Легких
def easy_bots_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Анкетный бот", callback_data="bot_Анкетный бот")],
        [InlineKeyboardButton(text="🔢 Бот счетчик", callback_data="bot_Бот счетчик")],
        [InlineKeyboardButton(text="📢 Инфо-рассыльщик", callback_data="bot_Инфо-рассыльщик")],
        [InlineKeyboardButton(text="🤖 Бот помощник", callback_data="bot_Бот помощник")],
        [InlineKeyboardButton(text="🔙 Назад к сложности", callback_data="new_order")]
    ])


# 3. Кнопки для Средних
def medium_bots_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗄 Бот с Базой Данных", callback_data="bot_Бот с БД")],
        [InlineKeyboardButton(text="📅 Бот для записи", callback_data="bot_Бот для записи")],
        [InlineKeyboardButton(text="🔗 Бот с API", callback_data="bot_Бот с API")],
        [InlineKeyboardButton(text="🧩 Квиз-бот", callback_data="bot_Квиз-бот")],
        [InlineKeyboardButton(text="🛒 Простой магазин", callback_data="bot_Простой магазин")],
        [InlineKeyboardButton(text="🔙 Назад к сложности", callback_data="new_order")]
    ])


# 4. Кнопки для Сложных
def hard_bots_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡ Магазин с автовыдачей", callback_data="bot_Магазин с автовыдачей")],
        [InlineKeyboardButton(text="⚙️ Бот с админ-панелью", callback_data="bot_Бот с админ-панелью")],
        [InlineKeyboardButton(text="🧠 Бот с ИИ", callback_data="bot_Бот с ИИ")],
        [InlineKeyboardButton(text="🌐 Telegram Web Apps", callback_data="bot_Web Apps")],
        [InlineKeyboardButton(text="🔙 Назад к сложности", callback_data="new_order")]
    ])


def cancel_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]])


def review_stars_kb(order_id: int = None):
    cancel_cb = f"cancel_to_order_{order_id}" if order_id else "cancel_action"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="1 ⭐", callback_data="star_1"),
         InlineKeyboardButton(text="2 ⭐", callback_data="star_2"),
         InlineKeyboardButton(text="3 ⭐", callback_data="star_3"),
         InlineKeyboardButton(text="4 ⭐", callback_data="star_4"),
         InlineKeyboardButton(text="5 ⭐", callback_data="star_5")],
        [InlineKeyboardButton(text="❌ Назад", callback_data=cancel_cb)]
    ])


def review_cancel_kb(order_id: int = None):
    cancel_cb = f"cancel_to_order_{order_id}" if order_id else "cancel_action"
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Назад", callback_data=cancel_cb)]])


def get_time_left(created_at_str):
    if not created_at_str: return 0
    created_at = datetime.fromisoformat(created_at_str)
    elapsed = (datetime.now() - created_at).total_seconds()
    remaining = 300 - elapsed
    return max(0, int(remaining))


def order_pay_kb(order_id: int, price: int, created_at: str):
    kb = [
        [InlineKeyboardButton(text=f"💳 Оплатить 100% ({price} ₽)", callback_data=f"pay_100_{order_id}")],
        [InlineKeyboardButton(text=f"💰 Предоплата 50% ({int(price / 2)} ₽)", callback_data=f"pay_50_{order_id}")],
        [InlineKeyboardButton(text="🎁 Пригласить друга (-10%)", callback_data=f"ref_{order_id}")],
        [InlineKeyboardButton(text="📄 Посмотреть заявку", callback_data=f"view_order_{order_id}")],
    ]
    time_left = get_time_left(created_at)
    if time_left > 0:
        kb.append([InlineKeyboardButton(text=f"❌ Отменить заявку (осталось {time_left} сек)",
                                        callback_data=f"cancel_order_{order_id}")])
    else:
        kb.append([InlineKeyboardButton(text="❌ Время на отмену истекло", callback_data="ignore")])

    kb.append([InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def deliver_result_kb(order_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Принять работу", callback_data=f"accept_work_{order_id}")],
        [InlineKeyboardButton(text="✏️ Запросить правки", callback_data=f"revise_work_{order_id}")],
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data=f"leave_review_{order_id}")],
        [InlineKeyboardButton(text="📄 Посмотреть заявку", callback_data=f"view_order_{order_id}")],
        [InlineKeyboardButton(text="💸 Запросить возврат", callback_data=f"refund_{order_id}")],
        [InlineKeyboardButton(text="💬 Связаться с автором", url="https://t.me/твой_ник")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")]
    ])