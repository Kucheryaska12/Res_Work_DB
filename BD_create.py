import sqlalchemy as sq
from sqlalchemy.orm import sessionmaker, declarative_base, relationship
import configparser

config = configparser.ConfigParser()
config.read('settings.ini')

DNS = f'postgresql://{config['TOKEN']['login']}:{config['TOKEN']['password']}@localhost:5432/TG_bot_db'
engine = sq.create_engine(DNS)
Base = declarative_base()

class Joint_Words(Base): # Создаем таблицу изучаемых слов
    __tablename__ = 'joint_words'
    id = sq.Column(sq.Integer, primary_key=True)
    target_word = sq.Column(sq.String(length=40), nullable=False)
    translate = sq.Column(sq.String(length=40), nullable=False)
    user_id = sq.Column(sq.Integer, sq.ForeignKey('users.user_id'), nullable = False)

class Other_Words(Base): # Создаем таблицу для слов, используемых для перемешки с верным словом
    __tablename__ = 'other_words'
    others = sq.Column(sq.String(length=40), nullable=False, primary_key=True)

class Users(Base): #Создаем таблицу пользователей
    __tablename__ = 'users'
    user_id = sq.Column(sq.Integer, primary_key=True)

    joint_words = relationship(Joint_Words, backref='users')


def create_tables(engine): #Метод для создания таблиц в базе данных
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

create_tables(engine)

Session = sessionmaker(bind = engine)
session = Session()

def new_word_add(message): #Метод для добавления в БД нового изучаемого слова
    words = message.text.split()
    if words[0] not in [i for i in session.query(Joint_Words.target_word).
                        filter(Joint_Words.user_id == message.chat.id).all()]:
        new_word = Joint_Words(target_word=words[0], translate=words[1], user_id=message.chat.id)
        session.add(new_word)
        session.commit()
    

def delete_word_from_db(message): #Метод для удаления из БД изученного слова
    print(message.text, message.chat.id)
    if session.query(Joint_Words).filter(Joint_Words.target_word == message.text and 
                                         Joint_Words.user_id == message.chat.id) is not None:
        session.query(Joint_Words).filter(Joint_Words.target_word == message.text and 
                                          Joint_Words.user_id == message.chat.id).delete()
        session.commit()
        return f'Слово {message.text} удалено'
    else:
        return f'Слова {message.text} нет в списке изучаемых'
        

def user_add(message): #Метод для добавления нового пользователя
    user = message.chat.id
    new_user = Users(user_id=user)
    session.add(new_user)
    session.commit()


def add_words_to_Others(word_list): #Метод для добавления в базу данных слов для смешивания с правильным словом в выводе
    for word in word_list:
        new_other_word = Other_Words(others=word)
        session.add(new_other_word)
        session.commit()


def first_known_word(id): #Метод для добавления первого изученного слова для первого вывода
    first_word = Joint_Words(target_word='Мир', translate='Peace', user_id = id)
    session.add(first_word)
    session.commit()
  

random_words = ['Elephant', 'Sunset', 'Whisper', 'Galaxy', 'Adventure', 'Umbrella', 
                'Mystery', 'Rainbow', 'Butterfly', 'Freedom']
add_words_to_Others(random_words)


def create_other_words_list(): #Метод для создания списка всех слов, необходимых для смешивания яс правильным переводом
    other_words = []
    for i in [word for word in session.query(Other_Words.others).all()]:
        other_words.append(i[0])
    return other_words


def take_target_word(message): #Метод для создания списка известных слов
    known_words = []
    for i in [word for word in  session.query(Joint_Words.target_word).
              filter(Joint_Words.user_id == message.chat.id).all()]:
        known_words.append(i[0])
    return known_words


def take_translate(word): #Метод для перевода слова
    translate = [i for i in session.query(Joint_Words.translate).
                 filter(Joint_Words.target_word == word).all()][0][0]
    return translate

session.commit()
session.close()