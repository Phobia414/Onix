from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.client_kb import (
    main_menu_kb, order_pay_kb, cancel_kb, deliver_result_kb, back_to_main_kb, back_to_info_kb,
    all_bots_kb, calc_complexity, get_time_left,
    BOT_TYPE_NAMES
)
from keyboards.admin_kb import admin_order_kb, STATUSES
from database import create_order, get_user_orders, get_order, update_order_status, delete_order, check_order_reviewed
from config import ADMIN_ID

router = Router()


class OrderState(StatesGroup):
    choosing_type = State()
    waiting_for_task = State()
    waiting_for_budget = State()


class ContactAdminState(StatesGroup):
    waiting_for_message = State()


INTRO_TEXT = (
    "Отлично! Давай создадим заявку.\n\n"
    "Выбери нужные <b>типы ботов</b> (можно несколько из разных категорий).\n"
    "💰 Итоговая сложность и цена определятся автоматически по самому сложному типу.\n\n"
    "Нажми на типы, чтобы отметить, затем — «Готово» 👇"
)


# === НОВАЯ ФУНКЦИЯ: ОТРИСОВКА КАРТОЧКИ ЗАЯВКИ ДЛЯ КЛИЕНТА ===
async def show_order_card_to_client(message, order_id: int):
    order = await get_order(order_id)
    if not order:
        return

    status_text = STATUSES.get(order[7], order[7])
    price_text = f"<b>{order[6]} ₽</b>" if order[6] > 0 else "Рассчитывается"

    card = (
        f"<b>Заявка №{order[0]}</b>\n━━━━━━━━━━━━━━━━━━\n\n"
        f"⚙️ <b>Сложность:</b> {order[2]}\n📌 <b>Тип:</b> {order[3]}\n\n"
        f"📊 <b>Статус:</b> {status_text}\n\n💰 <b>Цена:</b> {price_text}\n\n"
        f"📝 <b>Задача:</b>\n<i>{order[4]}</i>\n\n━━━━━━━━━━━━━━━━━━"
    )

    if order[7] == "closed":
        is_reviewed = await check_order_reviewed(order_id)
        kb_buttons = []
        if not is_reviewed:
            kb_buttons.append([InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data=f"leave_review_{order_id}")])
        kb_buttons.append([InlineKeyboardButton(text="🔙 К заявкам", callback_data="my_orders")])
        kb = InlineKeyboardMarkup(inline_keyboard=kb_buttons)
        await message.edit_text(card, reply_markup=kb)
        return

    if order[7] == "waiting_payment":
        kb = order_pay_kb(order_id, order[6], order[11])
    elif order[7] == "done":
        kb = deliver_result_kb(order_id)
    else:
        kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="🔙 К заявкам", callback_data="my_orders")]])

    await message.edit_text(card, reply_markup=kb)


@router.callback_query(F.data == "new_order")
async def start_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.update_data(bot_types=[])
    await callback.message.edit_text(INTRO_TEXT, reply_markup=all_bots_kb([]))
    await state.set_state(OrderState.choosing_type)
    await callback.answer()


@router.callback_query(OrderState.choosing_type, F.data.startswith("tog_"))
async def toggle_bot_type(callback: CallbackQuery, state: FSMContext):
    code = callback.data.split("_", 1)[1]
    data = await state.get_data()
    selected = list(data.get("bot_types") or [])

    if code in selected:
        selected.remove(code)
    else:
        selected.append(code)

    await state.update_data(bot_types=selected)
    await callback.message.edit_text(INTRO_TEXT, reply_markup=all_bots_kb(selected))
    await callback.answer()


@router.callback_query(OrderState.choosing_type, F.data == "bot_done")
async def bot_done(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected = data.get("bot_types") or []

    if not selected:
        await callback.answer("Сначала выберите хотя бы один тип!", show_alert=True)
        return

    names = [BOT_TYPE_NAMES.get(c, c) for c in selected]
    bot_types_str = ", ".join(names)
    complexity = calc_complexity(selected)

    await state.update_data(bot_types_str=bot_types_str, complexity=complexity)

    await callback.message.edit_text(
        f"✅ <b>Выбрано:</b>\n{bot_types_str}\n\n"
        f"📊 <b>Сложность заявки:</b> {complexity}\n\n"
        "Теперь <b>опиши задачу</b>. Что именно должен делать бот? Какие функции нужны?",
        reply_markup=cancel_kb()
    )
    await state.set_state(OrderState.waiting_for_task)
    await callback.answer()


@router.message(OrderState.waiting_for_task)
async def process_task(message: Message, state: FSMContext):
    if not message.text: return
    await state.update_data(task=message.text)
    await message.answer(
        "Принято! 📝\n\n<b>Какой у тебя примерный бюджет?</b> (напиши числом)",
        reply_markup=cancel_kb()
    )
    await state.set_state(OrderState.waiting_for_budget)


@router.message(OrderState.waiting_for_budget)
async def process_budget(message: Message, state: FSMContext):
    if not message.from_user or not message.text: return
    # Проверка, что бюджет — число
    if not message.text.replace(" ", "").isdigit():
        await message.answer("⚠️ Пожалуйста, напиши бюджет <b>числом</b> (например: 5000).")
        return
    data = await state.get_data()

    order_id = await create_order(
        message.from_user.id,
        data['complexity'],
        data['bot_types_str'],
        data['task'],
        message.text
    )
    await state.clear()

    await message.answer("🎉 <b>Твоя заявка успешно создана!</b>\n\nЯ уже изучаю детали.", reply_markup=main_menu_kb())

    admin_text = (
        f"🚨 <b>НОВАЯ ЗАЯВКА №{order_id}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>Клиент:</b> @{message.from_user.username}\n"
        f"🆔 <code>{message.from_user.id}</code>\n\n"
        f"⚙️ <b>Сложность:</b> {data['complexity']}\n"
        f"🤖 <b>Типы:</b> {data['bot_types_str']}\n"
        f"💰 <b>Бюджет:</b> {message.text} ₽\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Задача:</b>\n<i>{data['task']}</i>"
    )
    await message.bot.send_message(ADMIN_ID, admin_text, reply_markup=admin_order_kb(order_id, "new"))


@router.callback_query(F.data == "my_orders")
async def my_orders(callback: CallbackQuery):
    if not callback.from_user or not callback.message: return
    orders = await get_user_orders(callback.from_user.id)

    if not orders:
        await callback.message.edit_text("У тебя пока нет активных заявок. 📭", reply_markup=main_menu_kb())
        return

    await callback.message.edit_text("📊 <b>Твои заявки:</b>", reply_markup=back_to_main_kb())

    # Ограничиваем до 10 последних, чтобы не спамить
    for o in orders[:10]:
        status_text = STATUSES.get(o[4], o[4])
        price_text = f"<b>{o[3]} ₽</b>" if o[3] > 0 else "Рассчитывается"

        card = (
            f"<b>Заявка №{o[0]}</b>\n━━━━━━━━━━━━━━━━━━\n\n"
            f"📌 <b>Тип:</b> {o[1]}\n\n📊 <b>Статус:</b> {status_text}\n\n"
            f"💰 <b>Цена:</b> {price_text}\n\n📝 <b>Задача:</b>\n<i>{o[2][:50]}...</i>\n\n━━━━━━━━━━━━━━━━━━"
        )
        view_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="📄 Посмотреть заявку", callback_data=f"view_order_{o[0]}")]])

        if o[4] == "waiting_payment":
            await callback.message.answer(card, reply_markup=order_pay_kb(o[0], o[3], o[5]))
        else:
            await callback.message.answer(card, reply_markup=view_kb)

    await callback.answer()


@router.callback_query(F.data.startswith("view_order_"))
async def view_single_order(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await show_order_card_to_client(callback.message, order_id)
    await callback.answer()


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


@router.callback_query(F.data == "referral_menu")
async def show_referral_menu(callback: CallbackQuery):
    text = "🎁 <b>Реферальная программа</b>\n━━━━━━━━━━━━━━━━━━\n\nУ нас действует система «1 заявка = 1 друг».\n\nСкидка <b>10%</b> на заявку, если приведете друга.\n\n1. Перейдите в <b>«Мои заявки»</b>.\n2. Нажмите <b>«Пригласить друга»</b> под заявкой."
    await callback.message.edit_text(text, reply_markup=back_to_info_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("ref_"))
async def generate_ref_link(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split("_")[1])
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{order_id}"
    await callback.message.answer(
        f"🎁 <b>Ссылка для приглашения</b>\n━━━━━━━━━━━━━━━━━━\n\nСкидка 10% для <b>заявки №{order_id}</b>.\n\n<code>{ref_link}</code>")
    await callback.answer()


# --- СТАРЫЕ ОБРАБОТЧИКИ pay_100_/pay_50_ УДАЛЕНЫ (заменены на payments.py) ---


@router.callback_query(F.data.startswith("accept_work_"))
async def accept_work(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await update_order_status(order_id, "closed")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐ Оставить отзыв", callback_data=f"leave_review_{order_id}")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="cancel_action")]
    ])
    await callback.message.edit_text("🎉 <b>Отлично! Спасибо за принятие работы.</b>", reply_markup=kb)
    await callback.bot.send_message(ADMIN_ID, f"✅ Клиент принял работу по заявке №{order_id}.")


@router.callback_query(F.data.startswith("revise_work_"))
async def revise_work(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("✏️ <b>Напиши правки через кнопку «Связь с автором».</b>",
                                     reply_markup=main_menu_kb())
    await callback.bot.send_message(ADMIN_ID, f"✏️ Клиент запросил правки по заявке №{order_id}.")


@router.callback_query(F.data.startswith("refund_"))
async def request_refund(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    await callback.message.edit_text("💸 <b>Запрос на возврат принят.</b>\nЯ свяжусь с вами.",
                                     reply_markup=main_menu_kb())
    await callback.bot.send_message(ADMIN_ID, f"🚨 Клиент запросил ВОЗВРАТ по заявке №{order_id}!")


@router.callback_query(F.data.startswith("contact_admin_"))
async def contact_admin_start(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])
    await state.update_data(contact_order_id=order_id)
    await callback.message.edit_text("✍️ <b>Напиши свое сообщение разработчику по этой заявке:</b>",
                                     reply_markup=cancel_kb())
    await state.set_state(ContactAdminState.waiting_for_message)
    await callback.answer()


@router.message(ContactAdminState.waiting_for_message)
async def contact_admin_send(message: Message, state: FSMContext, bot: Bot):
    if not message.text: return
    data = await state.get_data()
    order_id = data.get('contact_order_id')
    await state.clear()
    await message.answer("✅ Сообщение отправлено разработчику! Я скоро отвечу.", reply_markup=main_menu_kb())
    await bot.send_message(ADMIN_ID,
                           f"💬 <b>Сообщение от клиента по заявке №{order_id}:</b>\nОт: @{message.from_user.username or 'Скрыт'}\n\n{message.text}")


@router.callback_query(F.data.startswith("cancel_to_order_"))
async def cancel_to_order(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    # ИСПРАВЛЕНО: извлекаем order_id из 4-го элемента и передаем в отдельную функцию
    order_id = int(callback.data.split("_")[3])
    await show_order_card_to_client(callback.message, order_id)
    await callback.answer()