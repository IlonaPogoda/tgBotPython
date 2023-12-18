import json
import os
import tempfile
import cv2
import numpy as np
from PIL import Image
from telegram import Bot, Update, InlineKeyboardButton, InlineKeyboardMarkup, bot
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import random
from deepface import DeepFace


# Пути к JSON-файлам
users_file_path = 'C:\\Users\\ilona\\PycharmProjects\\tgBotPython\\users.json'
photos_file_path = 'C:\\Users\\ilona\\PycharmProjects\\tgBotPython\\photos.json'
likes_file_path = 'C:\\Users\\ilona\\PycharmProjects\\tgBotPython\\likes.json'


# Функция для сохранения данных в JSON-файл
def save_to_json(data, file_path):
    print("fdfd")
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

    show_reg_message(update)


def show_reg_message(update: Update):

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Регистрация", callback_data='register')]
    ])
    a = "Привет! 😄 Давай начнем знакомство? Сначала загрузи свою фотографию!"
    if update.message is not None:
        update.message.reply_text(a, reply_markup=reply_markup)
    elif update.callback_query is not None:
        update.callback_query.message.reply_text(a, reply_markup=reply_markup)


def show_start_message(update: Update):
    a = "Привет, вы еще не зарегестрированы, введите /start"
    if update.message is not None:
        update.message.reply_text(a)
    elif update.callback_query is not None:
        update.callback_query.message.reply_text(a)


def register(update: Update, context):
    user_name = update.callback_query.from_user.username
    user_id = update.callback_query.from_user.id
    if user_id not in users:
        users[user_id] = {'photo': None, 'seen': [], 'username': user_name}
        update.callback_query.message.reply_text("Отправь мне свою фотографию!")
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("Знакомиться", callback_data='browse')],
            [InlineKeyboardButton("Хватит", callback_data='stop')]
        ])
        update.callback_query.message.reply_text("Вы уже зарегистрированы", reply_markup=reply_markup)
    save_to_json(users, users_file_path)


def photo_received(update: Update, context):
    user_id = update.message.from_user.id
    if not validate_user(update, user_id):
        return
    photo_id = update.message.photo[-1].file_id
    users[user_id]['photo'] = photo_id
    photos[user_id] = photo_id
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("Знакомиться", callback_data='browse')],
        [InlineKeyboardButton("Хватит", callback_data='stop')]
    ])
    update.message.reply_text("Отлично! Теперь выбери действие:", reply_markup=reply_markup)
    save_to_json(users, users_file_path)
    save_to_json(photos, photos_file_path)


def save_temp_file(photo_file):
    temp_dir = tempfile.gettempdir()
    temp_file_path = os.path.join(temp_dir, 'temp_photo.jpg')
    photo_file.save(temp_file_path)
    return temp_file_path


def get_gender(photo_file):
    temp_file_path = save_temp_file(photo_file)
    result = DeepFace.analyze(temp_file_path, actions=['gender'])
    os.remove(temp_file_path)
    gender = result[0]['dominant_gender']
    return gender


def has_face(photo_file):
    print("Я тут")
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Конвертируем BytesIO в массив numpy
    image = Image.open(photo_file)
    image_np = np.array(image)
    gray = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    print(len(faces))
    return len(faces) > 0


def browse_photos(update: Update, context):
    user_id = update.callback_query.from_user.id
    if not validate_user(update, user_id):
        return
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
    if not validate_user(update, user_id):
        return
    print("bsgdh")
    user_name = update.callback_query.from_user.username
    liked_user = int(update.callback_query.data.split('_')[1])
    if liked_user not in likes:
        likes[liked_user] = []
    likes[liked_user].append(user_id)
    if user_id in likes and liked_user in likes[user_id]:
        context.bot.send_message(chat_id=user_id, text=f"Ура! 🎉 Взаимный лайк с {'@' + users[liked_user]['username']}. Начните общение!")
        context.bot.send_message(chat_id=liked_user, text=f"Ура! 🎉 Взаимный лайк с {'@' + user_name}. Начните общение!")
    else:
        update.callback_query.answer("Лайк учтен! Давайте продолжим.")
    save_to_json(likes, likes_file_path)


def dislike(update: Update, context):
    user_id = update.callback_query.from_user.id
    if not validate_user(update, user_id):
        return
    print("fdjbvv")
    disliked_user = int(update.callback_query.data.split('_')[1])
    users[user_id]['seen'].append(disliked_user)  # добавляем пользователя в список просмотренных
    # Сохранение данных после обновления
    save_to_json(users, users_file_path)

    browse_photos(update, context)


def validate_user(update: Update, user_id):
    print(users)
    if user_id not in users:
        show_start_message(update)
        return False
    return True


def main():
    updater = Updater(token="6476555391:AAEDgmGX0vRdl1gMEj8Vm3biyLMDiBrv1XY", use_context=True)

    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(register, pattern='^register$'))
    dp.add_handler(MessageHandler(Filters.photo, photo_received))
    dp.add_handler(CallbackQueryHandler(browse_photos, pattern='^browse$'))
    dp.add_handler(CallbackQueryHandler(like, pattern='^like_\d+$'))
    dp.add_handler(CallbackQueryHandler(dislike, pattern='^dislike_\d+$'))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()

