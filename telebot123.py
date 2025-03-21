import random
import configparser
from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup
from BD_create import new_word_add, user_add, create_other_words_list, delete_word_from_db, take_target_word, take_translate, first_known_word

config = configparser.ConfigParser()
config.read('settings.ini')

print('Start telegram bot...')

state_storage = StateMemoryStorage()
token_bot = config['TOKEN']['telebot_token']
bot = TeleBot(token_bot, state_storage=state_storage)

known_users = []
userStep = {}
buttons = []


def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    if uid in userStep:
        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print("New user detected, who hasn't used \"/start\" yet")
        return 0


@bot.message_handler(commands=['start'])
def create_cards(message):
    cid = message.chat.id
    if cid not in known_users:
        known_users.append(cid)
        user_add(message)
        first_known_word(message.chat.id)
        userStep[cid] = 0
        bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)
    global buttons
    buttons = []
    target_word = random.choice(take_target_word(message))  # брать из БД
    translate = take_translate(target_word)  # брать из БД
    target_word_btn = types.KeyboardButton(translate)
    buttons.append(target_word_btn)
    others = random.choices(create_other_words_list(), k=3)  # брать из БД+++
    other_words_btns = [types.KeyboardButton(word) for word in others]
    buttons.extend(other_words_btns)
    random.shuffle(buttons)
    next_btn = types.KeyboardButton(Command.NEXT)
    add_word_btn = types.KeyboardButton(Command.ADD_WORD)
    delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
    buttons.extend([next_btn, add_word_btn, delete_word_btn])
    
    markup.add(*buttons)

    greeting = f"Выбери перевод слова:\n🇷🇺 {target_word}"
    bot.send_message(message.chat.id, greeting, reply_markup=markup)
    bot.set_state(message.from_user.id, MyStates.translate_word, message.chat.id)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        data['target_word'] = target_word
        data['translate_word'] = translate
        data['other_words'] = others


@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)


@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    msg = bot.send_message(message.chat.id, 'Введите слово, которое необходимо удалить из списка изучаемых:')
    print(msg)
    bot.register_next_step_handler(msg, delete_word_from_db)  # удалить из БД ++
    
   

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD) 
def add_word(message):
    cid = message.chat.id
    userStep[cid] = 1
    msg = bot.send_message(message.chat.id, 'Введите новое слово и его перевод через пробел')
    bot.register_next_step_handler(msg, new_word_add)
  


@bot.message_handler(func=lambda message: True, content_types=['text']) 
def message_reply(message):
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        translate_word = data['translate_word']
        if text == translate_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)

bot.add_custom_filter(custom_filters.StateFilter(bot))

bot.infinity_polling(skip_pending=True)