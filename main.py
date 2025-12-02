from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import PicklePersistence, ApplicationBuilder, CommandHandler, MessageHandler,ConversationHandler, ContextTypes, filters
from telegram.error import Forbidden
from dotenv import load_dotenv
from bd import *
import os


load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

persistence = PicklePersistence(filepath="bot_data.pkl")

app = ApplicationBuilder().token(TOKEN).persistence(persistence).build()
        

ASK_FACULTY, ASK_COURSE, ASK_GENDER, ASK_SEARCH_GENDER, ASK_NAME, ASK_BIO, ASK_PHOTO, MENU, SHOW_OTHER_PROFILE, SYMPATHY, TURN_OFF_PROFILE = range(11)

# ----------------------------------------------------------------------

def faculty_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["ФРКТ", "ФБМФ", "ФАКТ"],
            ["ЛФИ", "ФПМИ", "ФЭФМ"],
            ["ФАЛТ", "ВШПИ", "КНТ"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def course_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["1", "2", "3"],
            ["4", "5", "6"]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def gender_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Парень", "Девушка"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def search_gender_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["Парни", "Девушки", "Все равно"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ----------------------------------------------------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["user_id"] = update.effective_user.id
    context.user_data["username"] = update.effective_user.username

    if get_name_by_id(update.effective_user.id) != None:
        await show_my_profile(update, context)
        return await menu(update, context)

    await update.message.reply_text("Привет! Давай создадим твою анкету.\n\nТы откуда?", reply_markup=faculty_keyboard())
    return ASK_FACULTY

async def update_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ты откуда?", reply_markup=faculty_keyboard())
    return ASK_FACULTY

async def ask_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.text not in ["ФРКТ", "ЛФИ", "ФАКТ", "ФПМИ", "ФБМФ", "ФЭФМ", "ВШПИ", "ФАЛТ", "КНТ"]):
        await update.message.reply_text("Нет такого варианта ответа", reply_markup=faculty_keyboard())
        return ASK_FACULTY

    context.user_data["faculty"] = update.message.text
    await update.message.reply_text("Какой курс?", reply_markup=course_keyboard())
    return ASK_COURSE

async def ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.text not in ["1", "2", "3", "4", "5", "6"]):
        await update.message.reply_text("Нет такого варианта ответа", reply_markup=course_keyboard())
        return ASK_COURSE

    context.user_data["course"] = update.message.text
    await update.message.reply_text("Ты парень или девушка?", reply_markup=gender_keyboard())
    return ASK_GENDER

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.text not in ["Парень", "Девушка"]):
        await update.message.reply_text("Нет такого варианта ответа", reply_markup=gender_keyboard())
        return ASK_GENDER

    context.user_data["gender"] = update.message.text
    await update.message.reply_text("Кто тебе интересен?", reply_markup=search_gender_keyboard())
    return ASK_SEARCH_GENDER

async def ask_search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.text not in ["Парни", "Девушки", "Все равно"]):
        await update.message.reply_text("Нет такого варианта ответа", reply_markup=search_gender_keyboard())
        return ASK_SEARCH_GENDER

    context.user_data["search_gender"] = update.message.text
    await update.message.reply_text("Как тебя зовут?", reply_markup=ReplyKeyboardRemove())
    return ASK_NAME

async def ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) > 100:
        await update.message.reply_text("Слишком длинное имя, максимум 100 символов")
        return ASK_NAME
    
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Расскажи о себе, кого хочешь найти и чем предлагаешь заняться:")
    return ASK_BIO

async def ask_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(update.message.text) > 800:
        await update.message.reply_text("Слишком длинное описание, максимум 800 символов")
        return ASK_BIO

    context.user_data["bio"] = update.message.text
    await update.message.reply_text("Отправь своё фото:")
    return ASK_PHOTO

async def ask_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    context.user_data["photo_id"] = photo.file_id

    add_user(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username,
        faculty=context.user_data["faculty"],
        course=context.user_data["course"],
        gender=context.user_data["gender"],
        search_gender=context.user_data["search_gender"],
        name=context.user_data["name"],
        bio=context.user_data["bio"],
        photo_id=context.user_data["photo_id"]
    )

    await update.message.reply_text("✅ Анкета сохранена!")

    await show_my_profile(update, context)

    return await menu(update, context)

# ----------------------------------------------------------------------

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = ReplyKeyboardMarkup(
        [
            ["1🔥", "2", "3", "4"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if check_status(update.effective_user.id) == 'active':
        text4 = '4. Отключить анкету'
    else:
        text4 = '4. Активировать анкету'

    await update.message.reply_text(
        f"1. Смотреть анкеты🔥\n2. Моя анкета\n3. Заполнить анкету заново\n{text4}",
        reply_markup=keyboard
    )
    return MENU


async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == "1🔥" or choice == "1":
        turn_on_profile_bd(update.effective_user.id) # включаем анкету

        return await show_other_profile(update, context, get_random_user(update.effective_user.id))
    elif choice == "2":
        await show_my_profile(update, context)
        return await menu(update, context)
    elif choice == "3":
        return await update_profile(update, context)
    elif choice == "4":
        if check_status(update.effective_user.id) == 'active':
            return await turn_off_profile(update, context)
        else:
            return await turn_on_profile(update, context)
        
    else:
        await update.message.reply_text("Нет такого варианта ответа")
        return MENU

# ----------------------------------------------------------------------

async def sympathy(update: Update, context: ContextTypes.DEFAULT_TYPE, target_id: int):
    user_name = context.user_data["name"]
    user_username = context.user_data["username"]
    target_name = get_name_by_id(target_id)
    target_username = get_username_by_id(target_id)


    if target_username != None:
        target_link = f"https://t.me/{target_username}?text=Привет, я с Физтех.Знакомства"
    else:
        target_link = f"tg://user?id={target_id}"
    text_for_user = f"Взаимная симпатия с <a href='{target_link}'>{target_name}</a> ❤️\n\nНапиши скорее)"


    if user_username != None:
        user_link = f"https://t.me/{user_username}?text=Привет, я с Физтех.Знакомства"
    else:
        user_link = f"tg://user?id={update.effective_user.id}"
    text_for_target = f"Взаимная симпатия с <a href='{user_link}'>{user_name}</a> ❤️\n\nНапиши скорее)"

    keyboard = ReplyKeyboardMarkup(
        [
            ["Меню", "Дальше"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    await update.message.reply_text(text_for_user, parse_mode="HTML", reply_markup=keyboard)

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=text_for_target,
            parse_mode="HTML"
        )   
    except Forbidden:
        block(target_id) # target_id заблокировал бота   

    return SYMPATHY

async def handle_sympathy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    choice = update.message.text

    if choice == "Меню":
        return await menu(update, context)
    elif choice == "Дальше":
        return await show_other_profile(update, context, get_random_user(update.effective_user.id))
    else:
        await update.message.reply_text("Нет такого варианта ответа")
        return SYMPATHY

# ----------------------------------------------------------------------

async def handle_other_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    target_id = context.user_data.get("target_id")

    if update.message.text == "👎":
        save_action(user_id, target_id, "dislike")
        return await show_other_profile(update, context, get_random_user(user_id))
    elif update.message.text == "❤️":
        save_action(user_id, target_id, "like")

        if check_like(target_id, user_id):
            return await sympathy(update, context, target_id)
        else:
            try:
                await context.bot.send_message(
                    chat_id=target_id,
                    text="Кто-то хочет с тобой познакомиться✨\n\n Посмотри анкеты!",
                )    
            except Forbidden:
                block(target_id) # target_id заблокировал бота                

            return await show_other_profile(update, context, get_random_user(user_id))
    elif update.message.text == "Меню":
        return await menu(update, context)
    else:
        await update.message.reply_text("Нет такого варианта ответа")
        return SHOW_OTHER_PROFILE

async def show_other_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, id: int | None):
    if (id == None):
        await update.message.reply_text("Анкеты закончились 😢")
        return await menu(update, context)
    
    context.user_data["target_id"] = id  

    faculty, course, gender, search_gender, name, bio, photo_id = get_user(id)

    keyboard = ReplyKeyboardMarkup(
        [
            ["👎", "Меню", "❤️"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

    if check_like(id, update.effective_user.id):
        text = f"Кому-то понравилась твоя анкета:\n\n{name}, {faculty}, {course} курс - {bio}"
    else:
        text = f"{name}, {faculty}, {course} курс - {bio}"

    await update.message.reply_photo(
        photo=photo_id,
        caption=(
            text
        ),
        reply_markup=keyboard
    )

    return SHOW_OTHER_PROFILE


async def show_my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faculty, course, gender, search_gender, name, bio, photo_id = get_user(update.effective_user.id)

    await update.message.reply_text("Так выглядит твоя анкета:")

    await update.message.reply_photo(
        photo=photo_id,
        caption=(
            f"{name}, {faculty}, {course} курс - {bio}"
        ),
    )

# ----------------------------------------------------------------------

async def turn_off_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    turn_off_profile_keyboard = ReplyKeyboardMarkup(
        [
            ["Оставить как есть", "Отключить"],
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
        
    await update.message.reply_text("Вы уверены? В таком случае ваша анкета больше не будет показываться другим пользователям", reply_markup=turn_off_profile_keyboard)
    return TURN_OFF_PROFILE

async def handler_turn_off_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (update.message.text not in ["Оставить как есть", "Отключить"]):
        await update.message.reply_text("Нет такого варианта ответа")
        return TURN_OFF_PROFILE

    if update.message.text == "Отключить":
        await update.message.reply_text("💤 Анкета отключена!")
        turn_off_profile_bd(update.effective_user.id)

    return await menu(update, context)


async def turn_on_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Анкета активирована!")
    turn_on_profile_bd(update.effective_user.id)
        
    return await menu(update, context)

# ----------------------------------------------------------------------

async def incorrect_input_ask_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод", reply_markup=faculty_keyboard())
    return ASK_FACULTY

async def incorrect_input_ask_course(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод", reply_markup=course_keyboard())
    return ASK_COURSE

async def incorrect_input_ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод", reply_markup=gender_keyboard())
    return ASK_GENDER

async def incorrect_input_ask_search_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод", reply_markup=search_gender_keyboard())
    return ASK_SEARCH_GENDER

async def incorrect_input_ask_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return ASK_NAME

async def incorrect_input_ask_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return ASK_BIO

async def incorrect_input_ask_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return ASK_PHOTO

async def incorrect_input_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return MENU

async def incorrect_input_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return SHOW_OTHER_PROFILE

async def incorrect_input_SYMPATHY(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Некорректный ввод")
    return SYMPATHY

async def handle_other_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не знаю такой команды")

async def incorrect_input_turn_off_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Не знаю такой команды")

# ----------------------------------------------------------------------

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        ASK_FACULTY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_faculty),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_ask_faculty)
        ],
        ASK_COURSE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_course),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_ask_course)
        ],
        ASK_GENDER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_gender),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_ask_gender)
        ],
        ASK_SEARCH_GENDER: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_search_gender),
            MessageHandler(~(filters.TEXT & ~filters.COMMAND), incorrect_input_ask_search_gender)
        ],
        ASK_NAME: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_name),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_ask_name)
        ],
        ASK_BIO: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bio),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_ask_bio)
        ],
        ASK_PHOTO: [
            MessageHandler(filters.PHOTO, ask_photo),
            MessageHandler(filters.ALL & ~filters.PHOTO & ~filters.COMMAND, incorrect_input_ask_photo)
        ],
        MENU: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_menu)
        ],
        SHOW_OTHER_PROFILE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_other_profile),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_profile),
        ],
        SYMPATHY: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sympathy),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_SYMPATHY),
        ],
        TURN_OFF_PROFILE: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, handler_turn_off_profile),
            MessageHandler(filters.ALL & ~filters.COMMAND, incorrect_input_turn_off_profile),
        ]
    },
    fallbacks = [
        CommandHandler("start", start),
        MessageHandler(filters.COMMAND, handle_other_command),
    ],

    name="conversation",
    persistent=True
)

# ----------------------------------------------------------------------

app.add_handler(conv_handler)

try:
    app.run_polling()
except KeyboardInterrupt:
    print("Бот остановлен вручную.")
