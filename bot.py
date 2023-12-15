import json
import os
from telebot.apihelper import send_photo
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
import random

# Пути к JSON-файлам
users_file_path = 'users.json'
photos_file_path = 'photos.json'
likes_file_path = 'likes.json'


# Функция для сохранения данных в JSON-файл
def save_to_json(data, file_path):
    with open(file_path, 'w') as json_file:
        json.dump(data, json_file)


# Функция для загрузки данных из JSON-файла
def load_from_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            data = json.load(json_file)
        return data
    return {}


users = load_from_json(users_file_path)
photos = load_from_json(photos_file_path)
likes = load_from_json(likes_file_path)


def start(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in users:
        users[user_id] = {'photo': None, 'seen': []}
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Регистрация", callback_data='register')]
    ])
    update.message.reply_text("Привет! 😄 Давай начнем знакомство? Сначала загрузи свою фотографию!", reply_markup=reply_markup)


def register(update: Update, context):
    user_id = update.callback_query.from_user.id
    update.callback_query.message.reply_text("Отправь мне свою фотографию!")


def photo_received(update: Update, context):
    user_id = update.message.from_user.id
    photo_id = update.message.photo[-1].file_id
    users[user_id]['photo'] = photo_id
    photos[user_id] = photo_id
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Знакомиться", callback_data='browse')],
        [InlineKeyboardButton("Хватит", callback_data='stop')]
    ])
    update.message.reply_text("Отлично! Теперь выбери действие:", reply_markup=reply_markup)


def browse_photos(update: Update, context):
    user_id = update.callback_query.from_user.id
    unseen_users = [u for u in photos if u != user_id and u not in users[user_id]['seen']]
    if unseen_users:
        random_user = random.choice(unseen_users)
        users[user_id]['seen'].append(random_user)
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Лайк ❤️", callback_data=f'like_{random_user}')],
            [InlineKeyboardButton("Дизлайк 🚫", callback_data=f'dislike_{random_user}')],
        ])
        context.bot.send_photo(chat_id=user_id, photo=photos[random_user], reply_markup=reply_markup)
    else:
        update.callback_query.message.reply_text("Вы просмотрели все фотографии 😅. Ждите новых участников!")


def like(update: Update, context):
    user_id = update.callback_query.from_user.id
    liked_user = int(update.callback_query.data.split('_')[1])
    if liked_user not in likes:
        likes[liked_user] = []
    likes[liked_user].append(user_id)
    if user_id in likes and liked_user in likes[user_id]:
        context.bot.send_message(chat_id=user_id, text=f"Ура! 🎉 Взаимный лайк с {liked_user}. Начните общение!")
        context.bot.send_message(chat_id=liked_user, text=f"Ура! 🎉 Взаимный лайк с {user_id}. Начните общение!")
    else:
        update.callback_query.answer("Лайк учтен! Давайте продолжим.")


def dislike(update: Update, context):
    user_id = update.callback_query.from_user.id
    disliked_user = int(update.callback_query.data.split('_')[1])
    users[user_id]['seen'].append(disliked_user)  # добавляем пользователя в список просмотренных

    # Сохранение данных после обновления
    save_to_json(users, users_file_path)

    browse_photos(update, context)


def main():
    updater = Updater(token="6476555391:AAEDgmGX0vRdl1gMEj8Vm3biyLMDiBrv1XY", use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(register, pattern='^register$'))
    dp.add_handler(MessageHandler(Filters.photo, photo_received))
    dp.add_handler(CallbackQueryHandler(browse_photos, pattern='^browse$'))
    dp.add_handler(CallbackQueryHandler(like, pattern='^like_\d+$'))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

