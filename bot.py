import os
import sqlite3
import random
import re
import logging
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler,
)
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения из .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Путь к базе данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "glossary.db")


# Функция для инициализации базы данных
def init_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS glossary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            russian_term TEXT NOT NULL,
            chinese_term TEXT NOT NULL,
            pinyin TEXT,
            description TEXT,
            example TEXT,
            category TEXT
        );
        """)
        conn.commit()
        logger.info("База данных инициализирована.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка базы данных при инициализации: {e}")
    finally:
        conn.close()


# Заполнение базы данных терминами
def populate_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Список терминов для добавления
        terms = [
            # Углеродное регулирование
            (
                'декарбонизация',
                '脱碳',
                'tuō tàn',
                'Процесс сокращения выбросов диоксида углерода в атмосферу.',
                'Декарбонизация промышленности является ключевым шагом в борьбе с изменением климата.',
                'Углеродное регулирование'
            ),
            (
                'низкоуглеродное развитие',
                '低碳发展',
                'dī tàn fā zhǎn',
                'Модель экономического развития с низкими выбросами диоксида углерода.',
                'Низкоуглеродное развитие способствует устойчивому будущему.',
                'Углеродное регулирование'
            ),
            (
                'квоты на выбросы парниковых газов',
                '温室气体排放配额',
                'wēn shì qì tǐ páifàng pèi\'é',
                'Лимиты на выбросы парниковых газов для предприятий.',
                'Введение квот на выбросы парниковых газов стимулирует компании к снижению эмиссий.',
                'Углеродное регулирование'
            ),
            (
                'углеродные единицы',
                '碳单位',
                'tàn dānwèi',
                'Единицы, измеряющие количество выброшенного диоксида углерода.',
                'Компании покупают углеродные единицы для компенсации своих выбросов.',
                'Углеродное регулирование'
            ),
            (
                'таксономия',
                '分类法',
                'fēnlèi fǎ',
                'Система классификации, используемая для организации и оценки устойчивых инвестиций.',
                'Таксономия помогает инвесторам идентифицировать экологически устойчивые проекты.',
                'Углеродное регулирование'
            ),
            (
                'зеленые облигации',
                '绿色债券',
                'lǜsè zhàiquàn',
                'Финансовые инструменты для финансирования экологически устойчивых проектов.',
                'Компания выпустила зеленые облигации для финансирования газовых электростанций.',
                'Углеродное регулирование'
            ),
            # Энергетический переход
            (
                'природный газ',
                '天然气',
                'tiānrán qì',
                'Горючее ископаемое, используемое для производства энергии.',
                'Природный газ является самым экологически чистым ископаемым топливом.',
                'Энергетический переход'
            ),
            (
                'углеродный след',
                '碳足迹',
                'tàn zújì',
                'Общее количество выбросов углерода, связанных с деятельностью человека.',
                'Сокращение углеродного следа помогает уменьшить негативное воздействие на климат.',
                'Энергетический переход'
            ),
            (
                'энергетическая рентабельность',
                '能源效率',
                'néngyuán xiàolǜ',
                'Мера эффективности использования энергии.',
                'Повышение энергетической рентабельности снижает затраты на производство.',
                'Энергетический переход'
            ),
            (
                'улавливание и утилизация (диоксида) углерода',
                '碳捕集与利用',
                'tàn bǔjí yǔ lìyòng',
                'Технологии по захвату и использованию углекислого газа из промышленных процессов.',
                'Улавливание и утилизация углерода помогают снизить выбросы в атмосферу.',
                'Энергетический переход'
            ),
            # Вторичные и альтернативные источники энергии
            (
                'водородная энергетика',
                '氢能',
                'qīng néng',
                'Использование водорода как источника энергии.',
                'Водородная энергетика перспективна для создания чистых транспортных средств.',
                'Вторичные источники энергии'
            ),
            (
                'утилизация тепла',
                '热能利用',
                'rè néng lìyòng',
                'Использование отходящего тепла для полезных целей.',
                'Утилизация тепла повышает общую энергетическую эффективность предприятия.',
                'Вторичные источники энергии'
            ),
        ]

        # Вставка данных в таблицу
        cursor.executemany("""
        INSERT INTO glossary (
            russian_term,
            chinese_term,
            pinyin,
            description,
            example,
            category
        ) VALUES (?, ?, ?, ?, ?, ?)
        """, terms)

        conn.commit()
        logger.info("База данных успешно заполнена терминами.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при заполнении базы данных: {e}")
    finally:
        conn.close()


# Функция для поиска термина
def search_term(term: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Определение языка ввода
        if re.search(r'^[а-яА-ЯёЁ\s\-]+$', term):
            # Русский
            cursor.execute("SELECT * FROM glossary WHERE russian_term LIKE ?", (f"%{term}%",))
            logger.info(f"Поиск по русскому термину: {term}")
        elif re.search(r'[\u4e00-\u9fff]', term):
            # Китайский
            cursor.execute("SELECT * FROM glossary WHERE chinese_term LIKE ?", (f"%{term}%",))
            logger.info(f"Поиск по китайскому термину: {term}")
        else:
            # Неопределённый язык, ищем в обоих
            cursor.execute("""
            SELECT * FROM glossary 
            WHERE russian_term LIKE ? OR chinese_term LIKE ?
            """, (f"%{term}%", f"%{term}%",))
            logger.info(f"Поиск по обоим терминам: {term}")

        results = cursor.fetchall()
        logger.info(f"Найдено результатов: {len(results)}")
        return results
    except sqlite3.Error as e:
        logger.error(f"Ошибка при поиске термина '{term}': {e}")
        return []
    finally:
        conn.close()


# Функция для получения случайного термина
def get_random_term():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM glossary ORDER BY RANDOM() LIMIT 1;")
        result = cursor.fetchone()
        if result:
            logger.info(f"Случайный термин: {result}")
        else:
            logger.info("Глоссарий пуст при попытке получить случайный термин.")
        return result
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении случайного термина: {e}")
        return None
    finally:
        conn.close()


# Функция для получения всех категорий
def get_categories():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT category FROM glossary;")
        categories = [row[0] for row in cursor.fetchall()]
        logger.info(f"Категории: {categories}")
        return categories
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении категорий: {e}")
        return []
    finally:
        conn.close()


# Функция для получения терминов по категории
def get_terms_by_category(category: str):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM glossary WHERE category = ?", (category,))
        results = cursor.fetchall()
        logger.info(f"Найдено терминов в категории '{category}': {len(results)}")
        return results
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении терминов по категории '{category}': {e}")
        return []
    finally:
        conn.close()


# Функция для создания сообщения с термином
def format_term(term_data):
    if not term_data:
        return "Термин не найден."

    try:
        _, russian, chinese, pinyin, description, example, category = term_data
        message = (
            f"**Русский:** {russian}\n"
            f"**Китайский:** {chinese} ({pinyin})\n"
            f"**Описание:** {description}\n"
            f"**Пример:** {example}\n"
            f"**Категория:** {category}\n"
        )
        return message
    except Exception as e:
        logger.error(f"Ошибка при форматировании термина: {e}")
        return "Ошибка при форматировании термина."


# Команды бота

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "Привет! Я глоссарий по низкоуглеродной энергетике.\n\n"
        "Вот список команд, которые я поддерживаю:\n"
        "/search [термин] - Поиск термина на русском или китайском языке.\n"
        "/random - Показать случайный термин.\n"
        "/category - Выбрать категорию терминов.\n"
        "/quiz - Пройти викторину по терминам.\n"
        "/help - Получить справку по боту."
    )
    await update.message.reply_text(message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Пожалуйста, укажите термин для поиска. Пример: /search природный газ")
        return

    term = ' '.join(context.args)
    results = search_term(term)

    if results:
        messages = [format_term(result) for result in results]
        for msg in messages:
            await update.message.reply_text(msg, parse_mode='Markdown')
    else:
        await update.message.reply_text("Термин не найден в базе данных.")


async def random_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    term = get_random_term()
    if term:
        message = format_term(term)
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Глоссарий пуст.")


async def category_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = get_categories()
    if not categories:
        await update.message.reply_text("Категории не найдены.")
        return

    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    category = query.data
    terms = get_terms_by_category(category)
    if terms:
        for term in terms:
            msg = format_term(term)
            await query.message.reply_text(msg, parse_mode='Markdown')
    else:
        await query.message.reply_text("Термины в этой категории не найдены.")


# Функции для викторины

# Храним состояние пользователей для викторины
user_quiz_state = {}


async def quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_quiz_state and user_quiz_state[user_id]['active']:
        await update.message.reply_text("Викторина уже активна. Ответьте на текущий вопрос.")
        return

    term = get_random_term()
    if not term:
        await update.message.reply_text("Глоссарий пуст.")
        return

    question = f"Как переводится термин '{term[2]}' на русский язык?"
    user_quiz_state[user_id] = {
        'active': True,
        'answer': term[1],  # russian_term
        'term_id': term[0]
    }

    await update.message.reply_text(question)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id in user_quiz_state and user_quiz_state[user_id]['active']:
        correct_answer = user_quiz_state[user_id]['answer']
        if text.lower().strip() == correct_answer.lower().strip():
            await update.message.reply_text("Правильно! 🎉")
        else:
            await update.message.reply_text(f"Неправильно. Правильный ответ: {correct_answer}")

        user_quiz_state[user_id]['active'] = False
    else:
        # Можно добавить другие обработки сообщений, если необходимо
        pass


# Основная функция
def main():
    # Инициализация базы данных
    init_db()

    # Проверка, заполнена ли база данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM glossary;")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        logger.info("База данных пуста. Заполнение базы данных.")
        populate_db()
    else:
        logger.info(f"База данных уже содержит {count} записей.")

    # Создание приложения
    application = ApplicationBuilder().token(TOKEN).build()

    # Добавление обработчиков команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("search", search))
    application.add_handler(CommandHandler("random", random_term))
    application.add_handler(CommandHandler("category", category_command))
    application.add_handler(CallbackQueryHandler(category_callback))
    application.add_handler(CommandHandler("quiz", quiz_command))

    # Обработчик текстовых сообщений для викторины
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запуск бота
    logger.info("Бот запущен.")
    application.run_polling()


if __name__ == '__main__':
    main()
