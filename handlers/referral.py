from aiogram import Router, F, Bot
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import Message, CallbackQuery
from database import apply_referral
from config import CHANNEL_ID
from keyboards.client_kb import main_menu_kb

router = Router()


@router.message(CommandStart(deep_link=True))
async def handle_referral(message: Message, command: CommandObject, bot: Bot):
    args = command.args
    if args and args.startswith("ref_"):
        order_id = int(args.split("_")[1])
        try:
            member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=message.from_user.id)
            if member.status in ["member", "administrator", "creator"]:
                new_price = await apply_referral(order_id, message.from_user.id)
                if new_price:
                    await message.answer(
                        f"✅ Вы подписались на канал! Вашему другу одобрена скидка 10% на заказ №{order_id}. Теперь он заплатит {new_price} ₽.")
                else:
                    await message.answer("⚠️ Скидка уже была применена к этому заказу или цена еще не выставлена.")
            else:
                await message.answer("⚠️ Для активации скидки вам нужно подписаться на наш канал!")
        except Exception:
            await message.answer("⚠️ Ошибка проверки подписки. Убедитесь, что бот добавлен в админы канала.")

        await message.answer("Добро пожаловать в бота!", reply_markup=main_menu_kb())