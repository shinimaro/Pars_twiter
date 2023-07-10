from aiogram.utils.keyboard import InlineKeyboardBuilder as BD
from aiogram.types import InlineKeyboardButton as IB
from wordbank.wordlist import WORDS_MAIN_MENU

main_menu = BD()
main_menu.row(
    IB(
        text=WORDS_MAIN_MENU['buttons_main_name']['button_tasks'],
        callback_data='tasks'))
main_menu.row(
    IB(
        text=WORDS_MAIN_MENU['buttons_main_name']['button_profile'],
        callback_data='profile'),
    IB(
        text=WORDS_MAIN_MENU['buttons_main_name']['button_help_center'],
        callback_data='help_center'),
    width=2)
main_menu.row(
    IB(
        text=WORDS_MAIN_MENU['buttons_main_name']['button_gaids'],
        callback_data='gaids')
    )


