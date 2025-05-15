import logging
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, ContextTypes
from database import Database
from material import Material

# Загрузка переменных из .env
load_dotenv()

# Получение токенов из переменных окружения
TOKEN = os.getenv('TOKEN')
PAYMENT_PROVIDER_TOKEN = os.getenv('PAYMENT_PROVIDER_TOKEN')

# Проверка токена
if not PAYMENT_PROVIDER_TOKEN:
    raise ValueError("PAYMENT_PROVIDER_TOKEN не указан в .env")

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка материалов из JSON
db = Database()

async def send_start_msg(telegramObject, reply_markup):
    await telegramObject.message.reply_text('Привет! Выбери материал:', reply_markup=reply_markup)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start - показывает список материалов"""
    keyboard = [[InlineKeyboardButton(material.title, callback_data=str(material.id))] 
        for material in db.get_all_materials()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if update.message:
        # Обрабатываем команду /start
        await send_start_msg(update, reply_markup)
    elif update.callback_query:
        # Обрабатываем нажатие кнопки
        query = update.callback_query
        await query.answer()
        await send_start_msg(query, reply_markup)

async def handle_start_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await start(update, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка нажатия на кнопку материала"""
    logger.info("Функция обработки кнопки")
    query = update.callback_query
    id = int(query.data)
    material = db.get_material_by_id(id)
    
    # Создаём кнопки
    keyboard = [
        [InlineKeyboardButton("Скачать демо", callback_data=f'demo_{id}')],
        [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{id}')],
        [InlineKeyboardButton("Вернуться к началу", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.answer()
    try:
        await query.edit_message_media(
            media=InputMediaPhoto(
                media=material.img_link,
                caption=f"{material.title}"
            ),
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Ошибка при редактировании сообщения с изображением: {e}")
        await query.edit_message_text(
            text=f"{material.title}",
            reply_markup=reply_markup
        )


async def handle_demo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправка демо-файла"""
    query = update.callback_query
    id = int(query.data.split('_')[1])
    material = db.get_material_by_id(id)
    
    await query.answer()
    # Отправляем демо-файл по URL
    try:
        await query.message.reply_text(
            text=f"Вот ссылка на демо-версию материала:\n{material['demo_file_link']}"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке ссылки на демо-файл: {e}, ссылка: {material['demo_file_link']}")
        await query.message.reply_text("Ошибка при отправке ссылки на демо-файл.")
        return
    
    # Обновляем сообщение с кнопками
    keyboard = [
        [InlineKeyboardButton("Скачать демо", callback_data=f'demo_{id}')],
        [InlineKeyboardButton("Купить полный материал", callback_data=f'buy_{id}')],
        [InlineKeyboardButton("Вернуться к началу", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if material.get('img_link'):
        try:
            await query.edit_message_media(
                media=InputMediaPhoto(
                    media=material['img_link'],
                    caption=f"{material['title']}"
                ),
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения с изображением: {e}, ссылка: {material['img_link']}")
            await query.edit_message_text(
                text=f"{material['title']}",
                reply_markup=reply_markup
            )
    else:
        await query.edit_message_text(
            text=f"{material['title']}",
            reply_markup=reply_markup
        )

async def handle_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Запрос оплаты"""
    query = update.callback_query
    id = int(query.data.split('_')[1])
    material = db.get_material_by_id(id)
    
    await query.answer()
    try:
        # Отправляем инвойс
        await context.bot.send_invoice(
            chat_id=query.message.chat_id,
            title=material['title'],
            description=material['title'],
            payload=id,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency='RUB',
            prices=[{'label': 'Цена', 'amount': material['price']}],
            # Для продакшена ЮKassa требует provider_data для чека, пример:
            # provider_data={
            #     "receipt": {
            #         "items": [
            #             {
            #                 "description": material['title'],
            #                 "quantity": "1.00",
            #                 "amount": {
            #                     "value": str(material['price'] / 100.0),
            #                     "currency": "RUB"
            #                 },
            #                 "vat_code": 1  # Без НДС для цифровых товаров
            #             }
            #         ]
            #     }
            # }
        )
        logger.info(f"Инвойс отправлен для {material['title']} (ID: {id}, сумма: {material['price']/100} RUB)")
    except Exception as e:
        logger.error(f"Ошибка при отправке инвойса: {e}")
        await query.message.reply_text(f"Произошла ошибка при создании счёта: {str(e)}. Попробуйте позже.")

async def precheckout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Проверка перед оплатой"""
    query = update.pre_checkout_query
    await query.answer(ok=True)
    logger.info(f"Pre-checkout успешен для payload: {query.invoice_payload}")

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка успешной оплаты"""
    if update.message.successful_payment:
        payment = update.message.successful_payment
        id = int(payment.invoice_payload)
        material = db.get_material_by_id(id)
        
        try:
            keyboard = [[InlineKeyboardButton("Вернуться к началу", callback_data='start')]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                text=f"Спасибо за покупку! Вот полный материал {material['title']}:\n{material['full_file_link']}",
                reply_markup=reply_markup
            )

            logger.info(f"Успешная оплата для {material['title']} (ключ: {id})")
        except Exception as e:
            logger.error(f"Ошибка при отправке файла: {e}")
            await update.message.reply_text("Ошибка при отправке файла. Свяжитесь с поддержкой.")


def main() -> None:
    """Запуск бота"""
    if not TOKEN:
        raise ValueError("TOKEN не указан в .env")
    
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и событий
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button, pattern=r'^(?!start$|demo_|buy_)[\w]+$'))
    application.add_handler(CallbackQueryHandler(handle_demo, pattern=r'^demo_'))
    application.add_handler(CallbackQueryHandler(handle_buy, pattern=r'^buy_'))
    application.add_handler(CallbackQueryHandler(handle_start_button, pattern=r'^start$'))
    application.add_handler(PreCheckoutQueryHandler(precheckout_handler))
    application.add_handler(MessageHandler(None, successful_payment_handler))

    # Запуск polling
    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == '__main__':
    main()