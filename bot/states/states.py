from aiogram.fsm.state import StatesGroup, State


class ReviewState(StatesGroup):
    rating = State()
    text = State()
    confirm = State()


class OrderState(StatesGroup):
    description = State()
    budget = State()
    contact = State()
    confirm = State()


class PostBuilderState(StatesGroup):
    text = State()
    media = State()
    buttons = State()
    button_text = State()
    preview = State()


class AdminPortfolioState(StatesGroup):
    title = State()
    description = State()
    link = State()
    category = State()
    confirm = State()
