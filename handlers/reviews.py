from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.client_kb import main_menu_kb, review_stars_kb, review_cancel_kb, back_to_main_kb
from database import add_review, check_order_reviewed, get_reviews_stats, get_recent_reviews, get_order
from config import CHANNEL_ID, ADMIN_ID

router = Router()


class ReviewState(StatesGroup):
    waiting_for_stars = State()
    waiting_for_text = State()


# --- ПРОСМОТР ОТЗЫВОВ (ИЗ ГЛАВНОГО МЕНЮ) ---
@router.callback_query(F.data == "view_reviews")
async def show_reviews(callback: CallbackQuery):
    count, avg = await get_reviews_stats()

    if count == 0:
        text = "⭐ <b>Отзывы</b>\n\nПока отзывов нет. Станьте первым, кто оценит мою работу!"
        await callback.message.edit_text(text, reply_markup=back_to_main_kb())
        await callback.answer()
        return

    recent = await get_recent_reviews(5)

    text = f"⭐ <b>Отзывы клиентов</b>\n"
    text += f"━━━━━━━━━━━━━━━━━━\n"
    text += f"📊 <b>Средняя оценка:</b> {avg} из 5.0\n"
    text += f"💬 <b>Всего отзывов:</b> {count}\n"
    text += f"━━━━━━━━━━━━━━━━━━\n\n"

    for r in recent:
        stars = "⭐" * r[0]
        short_text = r[1] if len(r[1]) <= 100 else r[1][:100] + "..."
        text += f"{stars}\n<i>«{short_text}»</i>\n\n"

    text += "👇 <i>Чтобы оставить свой отзыв, дождитесь выполнения вашей заявки.</i>"

    await callback.message.edit_text(text, reply_markup=back_to_main_kb())
    await callback.answer()


# --- СОЗДАНИЕ ОТЗЫВА (ИЗ КАРТОЧКИ ЗАЯВКИ) ---
@router.callback_query(F.data.startswith("leave_review_"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    order_id = int(callback.data.split("_")[2])

    # ПРОВЕРКА 1: Существует ли заказ и выполнен ли он?
    order = await get_order(order_id)
    if not order or order[7] not in ["done", "closed"]:
        await callback.answer("❌ Вы можете оставить отзыв только после выполнения заявки!", show_alert=True)
        return

    # ПРОВЕРКА 2: Не оставлял ли уже отзыв?
    if await check_order_reviewed(order_id):
        await callback.answer("⚠️ Вы уже оставили отзыв по этой заявке!", show_alert=True)
        return

    await state.update_data(review_order_id=order_id)
    await callback.message.edit_text(
        "⭐ <b>Оцени мою работу!</b>\n\n"
        "Поставь оценку от 1 до 5 звезд. Твое мнение очень важно для меня!",
        reply_markup=review_stars_kb(order_id)
    )
    await state.set_state(ReviewState.waiting_for_stars)
    await callback.answer()


@router.callback_query(ReviewState.waiting_for_stars, F.data.startswith("star_"))
async def process_stars(callback: CallbackQuery, state: FSMContext):
    stars = int(callback.data.split("_")[1])
    data = await state.get_data()
    order_id = data.get('review_order_id')
    await state.update_data(stars=stars)

    await callback.message.edit_text(
        f"Ты поставил {stars} ⭐. Спасибо!\n\n"
        "Теперь напиши пару слов о нашей работе (текстом).",
        reply_markup=review_cancel_kb(order_id)
    )
    await state.set_state(ReviewState.waiting_for_text)
    await callback.answer()


@router.message(ReviewState.waiting_for_text)
async def process_review_text(message: Message, state: FSMContext, bot: Bot):
    if not message.text: return
    data = await state.get_data()
    stars = data.get('stars', 5)
    review_text = message.text
    order_id = data.get('review_order_id')

    await state.clear()

    # Сохраняем в БД
    await add_review(order_id, message.from_user.id, stars, review_text)

    # Отправляем в канал
    star_emojis = "⭐" * stars
    channel_post = f"<b>Новый отзыв!</b>\n\n{star_emojis}\n<i>«{review_text}»</i>\n\n— @{message.from_user.username or 'Клиент'}"
    try:
        await bot.send_message(CHANNEL_ID, channel_post)
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"🚨 <b>Ошибка отправки отзыва в канал!</b>\nПричина: <code>{e}</code>")

    # Сообщение клиенту
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Вернуться к заявке", callback_data=f"view_order_{order_id}")],
        [InlineKeyboardButton(text="🏠 В главное меню", callback_data="cancel_action")]
    ])
    await message.answer(
        "❤️ <b>Спасибо за твой отзыв!</b>\n\nОн успешно сохранен и отправлен в наш канал.",
        reply_markup=back_kb
    )