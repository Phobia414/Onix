from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime


# === СПРАВОЧНИКИ ТИПОВ БОТОВ ===
BOT_TYPES = {
    "easy": [
        ("anketa", "Анкетный бот"),
        ("counter", "Бот счетчик"),
        ("info", "Инфо-рассыльщик"),
        ("helper", "Бот помощник"),
    ],
    "medium": [
        ("db", "Бот с Базой Данных"),
        ("booking", "Бот для записи"),
        ("api", "Бот с API"),
        ("quiz", "Квиз-бот"),
        ("shop", "Простой магазин"),
    ],
    "hard": [
        ("auto", "Магазин с автовыдачей"),
        ("admin_panel", "Бот с админ-панелью"),
        ("ai", "Бот с ИИ"),
        ("webapp", "Telegram Web Apps"),
    ]
}

# Отображение с эмодзи (для кнопок)
BOT_TYPE_EMOJI = {
    "anketa": "📝 Анкетный бот",
    "counter": "🔢 Бот счетчик",
    "info": "📢 Инфо-рассыльщик",
    "helper": "🤖 Бот помощник",
    "db": "🗄 Бот с Базой Данных",
    "booking": "📅 Бот для записи",
    "api": "🔗 Бот с API",
    "quiz": "🧩 Квиз-бот",
    "shop": "🛒 Простой магазин",
    "auto": "⚡ Магазин с автовыдачей",
    "admin_panel": "⚙️ Бот с админ-панелью",
    "ai": "🧠 Бот с ИИ",
    "webapp": "🌐 Telegram Web Apps",
}

# Чистые названия (для записи в БД и админ-панели)
BOT_TYPE_NAMES = {code: name for code, name in BOT_TYPE_EMOJI.items()}
# Убираем эмодзи и для чистых имен используем label из BOT_TYPES
BOT_TYPE_NAMES = {code: label for group in BOT_TYPES.values() for code, label in group}


def calc_complexity(selected_codes: list) -> str:
    """Определяет общую сложность заявки по самому сложному выбранному типу."""
    if not selected_codes:
        return "Легкий"
    hard_codes = [c for c, _ in BOT_TYPES["hard"]]
    medium_codes = [c for c, _ in BOT_TYPES["medium"]]
    if any(c in hard_codes for c in selected_codes):
        return "Сложный"
    if any(c in medium_codes for c in selected_codes):
        return "Средний"
    return "Легкий"


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Оставить заявку", callback_data="new_order")],
        [InlineKeyboardButton(text="📊 Мои заявки", callback_data="my_orders")],
        [InlineKeyboardButton(text="⭐ Отзывы", callback_data="view_reviews")],
        [InlineKeyboardButton(text="ℹ️ Информация", callback_data="info_menu")],
        [InlineKeyboardButton(text="💬 Связь со мной", callback_data="contact_me")]
    ])


def info_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Как это работает", callback_data="how_it_works")],
        [InlineKeyboardButton(text="💰 Услуги и цены", callback_data="price_list")],
        [InlineKeyboardButton(text="💳 Оплата и гарантии", callback_data="payment_info")],
        [InlineKeyboardButton(text="💼 Портфолио", callback_data="portfolio")],
        [InlineKeyboardButton(text="🎁 Пригласить друга", callback_data="referral_menu")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")]
    ])


def back_to_info_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Назад в Информацию", callback_data="info_menu")]])


def back_to_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")]])


# === ВСЕ ТИПЫ БОТОВ В ОДНОМ ЭКРАНЕ, СГРУППИРОВАННЫЕ ПО СЛОЖНОСТИ ===
def all_bots_kb(selected: list):
    buttons = []

    buttons.append([InlineKeyboardButton(text="─── 🟢 ЛЕГКИЕ (от 500 ₽) ───", callback_data="ignore")])
    for code, label in BOT_TYPES["easy"]:
        mark = "✅ " if code in selected else "▫️ "
        buttons.append([InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"tog_{code}")])

    buttons.append([InlineKeyboardButton(text="─── 🟡 СРЕДНИЕ (от 1500 ₽) ───", callback_data="ignore")])
    for code, label in BOT_TYPES["medium"]:
        mark = "✅ " if code in selected else "▫️ "
        buttons.append([InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"tog_{code}")])

    buttons.append([InlineKeyboardButton(text="─── 🔴 СЛОЖНЫЕ (от 6000 ₽) ───", callback_data="ignore")])
    for code, label in BOT_TYPES["hard"]:
        mark = "✅ " if code in selected else "▫️ "
        buttons.append([InlineKeyboardButton(text=f"{mark}{label}", callback_data=f"tog_{code}")])

    if selected:
        buttons.append([InlineKeyboardButton(
            text=f"✔️ Готово (выбрано: {len(selected)})", callback_data="bot_done"
        )])

    buttons.append([InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_action")]])


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
        [InlineKeyboardButton(text=f"💳 Оплатить 100% ({price} ₽)", callback_data=f"pay_stars_100_{order_id}")],
        [InlineKeyboardButton(text=f"💰 Предоплата 50% ({int(price / 2)} ₽)", callback_data=f"pay_stars_50_{order_id}")],
        [InlineKeyboardButton(text="🎁 Пригласить друга (-10%)", callback_data=f"ref_{order_id}")],
        [InlineKeyboardButton(text="📄 Посмотреть заявку", callback_data=f"view_order_{order_id}")],
    ]
    time_left = get_time_left(created_at)
    if time_left > 0:
        kb.append([InlineKeyboardButton(text=f"❌ Отменить заявку (осталось {time_left} сек)", callback_data=f"cancel_order_{order_id}")])
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
        [InlineKeyboardButton(text="💬 Связаться с автором", callback_data=f"contact_admin_{order_id}")],
        [InlineKeyboardButton(text="🔙 В главное меню", callback_data="cancel_action")]
    ])