import os
import httpx

from aiogram.filters import Command, CommandStart
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery
from aiogram.types import Message
from dotenv import load_dotenv

from keyboards.user_kb import (russian_commands,
                               english_commands,
                               final_text,
                               select_video_keyboard)

user = Router()

load_dotenv()
API_KEY = os.getenv('YouTubeToken')
SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search'

last_update = 0


class SearchStates(StatesGroup):
    channel_title = State()
    video_title = State()
    maxResults = State()
    link = State()
    results = State()


@user.message(CommandStart())
async def start_handler(message: Message):
    bot = message.bot
    await bot.set_my_commands(commands=russian_commands, language_code="ru")
    await bot.set_my_commands(commands=english_commands, language_code="en")
    await message.answer(
        "Привет! 👋 Я — бот-помощник, который поможет тебе найти видео и каналы на YouTube. 🎥\n"
        "Просто введи команду /video, чтобы искать видео, \n"
        "или /channel — чтобы найти канал.\n"
        "Если нужна помощь — пиши /help 😊"
    )


@user.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("""🤖 This bot can download videos from YouTube for you.

How to use:
  1. Open the YouTube.
  2. Choose video that you liked.
  3. Click to the «Copy» button.
  4. Send the link to the bot and get your file!""")


@user.message(Command("video"))
async def video_search(message: Message, state: FSMContext):
    await message.answer("Напиши, что хочешь найти на YouTube:")
    await state.set_state(SearchStates.video_title)


@user.message(SearchStates.video_title)
async def maxResultsVideo(message: Message, state: FSMContext):
    video_title = message.text
    if video_title.startswith('/'):
        return
    await state.update_data(video_title=video_title)
    await message.answer("Сколько видео вывести? Введи число от 1 до 50:")
    await state.set_state(SearchStates.maxResults)


@user.message(Command("channel"))
async def channel_search(message: Message, state: FSMContext):
    await message.answer("Напиши, какой канал хочешь найти на YouTube:")
    await state.set_state(SearchStates.channel_title)


@user.message(SearchStates.maxResults)
async def search_videos(message: Message, state: FSMContext):
    maxResults = message.text
    page = 0

    try:
        maxResults = int(maxResults)
    except ValueError:
        await message.answer("Пожалуйста, введи число (например, 5).")
        return

    if not (1 <= maxResults <= 50):
        await message.answer("Число должно быть от 1 до 50.")
        return

    data = await state.get_data()
    video_title = data.get("video_title")

    params = {
        'part': 'snippet',
        'q': video_title,
        'type': 'video',
        'maxResults': maxResults,
        'key': API_KEY
    }

    response = httpx.get(SEARCH_URL, params=params)
    data = response.json()
    items = len(data['items'])
    await state.update_data(results=data)  # сохранить результаты в FSM

    if items:
        if maxResults > 5:
            await message.answer(f"Выбери видео: (всего найдено {items})",
                                 reply_markup=select_video_keyboard(data, page))
        else:
            for item in data['items']:
                video_id = item['id']['videoId']
                channel_id = item['snippet']['channelId']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                channel_url = f"https://www.youtube.com/channel/{channel_id}"
                await message.answer(f"🎬 Ссылка на видео: {video_url}\n"
                                     f"🔗 Ссылка на канал: {channel_url}")

        await message.answer(final_text)
    else:
        await message.answer(
            "🔍 We couldn’t find any videos matching your search. Please try again with different keywords.")


@user.callback_query(F.data.startswith('select_video_'))
async def video_page_handler(callback: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    data = state_data.get("results")
    if not data:
        await callback.answer("Нет данных для отображения", show_alert=True)
        return

    page_str = callback.data.split('_')[-1]
    try:
        page = int(page_str)
    except ValueError:
        await callback.answer("Неверная страница", show_alert=True)
        return

    keyboard = select_video_keyboard(data, page)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer()


@user.callback_query(F.data.startswith('stub'))
async def stub_handler(callback: CallbackQuery):
    await callback.message.answer("")


@user.message(SearchStates.channel_title)
async def search_channel(message: Message, state: FSMContext):
    channel_title = message.text.strip()
    if not channel_title:
        await message.answer("Пожалуйста, введи название канала для поиска.")
        return

    # Сохраняем в состояние
    await state.update_data(channel_title=channel_title)
    data = await state.get_data()
    chanel_title = data.get("channel_title")

    params = {
        'part': 'snippet',
        'q': chanel_title,
        'type': 'channel',
        'maxResults': 1,
        'key': API_KEY
    }

    response = httpx.get(SEARCH_URL, params=params)
    data = response.json()

    for item in data['items']:
        channel_id = item['id']['channelId']
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        await message.answer(f"🔗 Ссылка на канал: {channel_url}")

    await message.answer(final_text)
    await state.clear()

# @user.message(Command("download"))
# async def download_handler(message: Message, state: FSMContext):
#     await message.answer("Скинь ссылку, какое видео хочешь скачать с YouTube:")
#     await state.set_state(SearchStates.link)


# @user.message(SearchStates.link)
# async def choose_quality(message: Message, state: FSMContext):
#     video_id = message.text.strip().split('/')[-1].split('?')[0]
#     await state.update_data(link=video_id)
#
#     thumbnail = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
#     thumbnail_message = await message.answer_photo(
#         thumbnail,
#         caption="Выбери качество видео:",
#         reply_markup=quality_keyboard()
#     )
#     await state.update_data(thumbnail_msg_id=thumbnail_message.message_id)


# @user.callback_query(F.data.startswith("quality_"))
# async def download_and_send_video(callback: CallbackQuery, state: FSMContext):
#     quality = callback.data.split('_')[-1]
#
#     data = await state.get_data()
#     video_id = data.get("link")
#     thumbnail_msg_id = data.get("thumbnail_msg_id")
#     url = f'https://www.youtube.com/watch?v={video_id}'
#
#     if not video_id:
#         await callback.message.answer("Не удалось получить ссылку на видео. Попробуй снова.")
#         return
#
#     # Получаем форматы
#     formats = await get_video_formats(url)
#
#     # Ищем itag для нужного качества
#     selected_itag = None
#     for f in formats:
#         # Проверяем, что есть ключ 'height' и он совпадает с выбранным качеством
#         if f.get('format_note') == quality:
#             # Можно добавить фильтр по ext='mp4' или прогрессивности, если нужно
#             selected_itag = f.get('format_id')
#             break
#
#     if not selected_itag:
#         await callback.message.answer(f"Видео с разрешением {quality}p не найдено.")
#         return
#
#     # Остальной код — подготовка прогресса и скачивание
#     bot = callback.bot
#     if thumbnail_msg_id:
#         try:
#             await callback.bot.edit_message_caption(
#                 chat_id=callback.message.chat.id,
#                 message_id=thumbnail_msg_id,
#                 caption=""
#             )
#         except Exception:
#             try:
#                 await callback.bot.delete_message(
#                     chat_id=callback.message.chat.id,
#                     message_id=thumbnail_msg_id
#                 )
#             except Exception:
#                 pass
#
#     progress_message = await callback.message.answer("Видео загружается... ⏳")
#
#     loop = asyncio.get_running_loop()
#
#     def make_progress_hook(progress_message, bot, loop):
#         last_update_ref = {'time': 0}
#
#         def progress_hook(status):
#             if status['status'] == 'downloading':
#                 now = time.time()
#                 if now - last_update_ref['time'] < 1:
#                     return
#                 last_update_ref['time'] = int(now)
#
#                 downloaded = status.get('downloaded_bytes', 0)
#                 total = status.get('total_bytes') or status.get('total_bytes_estimate') or 1
#                 percent = downloaded / total * 100
#
#                 coro = progress_message.edit_text(
#                     f"Скачивание: {percent:.1f}% ({downloaded // (1024 * 1024)}MB / {total // (1024 * 1024)}MB)")
#                 asyncio.run_coroutine_threadsafe(bot(coro), loop)
#
#         return progress_hook
#
#     ydl_opts = {
#         'format': f"{selected_itag}",
#         'outtmpl': 'downloads/%(title)s.%(ext)s',
#         'quiet': True,
#         'progress_hooks': [make_progress_hook(progress_message, bot, loop)]
#     }
#
#     os.makedirs('downloads', exist_ok=True)
#
#     try:
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=True)
#             filename = ydl.prepare_filename(info)
#     except DownloadError:
#         await callback.message.answer("Ошибка: неправильная ссылка или видео недоступно.")
#         return
#     except ExtractorError:
#         await callback.message.answer("Ошибка: не удалось обработать видео.")
#         return
#     except Exception as e:
#         await callback.message.answer(f"Произошла ошибка: {e}")
#         return
#     finally:
#         await progress_message.edit_text("Что-то пошло не так...")
#
#     max_size = 1900 * 1024 * 1024  # 1.9 ГБ
#
#     file_size = os.path.getsize(filename)
#
#     if file_size > max_size:
#         await progress_message.delete()
#         await callback.message.answer("Файл слишком большой для отправки (больше 1.9 ГБ).")
#         os.remove(filename)
#         await state.clear()
#         return
#
#     await callback.message.answer_video(
#         video=r"C:\Users\rubly\IT\PycharmProjects\Aiogram\YouTube_API\downloads\Dark Hardwave ⧸ Trap Wave ⧸ Phonk Mix 'DRØWN Vol.5'.mp4",
#         caption=f'🎞 @{callback.message.from_user.username} {quality}')
#     await progress_message.delete()
#     await callback.bot.delete_message(
#         chat_id=callback.message.chat.id,
#         message_id=thumbnail_msg_id
#     )
#     os.remove(filename)
#     await state.clear()
#
#
# # async def get_video_formats(url):
#     def run():
#         ydl_opts = {'quiet': True}
#         with yt_dlp.YoutubeDL(ydl_opts) as ydl:
#             info = ydl.extract_info(url, download=False)
#             return info['formats']
#
#     formats = await asyncio.to_thread(run)
#     return formats
