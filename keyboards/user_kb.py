# Русский
import math

from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

VIDEOS_PER_PAGE = 10
russian_commands = [
    BotCommand(command="start", description="🔄 Перезапустить и поприветствовать бота"),
    BotCommand(command="channel", description="🔍 Найти канал на YouTube"),
    BotCommand(command="video", description="🎬 Найти видео на YouTube"),
    BotCommand(command="help", description="ℹ️ Узнать, что умеет бот"),
]

english_commands = [
    BotCommand(command="start", description="🔄 Restart the bot and get a welcome message"),
    BotCommand(command="channel", description="🔍 Search for a YouTube channel"),
    BotCommand(command="video", description="🎬 Search for YouTube videos"),
    BotCommand(command="help", description="ℹ️ What the bot can do and how to use it"),
]


# def quality_keyboard():
#     keyboard = InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text="144p", callback_data='quality_144p'),
#              InlineKeyboardButton(text="240p", callback_data='quality_240p'),
#              InlineKeyboardButton(text="360p", callback_data='quality_360p')],
#
#             [InlineKeyboardButton(text="480p", callback_data='quality_480p'),
#              InlineKeyboardButton(text="720p", callback_data='quality_720p'),
#              InlineKeyboardButton(text="1080p", callback_data='quality_1080p')],
#         ],
#     )
#     return keyboard


def select_video_keyboard(data, page):
    items = [item for item in data['items'] if item['id']['kind'] == 'youtube#video']
    items_per_page = 10
    start = page * items_per_page
    end = start + items_per_page
    page_items = items[start:end]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    for item in page_items:
        video_id = item['id']['videoId']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        button = InlineKeyboardButton(text=item['snippet']['title'], url=video_url)
        keyboard.inline_keyboard.append([button])  # добавляем кнопку в отдельный ряд

    nav_buttons = []

    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f'select_video_{page - 1}'))

    nav_buttons.append(InlineKeyboardButton(text=f"Страница {page+1} / { math.ceil(len(items) / 10)}", callback_data=f'stub'))

    if end < len(items):
        nav_buttons.append(InlineKeyboardButton(text="▶️ Вперёд", callback_data=f'select_video_{page + 1}'))

    if nav_buttons:
        keyboard.inline_keyboard.append(nav_buttons)

    return keyboard


final_text = """Вот что я нашёл по твоему запросу! 🎥

Если хочешь сделать новый поиск — просто нажми кнопку ниже.

🔄 /video — найти другое видео
🔍 /channel — найти канал"""
