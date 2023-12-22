from aiogram.exceptions import TelegramBadRequest
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import json
from aiogram.types import FSInputFile
import logging

logging.basicConfig(level=5, format="%(asctime)s %(levelname)s %(message)s",
                    encoding='utf-8')

TOKEN = '6463160714:AAGNRr6KGcbDGhNKdQhWa7fbfzcjFUGr_l0'
dp = Dispatcher()
bot = Bot(TOKEN)


def start_bot():
    logging.info('Бот запущен')


# Создание клавиатур
btn_back = types.InlineKeyboardButton(text='Назад', callback_data='back')
kb_back = InlineKeyboardBuilder()
kb_back.add(btn_back)
kb_back = kb_back.as_markup()

kb_start_menu = InlineKeyboardBuilder()
kb_start_menu.button(text='Запись на бесплатное пробное занятие', callback_data='1')
kb_start_menu.button(text='Расписание пробных занятий', callback_data='2')
kb_start_menu.button(text='Абонементы', callback_data='3')
kb_start_menu.button(text='Адрес', callback_data='4')
kb_start_menu.adjust(1, 1, 2, repeat=True)
kb_start_menu = kb_start_menu.as_markup()

kb_schedule = ReplyKeyboardBuilder()
kb_schedule.button(text='Понедельник 18:00-19:00')
kb_schedule.button(text='Вторник 19:30-20:30')
kb_schedule.button(text='Суббота с 15:00 до 16:00')
kb_schedule.adjust(1)
kb_schedule = kb_schedule.as_markup()
kb_schedule.resize_keyboard = True

kb_phone = ReplyKeyboardBuilder()
kb_phone.button(text='Воспользоваться номером аккаунта', request_contact=True)
kb_phone = kb_phone.as_markup()
kb_phone.resize_keyboard = True


# Машина состояний(нужно для записи на занятие)
class Form(StatesGroup):
    name = State()
    surname = State()
    telephone = State()
    record = State()


async def error_animation(message: types.Message):
    """
    Эта функция отправляет предупреждение и удаляет сообщение на которое ругается
    :param message:
    :return:
    """
    await message.answer_animation("CgACAgQAAxkBAAILzWV8feQ7TC8I_CWIjyXURuMPYXNkAAK6AgACqHRUU9340zLk5EeeMwQ",
                                   caption="Не балуйся!")
    await removal_past_message(message)
    await message.delete()


@dp.message(Command('admin'))
async def menu_sss(message: types.Message, state: FSMContext = None):
    """
    Эта функция отвечает на скрытую команду, выводит все записи из джисон файла
    :param message: 
    :return: 
    """""
    with open('data_test_bd.json', 'r', encoding='utf-8') as f:  # Открываем файл
        message_json = json.load(f)
        text_json = ''
        for i in message_json["customers"]:
            for j in i:
                text_json += j + ': ' + i[j] + '\n'
            text_json += '\n' + '\n'

        await message.answer(text=text_json)
    if state:
        await state.clear()


@dp.message(Command('start'))
async def start_menu(message: types.Message, state: FSMContext = None):
    """
    Эта функция отправляет сообщение с основным меню
    :param message: 
    :return: 
    """""
    logging.info(state)
    logging.info(f'Пользователь {message.from_user.username} запустил бота')
    await bot.send_message(chat_id=message.chat.id, text='Привет! Что тебе интересно?', reply_markup=kb_start_menu)
    await message.delete()
    if state:
        await state.clear()


@dp.callback_query(F.data == "1")
async def callback_register(callback: types.CallbackQuery, state: FSMContext):
    """
    Эта функция отвечает на кнопку 'Записаться на занятие'
    :param callback: 
    :param state: 
    :return: 
    """""
    await callback.message.answer('Напишите свое имя', inline_message_id=callback.message.text)
    await state.set_state(Form.name)
    await callback.message.delete()
    await callback.answer()


@dp.message(Form.name)
async def register_name(message: types.Message, state: FSMContext):
    """
    Эта функция записывает Имя
    :param message: 
    :param state: 
    :return: 
    """""
    try:
        if len(message.text) < 30:
            data = await state.update_data(name=message.text)
            await state.set_state(Form.surname)
            await message.answer(f'{data["name"]}, напишите фамилию')
            await removal_past_message(message)
            await message.delete()
        else:
            await error_animation(message)
            await message.answer('Слишком длинное имя, мы не выговариваем его, попробуйте еще раз')
    except (TelegramBadRequest, TypeError, ValueError) as e:
        await message.answer('Странное имя, попробуйте написать его текстом')
        await removal_past_message(message)
        await message.delete()
        logging.error(f"Неправильное заполнение Имени. ошибка {e}")


@dp.message(Form.surname)
async def register_surname(message: types.Message, state: FSMContext):
    """
    Эта функция записывает Фамилию
    :param message: 
    :param state: 
    :return: 
    """""
    try:
        if len(message.text) < 50:
            data = await state.update_data(surname=message.text)
            await state.set_state(Form.telephone)
            await message.answer('Укажите номер телефона без знаков', reply_markup=kb_phone)
            await removal_past_message(message)
            await message.delete()
        else:
            await error_animation(message)
            await message.answer('Слишком длинная фамилия, мы не запомним, попробуйте еще раз')
    except (TelegramBadRequest, TypeError) as e:
        await message.answer('Странная фамилия, попробуйте написать ее текстом')
        await removal_past_message(message)
        await message.delete()
        logging.error(f"Неправильное заполнение Фамилии. ошибка {e}")


@dp.message(Form.telephone)
async def register_telephone(message: types.Message, state: FSMContext):
    """
    Эта функция записывает Телефон
    :param message: 
    :param state: 
    :return: 
    """""
    try:
        if message.contact or (len(message.text) < 12 and int(message.text[0]) and int(message.text)):
            if not message.text:
                data = await state.update_data(telephone=message.contact.phone_number)
            else:
                data = await state.update_data(telephone=message.text)
            await state.set_state(Form.record)
            await message.answer(
                f'Отлично! Осталось совсем немного :) \n{data["name"]}, на какое занятие вас записать?',
                reply_markup=kb_schedule)
            await removal_past_message(message)
            await message.delete()
        else:
            await message.answer('Неправильный ввод номера телефона\nПопробуйте еще раз\nПример: 84564524587',
                                 reply_markup=kb_phone)
            await removal_past_message(message)
            await message.delete()
    except (TelegramBadRequest, TypeError, ValueError) as e:
        await removal_past_message(message)
        await message.delete()
        await message.answer('Неправильный ввод номера телефона\nПопробуйте еще раз\nПример: 84564524587',
                             reply_markup=kb_phone)
        await removal_past_message(message)
        logging.error(f"Неправильное заполнение Номера телефона. ошибка {e}")


@dp.message(Form.record)
async def register_finish(message: types.Message, state: FSMContext):
    """
    Эта функция высылает подробную информацию о записи, закрепляет сообщение
    :param message: 
    :param state: 
    :return: 
    """""
    try:
        kb_schedule_list = ['Понедельник 18:00-19:00', 'Вторник 19:30-20:30', 'Суббота с 15:00 до 16:00']
        if message.text in kb_schedule_list:
            data = await state.update_data(record=message.text)
            # Отправка сообщений пользователю о записи на занятие
            with open("reminder.txt", "rb") as f:  # открываем документ
                contents = f.read().decode("UTF-8")  # считываем все строки
                await message.answer_animation(
                    caption=contents,
                    animation="CgACAgQAAxkBAAII0GV8MhQFUNxAP2xAhXtFUlXhT1AbAAIGAwACHsEEU_iYmkD4qpCBMwQ",
                    reply_markup=types.ReplyKeyboardRemove())  # отправляем текст файла в сообщении
            text = data["name"] + ', вы записаны на занятие: \n' + data["record"] + '\nваш телефон для связи:\n' + data[
                "telephone"] + '\nДо скорой встречи!'
            await message.answer(text=text)
            await bot.pin_chat_message(chat_id=message.chat.id, message_id=message.message_id + 2)
            # Запись на занятие в джисон файл
            with open('data_test_bd.json', encoding='utf-8') as f:  # Открываем файл
                dd = json.load(f)
            with open("data_test_bd.json", "w", encoding='utf-8') as write_file:
                dd["customers"].append(data)
                json.dump(dd, write_file, ensure_ascii=False, indent=4)
            # удаление двух предыдущих сообщений
            await removal_past_message(message)
            await message.delete()
            await state.clear()
        else:
            await message.answer('Такого занятия не существует, выбирите вариант из предложенных',
                                 reply_markup=kb_schedule)
            await removal_past_message(message)
            await message.delete()
    except (TelegramBadRequest, ValueError):
        logging.error("С сообщениями о записи что-то пошло не так")
        await message.answer('Такого занятия не существует, выбирите вариант из предложенных', reply_markup=kb_schedule)
        await removal_past_message(message)
        await message.delete()


@dp.callback_query(F.data == "2")
async def callback_schedule(callback: types.CallbackQuery, state: FSMContext = None):
    """
    Эта функция перехватывает кнопку 'Расписание'
    :param callback:
    :return:
    """
    await callback.message.answer_photo(FSInputFile('p1.jpg'),
                                        caption='Расписание пробных занятий \nПонедельник 18:00-19:00\nВторник 19:30-20:30\nСуббота с 15:00 до 16:00',
                                        reply_markup=kb_back)
    await callback.message.delete()
    if state:
        await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "3")
async def callback_tickets(callback: types.CallbackQuery, state: FSMContext = None):
    """
    Эта функция перехватывает кнопку 'Абонементы', отправляет сообщение с информацией об Абонементах
    :param callback:
    :return:
    """
    await callback.message.answer_photo(FSInputFile('p2.jpg'),
                                        caption='Абонементы:\n8 занятий: 1 000\n12 занятий: 2 000\nбезлимит: 3 000',
                                        reply_markup=kb_back)
    await callback.message.delete()
    if state:
        await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "4")
async def callback_address(callback: types.CallbackQuery, state: FSMContext = None):
    """
    Эта функция отвечает на кнопку "Адрес", отправляет сообщение с Адресом
    :param callback:
    :return:
    """
    logging.info(f'{callback.from_user.username} смотрит адрес')
    await callback.message.answer('Адрес: \n ул. Советская 18, вход со стороны торца')  # сюда бы карту
    await callback.message.answer_location(55.03024562947552, 82.91680691108277, reply_markup=kb_back)
    await callback.message.delete()
    if state:
        await state.clear()
    await callback.answer()


@dp.callback_query(F.data == "back")
async def callback_back(callback: types.CallbackQuery, state: FSMContext = None):
    """
    Эта функция возвращает на главное меню
    :param callback:
    :return:
    """
    await removal_past_message(callback.message)
    await start_menu(callback.message)
    if state:
        await state.clear()
    await callback.answer()


async def removal_past_message(message: types.Message):
    """
    Эта функция удаляет предыдущее сообщение
    :param message:
    :return:
    """
    try:
        await message.chat.delete_message(message.message_id - 1)
    except TelegramBadRequest as e:
        logging.error('Сообщения не существует')


@dp.message()
async def error_error(message: types.Message):
    """
    Эта функция отправляет предупреждение на любые нестандартные действия и удаляет сообщение, на которое ругается
    :param message:
    :return:
    """
    logging.info(f"{message.from_user}")
    if message.from_user.username != 'system_project_bot':
        await message.answer(text='Вы пишите странные вещи, бот не понимает, чего вам надо')
        await removal_past_message(message)
        await message.delete()


if __name__ == '__main__':
    try:
        asyncio.run(dp.start_polling(bot, on_startup=start_bot()))
    except KeyboardInterrupt:
        logging.error("Работа завершена ошибка")
