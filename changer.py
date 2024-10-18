import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InputFile
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.types.message import ContentType
import os

API_TOKEN = 'bot tokenini kirit'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

class FileStates(StatesGroup):
    waiting_for_file = State()
    waiting_for_new_name = State()
    waiting_for_thumbnail = State()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer("Salom! Menga 4GB gacha fayl yuboring.")
    await FileStates.waiting_for_file.set()

@dp.message_handler(content_types=[ContentType.DOCUMENT], state=FileStates.waiting_for_file)
async def handle_file(message: types.Message, state: FSMContext):
    if message.document.file_size > 4 * 1024 * 1024 * 1024:
        await message.reply("Fayl hajmi 4GB dan katta, boshqa fayl yuboring.")
    else:
        file_id = message.document.file_id
        file_info = await bot.get_file(file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        original_file_name = message.document.file_name

        local_file_path = f"temp/{original_file_name}"
        with open(local_file_path, 'wb') as new_file:
            new_file.write(downloaded_file.read())

        await state.update_data(file_path=local_file_path)
        await message.answer("Fayl muvaffaqiyatli qabul qilindi! Endi yangi nom kiriting.")
        await FileStates.waiting_for_new_name.set()

@dp.message_handler(state=FileStates.waiting_for_new_name)
async def rename_file(message: types.Message, state: FSMContext):
    new_file_name = message.text
    data = await state.get_data()
    original_file_path = data['file_path']
    new_file_path = os.path.join("temp", new_file_name)

    os.rename(original_file_path, new_file_path)
    await state.update_data(new_file_path=new_file_path)

    await message.answer("Fayl nomi muvaffaqiyatli o'zgartirildi! Endi fayl uchun .jpg formatdagi thumbnail yuboring.")
    await FileStates.waiting_for_thumbnail.set()

@dp.message_handler(content_types=[ContentType.PHOTO], state=FileStates.waiting_for_thumbnail)
async def handle_thumbnail(message: types.Message, state: FSMContext):
    data = await state.get_data()
    new_file_path = data['new_file_path']

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_photo = await bot.download_file(file_info.file_path)
    thumbnail_path = f"temp/{os.path.basename(new_file_path)}_thumb.jpg"

    with open(thumbnail_path, 'wb') as thumb_file:
        thumb_file.write(downloaded_photo.read())

    await bot.send_document(message.chat.id, InputFile(new_file_path, filename=os.path.basename(new_file_path)), thumb=InputFile(thumbnail_path))

    os.remove(new_file_path)
    os.remove(thumbnail_path)

    await message.answer("Fayl nomi va thumbnail muvaffaqiyatli o'zgartirildi!")
    await state.finish()

if __name__ == '__main__':
    if not os.path.exists('temp'):
        os.makedirs('temp')
    
    executor.start_polling(dp, skip_updates=True)
