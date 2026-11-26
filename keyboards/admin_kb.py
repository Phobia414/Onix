from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

STATUSES = {
    "new": "🟡 На рассмотрении",
    "in_work": "🔵 В работе",
    "on_hold": "⏸ На паузе",
    "postponed": "⏳ Отложено",
    "need_contact": "❓ Нужно связаться",
    "refused": "🔴 Отказано",
    "waiting_payment": "💳 Ждет оплаты",
    "done": "🟢 Выполнена",
    "closed": "🔒 Закрыта"
}


def admin_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Новые заявки", callback_data="admin_new_orders")],
        [InlineKeyboardButton(text="📋 Все заявки", callback_data="admin_all_orders")],
        [InlineKeyboardButton(text="💼 Управление портфолио", callback_data="admin_portfolio")],
        [InlineKeyboardButton(text="⭐ Управление отзывами", callback_data="admin_reviews")], # НОВОЕ
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Сделать рассылку", callback_data="admin_broadcast")]
    ])


def admin_order_kb(order_id: int, current_status: str):
    builder = InlineKeyboardBuilder()
    if current_status == "done":
        builder.button(text="🔒 Закрыть заявку", callback_data=f"close_order_{order_id}")
    elif current_status != "closed":
        builder.button(text="🔄 Сменить статус", callback_data=f"status_menu_{order_id}")

    if current_status not in ["waiting_payment", "done", "refused", "closed"]:
        builder.button(text="💰 Выставить цену", callback_data=f"set_price_{order_id}")
    if current_status not in ["done", "closed", "refused"]:
        builder.button(text="📦 Сдать работу", callback_data=f"deliver_{order_id}")

    if current_status != "closed":
        builder.button(text="🚫 Заблокировать клиента", callback_data=f"block_{order_id}")

    builder.button(text="🔙 Назад к списку", callback_data="admin_all_orders")
    builder.adjust(1)
    return builder.as_markup()


def admin_status_select_kb(order_id: int):
    builder = InlineKeyboardBuilder()
    for key, name in STATUSES.items():
        if key != "closed":
            builder.button(text=name, callback_data=f"set_status:{key}:{order_id}")
    builder.button(text="🔙 Отмена", callback_data=f"admin_view_{order_id}")
    builder.adjust(1)
    return builder.as_markup()


def admin_orders_list_kb(orders):
    builder = InlineKeyboardBuilder()
    for o in orders:
        status_ru = STATUSES.get(o[6], o[6])
        builder.button(text=f"№{o[0]} | {o[2]} | {status_ru}", callback_data=f"admin_view_{o[0]}")
    builder.button(text="🔙 В админ-меню", callback_data="admin_main_menu")
    builder.adjust(1)
    return builder.as_markup()


def admin_broadcast_confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить и отправить", callback_data="broadcast_confirm")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_main_menu")]
    ])


def admin_portfolio_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить работу", callback_data="add_portfolio")],
        [InlineKeyboardButton(text="🗑 Удалить работу", callback_data="delete_portfolio_menu")],
        [InlineKeyboardButton(text="🔙 В админ-меню", callback_data="admin_main_menu")]
    ])


def delete_portfolio_kb(items):
    builder = InlineKeyboardBuilder()
    for item in items:
        builder.button(text=f"❌ Удалить: {item[1]}", callback_data=f"del_port_{item[0]}")
    builder.button(text="🔙 Назад", callback_data="admin_portfolio")
    builder.adjust(1)
    return builder.as_markup()


def cancel_portfolio_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_portfolio")]])


# НОВАЯ КЛАВИАТУРА ДЛЯ ОТЗЫВОВ
def admin_reviews_list_kb(reviews):
    builder = InlineKeyboardBuilder()
    for r in reviews:
        stars = "⭐" * r[2]
        short_text = r[3][:20] + "..." if len(r[3]) > 20 else r[3]
        builder.button(text=f"{stars} | №{r[1]} | {short_text}", callback_data=f"admin_del_review_{r[0]}")
    builder.button(text="🔙 В админ-меню", callback_data="admin_main_menu")
    builder.adjust(1)
    return builder.as_markup()