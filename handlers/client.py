from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
# Добавлены импорты для нового меню информации
from keyboards.client_kb import (
    main_menu_kb, cancel_kb, back_to_main_kb,
    info_menu_kb, back_to_info_kb
)
from database import add_user, get_portfolio
from config import ADMIN_ID

router = Router()


class ContactState(StatesGroup):
    waiting_for_message = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    if not message.from_user: return
    await add_user(message.from_user.id, message.from_user.username or "NoUsername")
    text = (
        "👋 <b>Приветствую!</b>\n\n"
        "Рад видеть тебя в моем боте. Я профессионально разрабатываю Telegram-ботов под ключ.\n\n"
        "Выбирай нужный раздел и давай начнем! 👇"
    )
    await message.answer(text, reply_markup=main_menu_kb())


# --- МЕНЮ ИНФОРМАЦИИ ---
@router.callback_query(F.data == "info_menu")
async def show_info_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message:
        await callback.message.edit_text(
            "ℹ️ <b>Полезная информация</b>\n\nВыбери нужный раздел ниже 👇",
            reply_markup=info_menu_kb()
        )
    await callback.answer()


@router.callback_query(F.data == "cancel_action")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    if callback.message:
        await callback.message.edit_text("🏠 <b>Главное меню</b>\n\nЧем еще могу помочь?", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_cb(callback: CallbackQuery):
    await callback.answer()


# --- ПОРТФОЛИО ---
@router.callback_query(F.data == "portfolio")
async def show_portfolio(callback: CallbackQuery):
    items = await get_portfolio()
    if not items:
        await callback.message.edit_text(
            "💼 <b>Мое портфолио</b>\n\nПока здесь пусто, но я уже работаю над новыми крутыми проектами!",
            reply_markup=back_to_info_kb() # Изменено на возврат в Информацию
        )
        return

    await callback.message.edit_text("💼 <b>Мои работы:</b>", reply_markup=back_to_info_kb()) # Изменено

    for item in items:
        text = f"<b>{item[1]}</b>\n\n{item[2]}"
        if item[4]:
            text += f"\n\n🔗 <a href='{item[4]}'>Ссылка на проект</a>"

        if item[3]:
            await callback.message.answer_photo(photo=item[3], caption=text)
        else:
            await callback.message.answer(text)

    await callback.answer()


# --- ИНФОРМАЦИЯ ---
@router.callback_query(F.data == "how_it_works")
async def how_it_works(callback: CallbackQuery):
    text = (
        "ℹ️ <b>Как проходит работа:</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "1️⃣ Вы оставляете заявку.\n"
        "2️⃣ Я согласовываю с вами точную цену.\n"
        "3️⃣ Вы вносите оплату.\n"
        "4️⃣ Я присылаю готовый результат прямо в этот чат.\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "🛡 <b>Гарантии:</b> Если что-то пойдет не так по моей вине — я верну деньги."
    )
    await callback.message.edit_text(text, reply_markup=back_to_info_kb()) # Изменено
    await callback.answer()


@router.callback_query(F.data == "payment_info")
async def payment_info(callback: CallbackQuery):
    text = (
        "💳 <b>Оплата и гарантии</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Доступные способы:\n"
        "├ 🇷🇺 Карта РФ / СБП\n"
        "├ 🟢 ЮMoney\n"
        "├ 🪙 Криптовалюта\n"
        "└ 🌍 Зарубежные сервисы\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "Вы можете оплатить 100% или внести предоплату 50%."
    )
    await callback.message.edit_text(text, reply_markup=back_to_info_kb()) # Изменено
    await callback.answer()


@router.callback_query(F.data == "price_list")
async def show_price(callback: CallbackQuery):
    text = (
        "💰 <b>Прайс-лист</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🟢 <b>Простые боты (от 500 ₽):</b>\n"
        "1. Анкетный бот — передает анкеты пользователей админу\n"
        "2. Бот счетчик — считает количество чего-либо\n"
        "3. Информационные рассыльщики — боты для отправки новостей\n"
        "4. Боты помощники — боты погоды, расписания, напоминалки\n\n"
        "🟡 <b>Средние боты (от 1500 ₽):</b>\n"
        "1. Боты с базой данных — сохранение профилей, истории заказов (SQLite/PostgreSQL)\n"
        "2. Боты для записи — салоны красоты, репетиторы (с выбором даты и времени)\n"
        "3. Боты с интеграцией API — отслеживание посылок, курсы валют, парсинг сайтов\n"
        "4. Квиз-боты — тесты с подсчетом баллов и выдачей результата\n"
        "5. Простые магазины — каталог товаров, корзина, оформление заявки\n\n"
        "🔴 <b>Сложные боты (от 6000 ₽):</b>\n"
        "1. Магазины с автовыдачей — моментальная выдача цифровых товаров/ключей\n"
        "2. Боты с админ-панелью — управление товарами, пользователями, рассылками прямо в боте\n"
        "3. Боты с ИИ — интеграция ChatGPT, генерация картинок, умные ассистенты\n"
        "4. Telegram Web Apps (Mini Apps) — полноценные магазины/игры внутри Telegram\n\n"
        "⚙️ <b>Дополнительные услуги:</b>\n"
        "• Подключение платежных систем: <b>+1000 ₽</b>\n"
        "• Настройка сервера и деплой (хостинг): <b>+500 ₽</b>\n"
        "• Разработка кастомного дизайна (кнопки, меню): <b>+700 ₽</b>\n"
        "• Доработка / починка чужого кода: <b>от 500 ₽/час</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "📍 <i>Точная стоимость зависит от задач. Оставьте заявку для расчета!</i>"
    )
    await callback.message.edit_text(text, reply_markup=back_to_info_kb()) # Изменено
    await callback.answer()


# --- СВЯЗЬ СО МНОЙ ---
@router.callback_query(F.data == "contact_me")
async def contact_me_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("✍️ <b>Напиши свое сообщение сюда:</b>", reply_markup=cancel_kb())
    await state.set_state(ContactState.waiting_for_message)
    await callback.answer()


@router.message(ContactState.waiting_for_message)
async def contact_me_send(message: Message, state: FSMContext, bot: Bot):
    if not message.text: return
    await state.clear()
    await message.answer("✅ Сообщение отправлено! Я скоро отвечу.", reply_markup=main_menu_kb())
    await bot.send_message(ADMIN_ID,
                           f"💬 <b>Сообщение от клиента:</b>\nОт: @{message.from_user.username or 'Скрыт'}\n\n{message.text}")