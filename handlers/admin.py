from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import (
    get_all_new_orders, get_all_orders, set_order_price, get_order,
    block_user, deliver_order, update_order_status, get_stats, get_all_users,
    add_portfolio, get_portfolio, delete_portfolio
)
from keyboards.admin_kb import (
    admin_menu_kb, admin_order_kb, admin_broadcast_confirm_kb,
    admin_orders_list_kb, admin_status_select_kb, STATUSES,
    admin_portfolio_menu_kb, delete_portfolio_kb, cancel_portfolio_kb
)
from keyboards.client_kb import deliver_result_kb, order_pay_kb
from keyboards.block_kb import blocked_menu_kb
from config import ADMIN_ID

router = Router()


class AdminState(StatesGroup):
    waiting_for_price = State()
    waiting_for_file = State()
    waiting_for_broadcast = State()
    waiting_for_title = State()
    waiting_for_desc = State()
    waiting_for_photo = State()
    waiting_for_link = State()


async def show_order_card(message: Message, order_id: int):
    order = await get_order(order_id)
    if not order: return

    status_ru = STATUSES.get(order[7], order[7])
    text = (
        f"📦 <b>Заявка №{order[0]}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"👤 <b>ID клиента:</b> <code>{order[1]}</code>\n\n"
        f"⚙️ <b>Сложность:</b> {order[2]}\n"
        f"🤖 <b>Тип:</b> {order[3]}\n\n"
        f"💰 <b>Бюджет:</b> {order[5]} ₽ | <b>Цена:</b> {order[6]} ₽\n\n"
        f"📊 <b>Статус:</b> {status_ru}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Задача:</b>\n<i>{order[4]}</i>"
    )
    await message.edit_text(text, reply_markup=admin_order_kb(order[0], order[7]))


@router.message(Command("admin"))
async def admin_start(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_ID: return
    await message.answer("👑 <b>Главное меню администратора</b>", reply_markup=admin_menu_kb())


@router.callback_query(F.data == "admin_main_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("👑 <b>Главное меню администратора</b>", reply_markup=admin_menu_kb())
    await callback.answer()


# --- ЗАКРЫТИЕ ЗАЯВКИ ---
@router.callback_query(F.data.startswith("close_order_"))
async def close_order(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[2])

    await update_order_status(order_id, "closed")
    await callback.answer("Заявка успешно закрыта и архивирована!", show_alert=True)

    order = await get_order(order_id)
    if order:
        await callback.bot.send_message(
            order[1],
            f"🔒 <b>Заявка №{order_id} закрыта.</b>\n\nСпасибо за сотрудничество! Если понадобится помощь снова — я всегда на связи."
        )
    await show_order_card(callback.message, order_id)


# --- ОСТАЛЬНЫЕ ФУНКЦИИ ---
@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    users_count, orders_count, total_earned = await get_stats()
    text = (
        "📊 <b>Статистика бота</b>\n━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n\n"
        f"📦 Всего заявок: <b>{orders_count}</b>\n\n"
        f"💵 Заработано: <b>{total_earned} ₽</b>\n\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, reply_markup=admin_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "admin_all_orders")
async def admin_all_orders(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    orders = await get_all_orders()
    if not orders:
        await callback.message.edit_text("В базе пока нет ни одной заявки.", reply_markup=admin_menu_kb())
        return
    await callback.message.edit_text("📋 <b>Выберите заявку:</b>", reply_markup=admin_orders_list_kb(orders))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_view_"))
async def admin_view_order(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[2])
    await show_order_card(callback.message, order_id)
    await callback.answer()


@router.callback_query(F.data.startswith("status_menu_"))
async def open_status_menu(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[2])
    await callback.message.edit_text("🔄 <b>Выберите новый статус:</b>", reply_markup=admin_status_select_kb(order_id))
    await callback.answer()


@router.callback_query(F.data.startswith("set_status:"))
async def process_status_change(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    try:
        parts = callback.data.split(":")
        status = parts[1]
        order_id = int(parts[2])

        await update_order_status(order_id, status)
        await callback.answer(f"Статус изменен на {STATUSES.get(status, status)}")

        order = await get_order(order_id)
        if order:
            await callback.bot.send_message(order[1],
                                            f"📊 <b>Статус заявки №{order_id} обновлен:</b> <b>{STATUSES.get(status, status)}</b>")
        await show_order_card(callback.message, order_id)
    except Exception as e:
        await callback.answer(f"Ошибка: {e}", show_alert=True)


@router.callback_query(F.data.startswith("set_price_"))
async def set_price_start(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[2])
    await state.update_data(order_id=order_id)
    await callback.message.edit_text(f"Введи цену для заявки №{order_id}:")
    await state.set_state(AdminState.waiting_for_price)
    await callback.answer()


@router.message(AdminState.waiting_for_price)
async def set_price_finish(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit(): return
    data = await state.get_data()
    order_id = data['order_id']
    await set_order_price(order_id, int(message.text))
    await state.clear()

    await message.answer(f"✅ Цена установлена.")
    order = await get_order(order_id)
    if order:
        kb = order_pay_kb(order_id, order[6], order[11])
        await message.bot.send_message(order[1], f"💰 По заявке №{order_id} установлена цена: <b>{message.text} ₽</b>.",
                                       reply_markup=kb)


@router.callback_query(F.data.startswith("deliver_"))
async def deliver_start(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[1])
    await state.update_data(order_id=order_id)
    await callback.message.edit_text(f"Отправь файл или текст для сдачи заявки №{order_id}:")
    await state.set_state(AdminState.waiting_for_file)
    await callback.answer()


@router.message(AdminState.waiting_for_file)
async def deliver_finish(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data['order_id']
    await deliver_order(order_id)
    await state.clear()

    order = await get_order(order_id)
    if order:
        chat_id = order[1]
        await message.bot.send_message(chat_id,
                                       f"📦 <b>Заявка №{order_id}</b>\n━━━━━━━━━━━━━━━━━━\n<i>Работа готова! Проверьте:</i>")
        await message.bot.copy_message(chat_id=chat_id, from_chat_id=message.chat.id, message_id=message.message_id)
        await message.bot.send_message(chat_id, "👇 <b>Выберите действие:</b>", reply_markup=deliver_result_kb(order_id))

    await message.answer("✅ Работа сдана. Ожидаем решения клиента.")


@router.callback_query(F.data.startswith("block_"))
async def block_client(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    order_id = int(callback.data.split("_")[1])
    order = await get_order(order_id)
    if order:
        if order[1] == ADMIN_ID:
            await callback.answer("Нельзя заблокировать себя!", show_alert=True)
            return
        await block_user(order[1], True)
        await callback.answer(f"Заблокирован", show_alert=True)
        await callback.bot.send_message(order[1], "⚠️ <b>Доступ ограничен.</b>", reply_markup=blocked_menu_kb())


@router.callback_query(F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("📢 <b>Отправь сообщение для рассылки:</b>",
                                     reply_markup=admin_broadcast_confirm_kb())
    await state.set_state(AdminState.waiting_for_broadcast)
    await callback.answer()


@router.message(AdminState.waiting_for_broadcast)
async def broadcast_preview(message: Message, state: FSMContext):
    if not message.from_user or message.from_user.id != ADMIN_ID: return
    await state.update_data(broadcast_msg_id=message.message_id, chat_id=message.chat.id)
    await message.answer("👀 <b>Превью.</b> Отправляем?", reply_markup=admin_broadcast_confirm_kb())


@router.callback_query(F.data == "broadcast_confirm")
async def broadcast_do(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    data = await state.get_data()
    msg_id, from_chat = data.get('broadcast_msg_id'), data.get('chat_id')
    if not msg_id: return
    users = await get_all_users()
    success = 0
    await callback.message.edit_text("⏳ Начинаю рассылку...")
    for u in users:
        try:
            await bot.copy_message(chat_id=u[0], from_chat_id=from_chat, message_id=msg_id)
            success += 1
        except Exception:
            pass
    await callback.message.edit_text(f"✅ Доставлено: {success} из {len(users)}")
    await state.clear()


@router.callback_query(F.data == "admin_portfolio")
async def portfolio_menu(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    await state.clear()
    await callback.message.edit_text("💼 <b>Управление портфолио</b>", reply_markup=admin_portfolio_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "add_portfolio")
async def add_portfolio_start(callback: CallbackQuery, state: FSMContext):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    await callback.message.edit_text("➕ <b>Шаг 1 из 4.</b> Введите название:", reply_markup=cancel_portfolio_kb())
    await state.set_state(AdminState.waiting_for_title)
    await callback.answer()


@router.message(AdminState.waiting_for_title)
async def portfolio_title(message: Message, state: FSMContext):
    if not message.text: return
    await state.update_data(title=message.text)
    await message.answer("Шаг 2 из 4. Введите описание:", reply_markup=cancel_portfolio_kb())
    await state.set_state(AdminState.waiting_for_desc)


@router.message(AdminState.waiting_for_desc)
async def portfolio_desc(message: Message, state: FSMContext):
    if not message.text: return
    await state.update_data(desc=message.text)
    await message.answer("Шаг 3 из 4. Отправьте фото (или /skip):", reply_markup=cancel_portfolio_kb())
    await state.set_state(AdminState.waiting_for_photo)


@router.message(AdminState.waiting_for_photo)
async def portfolio_photo(message: Message, state: FSMContext):
    photo_id = ""
    if message.photo:
        photo_id = message.photo[-1].file_id
    elif message.text and message.text != "/skip":
        await message.answer("Отправьте ФОТО или /skip.")
        return
    await state.update_data(photo_id=photo_id)
    await message.answer("Шаг 4 из 4. Отправьте ссылку (или /skip):", reply_markup=cancel_portfolio_kb())
    await state.set_state(AdminState.waiting_for_link)


@router.message(AdminState.waiting_for_link)
async def portfolio_link(message: Message, state: FSMContext):
    link = ""
    if message.text and message.text != "/skip": link = message.text
    data = await state.get_data()
    await add_portfolio(data['title'], data['desc'], data['photo_id'], link)
    await state.clear()
    await message.answer("✅ <b>Работа добавлена!</b>", reply_markup=admin_portfolio_menu_kb())


@router.callback_query(F.data == "delete_portfolio_menu")
async def delete_portfolio_menu(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    items = await get_portfolio()
    if not items:
        await callback.answer("Портфолио пустое.", show_alert=True)
        return
    await callback.message.edit_text("🗑 <b>Выберите работу для удаления:</b>", reply_markup=delete_portfolio_kb(items))
    await callback.answer()


@router.callback_query(F.data.startswith("del_port_"))
async def delete_portfolio_item(callback: CallbackQuery):
    if not callback.from_user or callback.from_user.id != ADMIN_ID: return
    item_id = int(callback.data.split("_")[2])
    await delete_portfolio(item_id)
    await callback.answer("Удалено!", show_alert=True)
    await callback.message.edit_text("💼 <b>Управление портфолио</b>", reply_markup=admin_portfolio_menu_kb())