from aiogram.utils.keyboard import InlineKeyboardBuilder as BD
from aiogram.types import InlineKeyboardButton as IB
from wordbank.wordlist import WORDS_PROFILE, BACK_LEXICON

profile_keyboard = BD()

profile_keyboard.row(
    IB(text=WORDS_PROFILE['buttons']['button_1'],
       callback_data='other'),
    IB(text=WORDS_PROFILE['buttons']['button_2'],
       callback_data='other'),
    IB(text=WORDS_PROFILE['buttons']['button_3'],
       callback_data='other'),
    IB(text=BACK_LEXICON,
       callback_data='back_to_main_menu'),

    width=2
)