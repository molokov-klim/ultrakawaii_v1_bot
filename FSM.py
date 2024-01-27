from aiogram.dispatcher.filters.state import State, StatesGroup


# Определение состояний для машины состояний
class Form(StatesGroup):
    email = State()  # состояние для email
    category = State()  # состояние для категории
