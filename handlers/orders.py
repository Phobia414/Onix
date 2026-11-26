from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.client_kb import (
    main_menu_kb, order_pay_kb, cancel_kb, deliver_result_kb, back_to_main_kb,
    complexity_kb, easy_bots_kb, medium_bots_kb, hard_bots_kb, get_time_left
)
from keyboards.admin_kb import admin_order_kb, STATUSES
from database import create_order, get_user_orders, get_order, update_order_status, delete_order
from config import ADMIN_ID

router = Router()


class OrderState(StatesGroup):
    choosing_complexity = State()
    choosing_type = State()
    waiting_for_task = State()
    waiting_for_budget = State()


# Тексты прайсов
EASY_TEXT = (
    "🟢 <b>Легкие боты (от 500 ₽)</b>\n"
    "━━━━━━━━━━━━━━━━━\n\n"
    "1. Анкетный бот — передает анкеты пользователей админу\n"
    "2. Бот счетчик — считает количество чего-либо\n"
    "3. Инфо-рассыльщик — для отправки новостей\n"
    "4. Бот помощник — погода, расписания, напоминалки\n\n"
    "👇 <b>Выберите нужный вариант:</b>"
)
MEDIUM_TEXT = (
    "🟡 <b>Средние боты (от 1500 ₽)</b>\n"
    "━━━━━━━━━━━━━━━━━\n\n"
    "1. Боты с БД — сохранение профилей, истории заказов\n"
    "2. Боты для записи — салоны, репетиторы\n"
    "3. Боты с API — отслеживание посылок, курсы валют\n"
    "4. Квиз-боты — тесты с подсчетом баллов\n"
    "5. Простые магазины — каталог, корзина, заявки\n\n"
    "👇 <b>Выберите нужный вариант:</b>"
)
HARD_TEXT = (
    "🔴 <b>Сложные боты (от 6000 ₽)</b>\n"
    "━━━━━━━━━━━━━━━━━\n\n"
    "1. Магазины с автовыдачей — моментальная выдача ключей\n"
    "2. Боты с админ-панелью — управление прямо в боте\n"
    "3. Боты с ИИ — интеграция ChatGPT, генерация картинок\n"
    "4. Telegram Web Apps — полноценные магазины/игры\n\n"
    "👇 <b>Выберите нужный вариант:</b>"
)


# --- СОЗДАНИЕ ЗАЯВКИ (ШАГ 1: Сложность) ---
@router.callback_query(F.data == "new_order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Отлично! Давай создадим заявку.\n\nСначала выбери <b>сложность</b> твоего бота:",
        reply_markup=complexity_kb()
    )
    await state.set_state(OrderState.choosing_complexity)
    await callback.answer()


# --- ШАГ 2: Выбор бота и показ прайса ---
@router.callback_query(OrderState.choosing_complexity, F.data.startswith("comp_"))
async def process_complexity(callback: CallbackQuery, state: FSMContext):
    complexity = callback.data.split("_")[1]  # "Легкий", "Средний" или "Сложный"
    await state.update_data(complexity=complexity)

    if complexity == "Легкий":
        text = EASY_TEXT
        kb = easy_bots_kb()
    elif complexity == "Средний":
        text = MEDIUM_TEXT
        kb = medium_bots_kb()
    else:
        text = HARD_TEXT
        kb = hard_bots_kb()

    await callback.message.edit_text(text, reply_markup=kb)
    await state.set_state(OrderState.choosing_type)
    await callback.answer()


# --- ШАГ 3: Выбор конкретного бота и ввод задачи ---
@router.callback_query(OrderState.choosing_type, F.data.startswith("bot_"))
async def process_type(callback: CallbackQuery, state: FSMContext):
    bot_type = callback.data.split("_")[1]
    await state.update_data(bot_type=bot_type)

    await callback.message.edit_text(
        f"Выбран тип: <b>{bot_type}</b>.\n\n"
        "Теперь <b>опиши задачу</b>. Что именно должен делать бот? Какие функции нужны?",
        reply_markup=cancel_kb()
    )
    await state.set_state(OrderState.waiting_for_task)
    await callback.answer()


@router.message(OrderState.waiting_for_task)
async def process_task(message: Message, state: FSMContext):
    if not message.text: return
    await state.update_data(task=message.text)
    await message.answer("Принято! 📝\n\n<b>Какой у тебя примерный бюджет?</b> (напиши числом)",
                         reply_markup=cancel_kb())
    await state.set_state(OrderState.waiting_for_budget)


@router.message(OrderState.waiting_for_budget)
async def process_budget(message: Message, state: FSMContext):
    if not message.from_user or not message.text: return
    data = await state.get_data()

    # Создаем заявку
    order_id = await create_order(
        message.from_user.id,
        data['complexity'],
        data['bot_type'],
        data['task'],
        message.text
    )
    await state.clear()

    await message.answer("🎉 <b>Твоя заявка успешно создана!</b>\n\nЯ уже изучаю детали.", reply_markup=main_menu_kb())

    # Отправляем в админку
    admin_text = (
        f"🚨 <b>НОВАЯ ЗАЯВКА №{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Клиент:</b> @{message.from_user.username}\n"
        f"🆔 <code>{message.from_user.id}</code>\n\n"
        f"⚙️ <b>Сложность:</b> {data['complexity']}\n"
        f"🤖 <b>Тип:</b> {data['bot_type']}\n"
        f"💰 <b>Бюджет:</b> {message.text} ₽\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Задача:</b>\n<i>{data['task']}</i>"
    )
    await message.bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_order_kb(order_id, "new"))


# --- СПИСОК ЗАЯВОК ---
@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    if not callback.from_user or not callback.message: return
    orders = await get_user_orders(callback.from_user.id)

    if not orders:
        await callback.message.edit_text("У тебя пока нет активных заявок. 📭", reply_markup=main_menu_kb())
        return

    await callback.message.edit_text("📊 <b>Твои заявки:</b>", reply_markup=back_to_main_kb())

    for o in orders:
        # o = (id, bot_type, task, price, status, created_at)
        status_text = STATUSES.get(o[4], o[4])
        price_text = f"<b>{o[3]} ₽</b>" if o[3] > 0 else "Рассчитывается"

        card = (
            f"<b>Заявка №{o[0]}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>Тип:</b> {o[1]}\n\n"
            f"📊 <b>Статус:</b> {status_text}\n\n"
            f"💰 <b>Цена:</b> {price_text}\n\n"
            f"📝 <b>Задача:</b>\n<i>{o[2][:50]}...</i>\n\n"
            f"━━━━━━━━━━━━━━━━━"
        )

        view_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📄 Посмотреть заявку", callback_data=f"view_order_{o[0]}")]])

        if o[4] == "waiting_payment":
            await callback.message.answer(card, reply_markup=order_pay_kb(o[0], o[3], o[5]))
        else:
            await callback.message.answer(card, reply_markup=view_kb)

    await callback.answer()


# --- ПРОСМОТР ЗАЯВКИ (С обработкой статуса "Закрыта") ---
@router.callback_query(F.data.startswith("view_order_"))
async def view_single_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    order = await get_order(order_id)
    if not order:
        await callback.answer("Заявка не найдена", show_alert=True)
        return

    status_text = STATUSES.get(order[7], order[7])
    price_text = f"<b>{order[6]} ₽</b>" if order[6] > 0 else "Рассчитывается"

    card = (
        f"<b>Заявка №{order[0]}</b>\n"
        f"━━━━━━━━━━━━━━━━━\n\n"
        f"⚙️ <b>Сложность:</b> {order[2]}\n"
        f"📌 <b>Тип:</b> {order[3]}\n\n"
        f"📊 <b>Статус:</b> {status_text}\n\n"
        f"💰 <b>Цена:</b> {price_text}\n\n"
        f"📝 <b>Задача:</b>\n<i>{order[4]}</i>\n\n"
        f"━━━━━━━━━━━━━━━━━"
    )

    # Если заявка закрыта, убираем все кнопки действий
    if order[7] == "closed":
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К заявкам", callback_data="my_orders")]])
        await callback.message.edit_text(card, reply_markup=kb)
        await callback.answer()
        return

    if order[7] == "waiting_payment":
        kb = order_pay_kb(order_id, order[6], order[11])
    elif order[7] == "done":
        kb = deliver_result_kb(order_id)
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К заявкам", callback_data="my_orders")]])

    await callback.message.edit_text(card, reply_markup=kb)
    await callback.answer()


# --- ОТМЕНА ЗАЯВКИ ---
@router.callback_query(F.data.startswith("cancel_order_"))
async def cancel_my_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    order = await get_order(order_id)

    time_left = get_time_left(order[11])

    if time_left <= 0:
        await callback.answer("❌ Время на отмену истекло. Свяжитесь с админом.", show_alert=True)
        return

    await delete_order(order_id)
    await callback.message.edit_text("❌ <b>Заявка успешно отменена и удалена.</b>", reply_markup=main_menu_kb())
    await callback.answer("Заявка отменена")


# --- РЕФЕРАЛЬНАЯ ПРОГРАММА ---
@router.callback_query(F.data == "referral_menu")
async def show_referral_menu(callback: CallbackQuery):
    text = "🎁 <b>Реферальная программа</b>\n━━━━━━━━━━━━━━━━━\n\nУ нас действует система «1 заявка = 1 друг».\n\nСкидка <b>10%</b> на заявку, если приведете друга.\n\n1. Перейдите в <b>«Мои заявки»</b>.\n2. Нажмите <b>«Пригласить друга»</b> под заявкой."
    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("ref_"))
async def generate_ref_link(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split("_")[1])
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{order_id}"
    await callback.message.answer(
        f"🎁 <b>Ссылка для приглашения</b>\n━━━━━━━━━━━━━━━━━\n\nСкидка 10% для <b>заявки №{order_id}</b>.\n\n<code>{ref_link}</code>")
    await callback.answer()


# --- ОПЛАТА ---
@router.callback_query(F.data.startswith("pay_100_"))
async def pay_100(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await update_order_status(order_id, "in_work")
    await callback.message.edit_text("✅ <b>Оплата 100% прошла!</b>\nЯ взял заявку в работу.",
                                     reply_markup=main_menu_kb())
    order = await get_order(order_id)
    await callback.bot.send_message(ADMIN_ID, f"💰 Клиент полностью оплатил заявку №{order_id} ({order[6]} ₽)!")


@router.callback_query(F.data.startswith("pay_50_"))
async def pay_50(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await update_order_status(order_id, "in_work")
    await callback.message.edit_text("✅ <b>Предоплата 50% получена!</b>\nЯ взял заявку в работу.",
                                     reply_markup=main_menu_kb())
    order = await get_order(order_id)
    await callback.bot.send_message(ADMIN_ID, f"💰 Клиент внес 50% по заявке №{order_id} ({int(order[6] / 2)} ₽)!")


# --- СДАЧА РАБОТЫ (КЛИЕНТОМ) ---
@router.callback_query(F.data.startswith("accept_work_"))
async def accept_work(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("🎉 <b>Отлично! Спасибо за принятие работы.</b>", reply_markup=main_menu_kb())
    await callback.bot.send_message(ADMIN_ID, f"✅ Клиент принял работу по заявке №{order_id}.")


@router.callback_query(F.data.startswith("revise_work_"))
async def revise_work(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("✏️ <b>Напиши правки через кнопку «Связь со мной».</b>",
                                     reply_markup=main_menu_kb())
    await callback.bot.send_message(ADMIN_ID, f"✏️ Клиент запросил правки по заявке №{order_id}.")


@router.callback_query(F.data.startswith("refund_"))
async def request_refund(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("💸 <b>Запрос на возврат принят.</b>\nЯ свяжусь с вами.",
                                     reply_markup=main_menu_kb())
    await callback.bot.send_message(ADMIN_ID, f"🚨 Клиент запросил ВОЗВРАТ по заявке №{order_id}!")


@router.callback_query(F.data.startswith("cancel_to_order_"))
async def cancel_to_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await view_single_order(callback)