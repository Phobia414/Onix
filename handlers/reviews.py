from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from keyboards.client_kb import main_menu_kb, review_stars_kb, review_cancel_kb
from config import CHANNEL_ID, ADMIN_ID

router = Router()


class ReviewState(StatesGroup):
    waiting_for_stars = State()
    waiting_for_text = State()


@router.callback_query(F.data.startswith("leave_review"))
async def start_review(callback: CallbackQuery, state: FSMContext):
    # Проверяем, пришли ли мы из конкретной заявки или из главного меню
    order_id = None
    if callback.data.startswith("leave_review_"):
        order_id = int(callback.data.split("_")[2])

    await state.update_data(review_order_id=order_id)

    if callback.message:
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

    if callback.message:
        await callback.message.edit_text(
            f"Ты поставил {stars} ⭐. Спасибо!\n\n"
            "Теперь напиши пару слов о нашей работе (текстом).",
            reply_markup=review_cancel_kb(order_id)  # Передаем order_id для отмены
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

    # Красивое сообщение с кнопкой возврата к заявке (если она есть)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📄 Вернуться к заявке", callback_data=f"view_order_{order_id}")] if order_id else [
            InlineKeyboardButton(text="🏠 В главное меню", callback_data="cancel_action")]
    ])

    await message.answer(
        "❤️ <b>Спасибо за твой отзыв!</b> Мне очень приятно.",
        reply_markup=back_kb
    )

    star_emojis = "⭐" * stars
    channel_post = f"<b>Новый отзыв!</b>\n\n{star_emojis}\n<i>«{review_text}»</i>\n\n— @{message.from_user.username or 'Клиент'}"

    try:
        await bot.send_message(CHANNEL_ID, channel_post)
    except Exception as e:
        await bot.send_message(message.from_user.id, "⚠️ Ой, я не смог отправить отзыв в канал. Но я его сохранил!")
        await bot.send_message(ADMIN_ID, f"🚨 <b>Ошибка отзыва!</b>\nПричина: <code>{e}</code>")