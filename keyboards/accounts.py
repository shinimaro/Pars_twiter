from math import ceil

from aiogram.utils.keyboard import InlineKeyboardBuilder as BD
from aiogram.types import InlineKeyboardButton as IB
from asyncpg import ConnectionDoesNotExistError

from databases.database import Database
from wordbank.wordlist import BACK_LEXICON, FORWARD_LEXICON, BACK_MENU_LEXICON, WORDS_PERFORMANCE_TASK


async def accounts_kb(tg_id, page: int = 1):

    if page == 0:
        return False

    db = Database()
    await db.connect()
    quantity = await db.quantity_accounts(tg_id)
    set_accounts = await db.set_accounts(tg_id)
    await db.disconnect()
    accounts = BD()

    if quantity == 0:
        accounts.row(
            IB(text=BACK_LEXICON, callback_data='back_to_tasks'))
        return accounts.as_markup()


    q = quantity // 8
    if q == 0:
        e = quantity % (1 * 8)
    else:
        e = quantity % (q*8)
    if e != 0 and page > q+1:
        return False
    elif e == 0 and page > q:
        return False


    if quantity > 8:
        pagus = page * 8

        accs_list = []
        for acc in set_accounts:
            accs_list.append(acc['acc_name'])
            if len(accs_list) == pagus:
                break

        if len(accs_list) % 8 == 0:
            accs_list = accs_list[pagus-8:pagus+1]
        else:
            a = len(accs_list) % 8
            accs_list = accs_list[-a:]

        for acc in range(len(accs_list)):
            accounts.row(
                IB(text=accs_list[acc], callback_data=accs_list[acc]),
                width=1
            )


        pagination = quantity
        if pagination <= 8:
            pagination = 1
        else:
            pagination /= 8

        accounts.row(
            IB(text=BACK_LEXICON, callback_data=f'back_{page-1}'),
            IB(text=f'{page}/{ceil(pagination)}', callback_data='other'),
            IB(text=FORWARD_LEXICON, callback_data=f'forward_{page+1}'), width=3)

        accounts.row(
            IB(text=BACK_MENU_LEXICON, callback_data='back_to_tasks')
        )

    else:
        for acc in set_accounts:
            accounts.row(
                IB(text=acc['acc_name'], callback_data=acc['acc_name']),
            width=1)

        accounts.row(
            IB(text=BACK_LEXICON, callback_data='back_to_tasks')
        )
    return accounts.as_markup()


# Доп клавиатура для сохранения аккаунта
async def save_kb(task_id=None):
    save_keyboard = BD()

    save_keyboard.row(
        IB(text=WORDS_PERFORMANCE_TASK['button_yes_save_account'],
           callback_data='save_account'),
        IB(text=WORDS_PERFORMANCE_TASK['button_no_save_account'],
           callback_data='no_save_account'),
        IB(text=WORDS_PERFORMANCE_TASK['button_cansel'],
           callback_data=f'task_{task_id}'),
        width=2)
    return save_keyboard.as_markup()


# Доп клавиатура, которая прерывает проверку и возвращает пользователя обратно в таски

stop_keyboard = BD()

stop_keyboard.row(
    IB(text=WORDS_PERFORMANCE_TASK['button_cansel'],
       callback_data='stop_check')
)

# Доп клавиатура, сообщающая о том, что аккаунт прошёл проверку
# В check - кидаем результат проверки
async def fynally_keyboard(task_id, check):
    if check:
        success_keyboard = BD()
        success_keyboard.row(
            IB(text=WORDS_PERFORMANCE_TASK['button_continue'],
               callback_data=f'task_{task_id}'), width=1)
        return success_keyboard.as_markup()
    else:
        failded_keyboard = BD()
        failded_keyboard.row(
            IB(text=BACK_LEXICON,
               callback_data=f'task_{task_id}'), width=1)
        return failded_keyboard.as_markup()





