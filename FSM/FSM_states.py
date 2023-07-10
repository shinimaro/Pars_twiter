from aiogram.filters.state import State, StatesGroup


# Состояние для прохождения верификации
class FSMInputAccount(StatesGroup):
    account_name = State()
    execution_check = State()
