import asyncio
import aiogram
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
from aiogram.types import BufferedInputFile, CallbackQuery

import lerya

Api_tg_Token = '6692691429:AAFagkU_TTogj1KKLR1g7f2sf0dR30PC0Hc'
logging.basicConfig(level=logging.INFO)
bot = aiogram.Bot(token=Api_tg_Token)
dp = aiogram.Dispatcher()


async def availability(chatid, availab):
    image = BufferedInputFile(availab, filename=f"image.png")
    await bot.send_photo(chat_id=chatid, photo=image, caption=
    'Проверка наличия товара в магазинах:\nЕсли вам нужен другой товар, просто напишите его название или артикул')


@dp.message(Command("start"))
async def send_welcome(message: aiogram.types.Message):
    first_name = message.chat.first_name
    await message.answer(f"*Здравствуйте {first_name}*\nЯ бот для подразделения Леруа Мерлен в Новосибирске\nЗдесь"
                         " вы можете посмотреть наличие товара в магазине\nДля этого просто отправьте мне ваш запрос: "
                         "это может быть полное, частичное название товара, или же его артикул",
                         parse_mode=ParseMode.MARKDOWN_V2)


@dp.message(aiogram.F.text)
async def extract_data(message: aiogram.types.Message):
    await message.answer('Подождите несколько секунд')
    try:
        for vendor_code, card_image in lerya.main(message.text):
            if vendor_code == 'no':
                await availability(message.chat.id, card_image)
            else:
                photo = BufferedInputFile(card_image, filename=f"{vendor_code}.png")
                builder = InlineKeyboardBuilder()
                builder.add(InlineKeyboardButton(
                    text=f"{vendor_code}",
                    callback_data=f"{vendor_code}")
                )
                await message.answer_photo(photo, reply_markup=builder.as_markup())
    except TypeError:
        await message.answer('По вашему запросу не нашлось совпадений, попробуйте другой запрос')


@dp.callback_query()
async def handle_callback_query(callback: CallbackQuery):
    vendor_code = callback.data
    i, result = next(lerya.main(vendor_code))
    await availability(callback.from_user.id, result)
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
