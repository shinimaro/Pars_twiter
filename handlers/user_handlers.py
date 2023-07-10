from aiogram import Router, Bot
from aiogram.filters import CommandStart, Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import Message, CallbackQuery

from FSM.FSM_states import FSMInputAccount
from config import Config, load_config
from databases.database import Database
from funcks_handlers.correct_account_name import correct_account
from funcks_handlers.handler_parsing import parser
from funcks_handlers.task_text import task_text
from keyboards.accounts import accounts_kb, stop_keyboard, fynally_keyboard, save_kb
from keyboards.main_menu import main_menu
from keyboards.profile import profile_keyboard
from keyboards.tasks import tasks_list
from wordbank import wordlist
from wordbank.wordlist import WORDS_PROFILE, WORDS_PERFORMANCE_TASK

config: Config = load_config()
router: Router = Router()
state: State = State()
db = Database()
bot = Bot(token=config.tg_bot.token, parse_mode="HTML")


# Запуск бота
@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(wordlist.WORDS_MAIN_MENU['welcome_text'], reply_markup=main_menu.as_markup())
    # Занесение пользователя в базу данных
    await db.connect()
    await db.user_in_database(message.from_user.id, '@' + message.from_user.username)
    await db.disconnect()


# Возвращение в главное меню
@router.callback_query(Text(text=['back_to_main_menu']))
async def process_open_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(wordlist.WORDS_MAIN_MENU['welcome_text'], reply_markup=main_menu.as_markup())


# Пользователь отрыл меню с тасками
@router.callback_query(Text(text=['tasks', 'back_to_tasks']))
async def process_open_tasks(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(wordlist.WORDS_TASKS['main_text'].format(), reply_markup=await tasks_list())
    await state.clear()


# Пользователь открыл один из тасков
@router.callback_query(lambda x: x.data.startswith('task_'))
async def process_open_task(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    await callback.message.edit_text(await task_text(tg_id, int(callback.data[5:])), disable_web_page_preview=True,
                                     reply_markup=await accounts_kb(tg_id))
    await state.set_state(FSMInputAccount.account_name)
    await state.update_data(message_id=callback.message.message_id)
    await state.update_data(task_id=int(callback.data[5:]))


# Пользователь перебирает свои аккаунты
@router.callback_query(lambda x: x.data.startswith('forward_') or x.data.startswith('back_'))
async def process_open_accounts(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.from_user.id
    await db.disconnect()
    if callback.data.startswith('back_'):
        string = callback.data[5:]
    else:
        string = callback.data[8:]
    keyboard = await accounts_kb(tg_id, int(string))
    if not keyboard:
        await callback.answer()
    else:
        text = await task_text(tg_id)
        await callback.message.edit_text(text=text, disable_web_page_preview=True,
                                         reply_markup=keyboard)
    await state.update_data(message_id=callback.message.message_id)


# Пользователь указал аккаунт
@router.message(StateFilter(FSMInputAccount.account_name))
async def process_input_account(message: Message, state: FSMContext):
    await state.update_data(account=message.text)
    data = await state.get_data()
    await message.delete()
    await bot.edit_message_text(text=WORDS_PERFORMANCE_TASK['new_account'].format(message.text.strip().lower()), message_id=data.get('message_id'), chat_id=message.chat.id, reply_markup=await save_kb(data.get('task_id')))


# Пользователь указал новый аккаунт для проверки
@router.callback_query(StateFilter(FSMInputAccount.account_name), Text(text=['save_account', 'no_save_account']))
async def process_save_account(callback: CallbackQuery, state: FSMContext):
    # Определяем переменные
    data = await state.get_data()
    account = data.get('account')
    task_id = data.get('task_id')
    result = await correct_account(account)
    tg_id = callback.from_user.id
    # Проверяем аккаунт
    if result is None:
        await callback.answer(WORDS_PERFORMANCE_TASK['incorrect_account'], show_alert=True)
    elif not result:
        await callback.answer(WORDS_PERFORMANCE_TASK['another_user_account'], show_alert=True)
    elif result:
        # Добавляем аккаунт, если он прошёл проверку
        await db.connect()
        if callback.data == 'save_account':
            await db.insert_account(tg_id, account)
        completed_task = await db.check_account(account, task_id)
        await db.disconnect()
        # Проверяем, не выполнял ли он таск ранее
        if not completed_task:
            await callback.message.edit_text(WORDS_PERFORMANCE_TASK['account_completed_task'],
                                             reply_markup=await fynally_keyboard(task_id, False))
        else:
            # Проверяем статус выполнения задания
            await state.set_state(FSMInputAccount.execution_check)
            if callback.data == 'save_account':
                await callback.answer(WORDS_PERFORMANCE_TASK['save_account_user'])
            await callback.message.edit_text(WORDS_PERFORMANCE_TASK['bot_check_task'], reply_markup=stop_keyboard.as_markup())
            check = await parser(task_id, account)
            # Если задание выполнено, насыпаем монет пользователю и указываем, что аккаунт сделал этот таск
            if check:
                await db.connect()
                price = await db.give_price(task_id)
                await db.completed_task(tg_id, account, task_id, price)
                await db.disconnect()
                await callback.message.edit_text(WORDS_PERFORMANCE_TASK['user_finally_task'].format(price),
                                              reply_markup=await fynally_keyboard(task_id, check))
            else:
                await callback.message.edit_text(WORDS_PERFORMANCE_TASK['user_not-finally_task'],
                                              reply_markup=await fynally_keyboard(task_id, check))


# Пользователь выбрал для проверки один из своих аккаунтов
@router.callback_query(StateFilter(FSMInputAccount.account_name), lambda x: x.data.startswith('@'))
async def process_check_task(callback: CallbackQuery, state: FSMContext):
    await state.set_state(FSMInputAccount.execution_check)
    data = await state.get_data()
    account = callback.data
    task_id = data.get('task_id')

    # Проверяем, не выполнял ли он таск ранее
    await db.connect()
    completed_task = await db.check_account(account, task_id)
    await db.disconnect()
    if not completed_task:
        await callback.message.edit_text(WORDS_PERFORMANCE_TASK['account_completed_task'],
                                         reply_markup=await fynally_keyboard(task_id, False))
    else:
        await callback.message.edit_text(WORDS_PERFORMANCE_TASK['bot_check_task'], reply_markup=stop_keyboard.as_markup())
        check = await parser(task_id, account)
        if check:
            await db.connect()
            price = await db.give_price(task_id)
            await db.completed_task(callback.from_user.id, account, task_id, price)
            await db.disconnect()
            await callback.message.edit_text(WORDS_PERFORMANCE_TASK['user_finally_task'].format(price),
                                             reply_markup=await fynally_keyboard(task_id, check))
        else:
            await callback.message.edit_text(WORDS_PERFORMANCE_TASK['user_not-finally_task'],
                                             reply_markup=await fynally_keyboard(task_id, check))


# Пользователь открыл профиль
@router.callback_query(Text(text=['profile']))
async def process_open_profile(callback: CallbackQuery):
    await db.connect()
    result = await db.check_user(callback.from_user.id)
    await db.disconnect()
    await callback.message.edit_text(WORDS_PROFILE['main_text'].format('@' + callback.from_user.username, result[0], result[1], result[2]),
                                     reply_markup=profile_keyboard.as_markup())


# Ответ на прочие кнопки, чтобы они не светились
@router.callback_query(Text(text=['other']))
async def other(callback: CallbackQuery):
    await callback.answer()






















