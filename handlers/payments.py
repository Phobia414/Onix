"""
Оплата через Telegram Stars (XTR).
Самый простой способ: не требует внешних API и ключей.
Комиссия Telegram ~30%, но зато работает во всех странах.

Курс: 1 звезда ≈ 1.3 рубля (при покупке). Для точности настройте K_STARS.
"""

import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from database import get_order, update_order_status
from config import ADMIN_ID

router = Router()

# Курс: сколько рублей за 1 звезду (для пересчета)
# 1 звезда при покупке ~1.3 рубля. Для вывода курс другой.
# Настройте под себя, либо используйте ЮKassa для точных сумм.
RUB_PER_STAR = 1.3


@router.callback_query(F.data.startswith("pay_stars_100_"))
async def pay_stars_100(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split("_")[3])
    order = await get_order(order_id)
    if not order or order[6] <= 0:
        await callback.answer("Цена еще не установлена", show_alert=True)
        return

    price_rub = order[6]
    stars = max(1, int(price_rub / RUB_PER_STAR))  # минимум 1 звезда

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Заявка №{order_id} — 100%",
        description=f"Полная оплата заявки №{order_id} ({price_rub} ₽)",
        payload=f"order_{order_id}_100",
        provider_token="",  # Для Stars пустой
        currency="XTR",     # Telegram Stars
        prices=[LabeledPrice(label=f"Заявка №{order_id}", amount=stars)],
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_stars_50_"))
async def pay_stars_50(callback: CallbackQuery, bot: Bot):
    order_id = int(callback.data.split("_")[3])
    order = await get_order(order_id)
    if not order or order[6] <= 0:
        await callback.answer("Цена еще не установлена", show_alert=True)
        return

    price_rub = order[6] // 2
    stars = max(1, int(price_rub / RUB_PER_STAR))

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=f"Заявка №{order_id} — 50%",
        description=f"Предоплата 50% заявки №{order_id} ({price_rub} ₽)",
        payload=f"order_{order_id}_50",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"Заявка №{order_id} (50%)", amount=stars)],
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Обязательно подтверждаем — иначе Telegram не даст оплатить
    await pre_checkout_query.answer(ok=True)


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot):
    payload = message.successful_payment.invoice_payload
    # payload = "order_{id}_100" или "order_{id}_50"
    try:
        parts = payload.split("_")
        order_id = int(parts[1])
        payment_type = parts[2]
    except (IndexError, ValueError):
        logging.error(f"Некорректный payload: {payload}")
        return

    await update_order_status(order_id, "in_work")
    order = await get_order(order_id)

    if payment_type == "100":
        await message.answer("✅ <b>Оплата 100% прошла!</b>\nЯ взял заявку в работу.")
        await bot.send_message(
            ADMIN_ID,
            f"💰 Клиент полностью оплатил заявку №{order_id} ({order[6]} ₽) через Telegram Stars!"
        )
    else:
        await message.answer("✅ <b>Предоплата 50% получена!</b>\nЯ взял заявку в работу.")
        await bot.send_message(
            ADMIN_ID,
            f"💰 Клиент внес 50% по заявке №{order_id} ({int(order[6] / 2)} ₽) через Telegram Stars!"
        )