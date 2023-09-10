import random

import telebot
import sqlite3


from telebot import types, TeleBot

bot: TeleBot = telebot.TeleBot('TOKEN')

cups_max = {'default': 6, 'vip': 5, 'special': 3}

cardid = 0
drunkcups = 0
cups = 0
cupsav = 0
i = ''
tags = ''
tagsus = ''

cups_endarray = {''}


def getCupsEnding(number):
    number = number % 100
    if 11 <= number <= 19:
        end = f'Тебе доступно {number} бесплатных кружек'
    else:
        if number == 1:
            end = f'Тебе доступна {number} бесплатная кружка'
        elif number == 2 or number == 3 or number == 4:
            end = f'Тебе доступно {number} бесплатные кружки'
        else:
            end = f'Тебе доступно {number} бесплатных кружек'

    end += '\n\n🌱 Сообщи номер карты при заказе и получи напиток в подарок!'

    return end

def startcustomer(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, 'Привет\nВведи номер карты пользователя, чтобы начислить или выдать кружки',
                     reply_markup=markup)
    bot.register_next_step_handler(message, cupsinfo)

@bot.message_handler(commands=['start'])
def start(message):  # проверка на тэг админки и отображение кнопки админки / вывод главного меню
    conn = sqlite3.connect('heypopei.sql')
    cur = conn.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS users (id int primary key, tgid, cardid, cups int DEFAULT 0, '
                'tags TEXT DEFAULT " " NOT NULL, authcode)')
    conn.commit()
    cur.close()
    conn.close()

    tgid = message.from_user.id

    conn = sqlite3.connect('heypopei.sql')
    cur = conn.cursor()

    cur.execute("SELECT cardid, tags, cups FROM users WHERE tgid=?", (tgid,))
    info = cur.fetchone()

    cur.close()
    conn.close()

    markup = types.ReplyKeyboardMarkup()
    # Если запрос вернул 0 строк, то... / вывод главного меню
    if info is not None and 'admin' in info[1]:
        btnadm = types.KeyboardButton('Администрирование')
        btn1 = types.KeyboardButton('Добавить/Выдать кружки')
        markup.row(btnadm, btn1)
    if info is None:
        btn1 = types.KeyboardButton('Зарегистрироваться')
        markup.row(btn1)
    else:
        btn2 = types.KeyboardButton('Меню')
        btn3 = types.KeyboardButton('Акции')
        markup.row(btn2, btn3)
        btn4 = types.KeyboardButton('Контакты')
        btn5 = types.KeyboardButton('Как добраться?')
        markup.row(btn4, btn5)
    logo = open('./photo.jpg', 'rb')

    if info is not None and 'customer' in info[1]:
        startcustomer(message)
    elif info is not None:  # отображение приветственного сообщения
            i = 'default'
            cups = info[2]
            if 'vip' in info[1]:
                i = 'vip'
            if 'special' in info[1]:
                i = 'special'
            cupsav = cups // cups_max[i]
            napom = "<b>\n\nОбязательно сообщи при заказе номер карты, чтобы начислить выпитые кружки!</b>"
            bot.send_photo(message.chat.id, logo, f'Привет 🍃\n\nТвой номер карты: <b>{info[0]}</b>\n'
                                                  f'Выпито кружек ☕: <b>{cups} / {cups_max[i]}</b>'
                                                  f'\n\n<b>{getCupsEnding(cupsav) if cupsav > 0 else f"До бесплатной кружки осталось {cups_max[i] - cups} 🌱 {napom} "}</b>', reply_markup=markup, parse_mode='html')
    else:
        bot.send_photo(message.chat.id, logo, f'Привет!', reply_markup=markup)


@bot.message_handler(commands=['help'])
def main(message):
    bot.send_message(message.chat.id, 'Информация о помощи')


@bot.message_handler(commands=['id'])
def main(message):
    bot.reply_to(message, f'ID: {message.from_user.id}')

@bot.message_handler()
def inform(message):
    if message.text.lower() == 'зарегистрироваться':  # проверка есть ли уже пользователь в бд, \
        # создание номера кабинета и добавление пользователя в базу данных (ID Telegram, Card ID, tags)
        tgid = message.from_user.id
        # проверка, есть ли уже пользователь с
        # таким ид тг в базе
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute("SELECT cardid FROM users WHERE tgid=?", (tgid, ))
        info = cur.fetchone()

        # Если запрос вернул строку, то...
        if info is not None:
            bot.send_message(message.chat.id, f'Вы уже зарегистрированы в системе.\nВаш номер кабинета: {info[0]}')
        else:
            cardid = random.randint(10000, 99999)
            cur.execute("SELECT cardid FROM users WHERE cardid=?", (cardid,))
            info = cur.fetchone()
            if info is not None:  # проверка, есть ли уже такой номер карты. пока не будет сгенирирован индивидуальный н
                # мер, то программа будет продолжать генерировать его
                while info[0] == cardid:
                    cardid = random.randint(10000, 99999)
                    cur.execute("SELECT cardid FROM users WHERE cardid=?", (cardid,))
                    info = cur.fetchone()

            else:
                cur.execute(f'INSERT INTO users (tgid, cardid) VALUES ({tgid}, {cardid})')
                conn.commit()
                cur.close()
                conn.close()
                markup = types.ReplyKeyboardMarkup()
                btn2 = types.KeyboardButton('Меню')
                btn3 = types.KeyboardButton('Акции')
                markup.row(btn2, btn3)
                btn4 = types.KeyboardButton('Контакты')
                btn5 = types.KeyboardButton('Как добраться?')
                markup.row(btn4, btn5)
                bot.send_message(message.chat.id, f'Вы успешно зарегистрированы.\nНомер кабинета: {cardid} '
                                                  f'\nСообщите его сотруднику кофейни, чтобы участвовать в акции'
                                                  f' "Шестая кружка в подарок"!', reply_markup=markup)

    if message.text.lower() == 'меню' or message.text.lower() == '/menu':
        menu1 = open('./menu1.PNG', 'rb')
        menu2 = open('./menu2.PNG', 'rb')
        bot.send_media_group(message.chat.id,
                             [telebot.types.InputMediaPhoto(menu1), telebot.types.InputMediaPhoto(menu2)])
    if message.text.lower() == 'контакты' or message.text.lower() == '/contacts':
        bot.send_message(message.chat.id, 'Телефон: +7‒953‒625‒61‒95\nEmail: hey.popei.coffee@gmail.com',
                         parse_mode='html')
    if message.text.lower() == 'акции' or message.text.lower() == '/proms':
        tgid = message.from_user.id

        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute("SELECT tags FROM users WHERE tgid=?", (tgid,))
        info = cur.fetchone()
        global tags
        tags = info[0]

        if 'special' in tags:
            bot.send_message(message.chat.id, 'Персональное предложение: Третья кружка в подарок!')
        elif 'vip' in tags:
            bot.send_message(message.chat.id, 'Персональное предложение: Пятая кружка в подарок!')
        else:
            bot.send_message(message.chat.id, 'Шестая кружка в подарок!')
    if message.text.lower() == 'как добраться?' or message.text.lower() == '/address':
        bot.send_message(message.chat.id, '1-я Курская улица, 27, Новосильская слобода \
        \nЖелезнодорожный район, Орел, 302030\n Мы в <a href="https://yandex.ru/maps/org/ey_popey/192777247256/">'
                                          'Яндекс Картах</a>\n Мы в <a href="'
                                          'https://2gis.ru/orel/firm/70000001076379036">2ГИС</a>', parse_mode='html')
    if message.text.lower() == 'добавить/выдать кружки':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute("SELECT cardid, tags FROM users WHERE tgid=?", (tgid,))
        info = cur.fetchone()

        tags = info[1]

        if 'customer' in tags or 'admin' in tags:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Выйти')
            markup.row(btn1)
            bot.send_message(message.chat.id, f'Введите номер карты клиента', reply_markup=markup)
            bot.register_next_step_handler(message, cupsinfo)
        else:
            pass

    if message.text.lower() == 'администрирование':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute("SELECT cardid, tags FROM users WHERE tgid=?", (tgid,))
        info = cur.fetchone()

        if 'admin' in info[1]:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Управление ролями', callback_data='admtags')
            btn2 = types.InlineKeyboardButton('Выгрузка истории чашек', callback_data='admlogs')
            btn3 = types.InlineKeyboardButton('Выгрузка оценок', callback_data='admrates')
            btn4 = types.InlineKeyboardButton('Создание рассылки', callback_data='admnews')
            btn5 = types.InlineKeyboardButton('Что-то сломалось(помощь)', callback_data='admhelp')
            markup.row(btn1)
            markup.row(btn2, btn3)
            markup.row(btn4)
            markup.row(btn5)

            bot.send_message(message.chat.id, '<b>Добро пожаловать в панель администрирования 🍃:</b>', reply_markup=markup, parse_mode='html')
        else:
            pass

    if message.text.lower() == 'customer':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET tags = tags || ' ' || 'customer' WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'admin':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET tags = tags || ' ' || 'admin' WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'vip':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET tags = tags || ' ' || 'vip' WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'special':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET tags = tags || ' ' || 'special' WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'cleartags':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET tags = ' ' WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'clearcups':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET cups = 0 WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()
    if message.text.lower() == 'cupstest':
        tgid = message.from_user.id
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET cups = 12 WHERE tgid = {tgid}")
        conn.commit()
        cur.close()
        conn.close()

    if message.text.lower() == 'list':
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute('SELECT * FROM users')
        users = cur.fetchall()

        info = ''
        for el in users:
            info += f'TGID: {el[1]} ID Кабинета: {el[2]} Чашки: {el[3]} Тэги:{el[4]}\n'

        cur.close()
        conn.close()

        bot.send_message(message.chat.id, info)
    if message.text.lower() == 'рассылка':
        bot.send_message(757282114, f'Пиу пау')
    elif message.text.lower() == 'id':
        bot.reply_to(message, f'ID: {message.from_user.id}')




def cupsinfo(message):
    global cardid
    cardidstr = str(message.text.strip())
    if message.text.lower() == 'list' or message.text.lower() == '/menu' or message.text.lower() == '/proms' or message.text.lower() == '/contacts'or message.text.lower() == '/address'or message.text.lower() == 'cleartags':
        inform(message)
    elif message.text.strip() == 'Выйти' or message.text.lower() == '/start':
        start(message)
    else:
        global tags
        if cardidstr.isnumeric() == False:
            tgid = message.from_user.id
            conn = sqlite3.connect('heypopei.sql')
            cur = conn.cursor()

            cur.execute("SELECT tags FROM users WHERE tgid=?", (tgid,))
            info = cur.fetchone()
            tags = info[1]
            if 'admin' in tags:
                markup = types.ReplyKeyboardMarkup()
                btn1 = types.KeyboardButton('Выйти')
                markup.row(btn1)
            bot.send_message(message.chat.id, 'Пожалуйста, введите номер карты (число)')
            bot.register_next_step_handler(message, cupsinfo)
        else:
            cardid = int(message.text.strip())

            conn = sqlite3.connect('heypopei.sql')
            cur = conn.cursor()

            cur.execute("SELECT cups, tags FROM users WHERE cardid=?", (cardid,))

            info = cur.fetchone()

            if info is None:
                markup = types.ReplyKeyboardMarkup()
                if 'admin' in tags:
                    btn1 = types.KeyboardButton('Выйти')
                    markup.row(btn1)
                bot.send_message(message.chat.id, f'Пользователя {cardid} нет в системе. Пожалуйста, проверьте правильность'
                                                  f' ввода данных и попробуйте ещё раз', reply_markup=markup)
                bot.register_next_step_handler(message, cupsinfo)
            else:
                global i
                i = 'default'
                if 'vip' in info[1]:
                    i = 'vip'
                elif 'special' in info[1]:
                    i = 'special'

                markup = types.InlineKeyboardMarkup()
                global cups, cupsav
                cups = info[0]
                cupsav = cups // cups_max[i]
                if cupsav > 0:
                    btn1 = types.InlineKeyboardButton('Добавить ☕️', callback_data='cupadd')
                    btn2 = types.InlineKeyboardButton('Выдать бесплатные ☕️', callback_data='cupdelete')
                    markup.row(btn1, btn2)
                else:
                    btn1 = types.InlineKeyboardButton('Добавить ☕️', callback_data='cupadd')
                    markup.row(btn1)
                bot.send_message(message.chat.id, f'Пользователь: {cardid}\n'
                                                  f'Выпито кружек: {cups} / {cups_max[i]} \n'
                                                  f'Доступно беспл. кружек: {cups // cups_max[i]}', reply_markup=markup)


def cupadd(message):
    global drunkcups
    cardidstr = str(message.text.strip())
    cardidstr.translate({ord(i): None for i in '123'})
    if message.text.strip() == 'Выйти':
        start(message)
    else:
        if cardidstr.isnumeric() == False:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Выйти')
            markup.row(btn1)
            global cups

            bot.send_message(message.chat.id, f'Пожалуйста, введите количество кружек (число)', reply_markup=markup)
            bot.register_next_step_handler(message, cupadd)
        else:
            drunkcups = int(message.text.strip())
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Да', callback_data='cupaddyes')
            btn2 = types.InlineKeyboardButton('Нет', callback_data='cupaddno')
            markup.row(btn1, btn2)

            bot.send_message(message.chat.id, f'Добавляю {drunkcups} ☕ профилю {cardid} ?', reply_markup=markup)

def cupdelete(message):
    global drunkcups, cupsav
    cardidstr = str(message.text.strip())
    if message.text.strip() == 'Выйти':
        start(message)
    else:
        if cupsav == 1:
            drunkcups = 1
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton('Да', callback_data='cupdeleteyes')
            btn2 = types.InlineKeyboardButton('Нет', callback_data='cupdeleteno')
            markup.row(btn1, btn2)

            bot.send_message(message.chat.id, f'Выдаю {drunkcups} ☕ профилю {cardid} ?', reply_markup=markup)
        else:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Выйти')
            markup.row(btn1)
            if cardidstr.isnumeric() == False:
                bot.send_message(message.chat.id, f'Введите количество кружек для выдачи (число от 1 до {cupsav})', reply_markup=markup)
                bot.register_next_step_handler(message, cupdelete)
            else:
                drunkcups = int(message.text.strip())
                if drunkcups > cupsav or drunkcups <= 0:
                    bot.send_message(message.chat.id, f'Максимальное количество чашек <b>{cupsav}</b>' 
                                                      f'\n\nВведите количество чашек для выдачи '
                                                      f'(число от 1 до {cupsav})', reply_markup=markup,
                                     parse_mode='html')
                    bot.register_next_step_handler(message, cupdelete)
                else:
                    markup = types.InlineKeyboardMarkup()
                    btn1 = types.InlineKeyboardButton('Да', callback_data='cupdeleteyes')
                    btn2 = types.InlineKeyboardButton('Нет', callback_data='cupdeleteno')
                    markup.row(btn1, btn2)

                    bot.send_message(message.chat.id, f'Выдать {drunkcups} ☕ профилю {cardid} ?', reply_markup=markup)

def cupdeleteaccept(message):
    authcodestr = str(message.text.strip())
    if message.text.strip() == 'Выйти':
        start(message)
    else:
        if authcodestr.isnumeric() == False:
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Выйти')
            markup.row(btn1)
            global cups

            bot.send_message(message.chat.id, f'Пожалуйста, введите код авторизации (число)', reply_markup=markup)
            bot.register_next_step_handler(message, cupdeleteaccept)
        else:
            conn = sqlite3.connect('heypopei.sql')
            cur = conn.cursor()

            cur.execute("SELECT authcode FROM users WHERE cardid=?", (cardid,))

            info = cur.fetchone()

            cur.close()
            conn.close()

            authcode = info[0]
            markup = types.ReplyKeyboardMarkup()
            btn1 = types.KeyboardButton('Выйти')
            markup.row(btn1)
            if str(authcode) != authcodestr:
                bot.send_message(message.chat.id, f'Неверный код авторизации! Введите код ещё раз', reply_markup=markup)
                bot.register_next_step_handler(message, cupdeleteaccept)
            else:
                # ЗАПИСЬ В ЛОГИ
                global newcups, i, cups
                newcups = cups - drunkcups * cups_max[i]
                conn = sqlite3.connect('heypopei.sql')
                cur = conn.cursor()
                cur.execute(f"UPDATE users SET cups = {newcups} WHERE cardid = {cardid}")
                conn.commit()
                cur.close()
                conn.close()
                bot.send_message(message.chat.id, f'Выдали {drunkcups} ☕ пользователю {cardid}' '\n\nВведи номер карты пользователя, чтобы добавить или выдать кружки'  )
                bot.register_next_step_handler(message, cupsinfo)

def admtagsinfo(message):
    if message.forward_from is None:
        global cardid
        cardidstr = str(message.text.strip())
        if message.text.lower() == 'list' or message.text.lower() == '/menu' or message.text.lower() == '/proms'\
                or message.text.lower() == '/contacts' or message.text.lower() == '/address'\
                or message.text.lower() == 'cleartags':
            inform(message)
        elif message.text.strip() == 'Выйти' or message.text.lower() == '/start':
            start(message)
        else:
            global tags
            if not cardidstr.isnumeric():
                markup = types.ReplyKeyboardMarkup()
                btn1 = types.KeyboardButton('Выйти')
                markup.row(btn1)
                bot.send_message(message.chat.id, 'Пожалуйста, введите номер карты (число) или'
                                                  ' перешлите сообщение от пользователя')
                bot.register_next_step_handler(message, admtagsinfo)
            else:
                cardid = int(message.text.strip())

                conn = sqlite3.connect('heypopei.sql')
                cur = conn.cursor()

                cur.execute("SELECT cups, tags FROM users WHERE cardid=?", (cardid,))

                info = cur.fetchone()

                if info is None:
                    markup = types.ReplyKeyboardMarkup()
                    btn1 = types.KeyboardButton('Выйти')
                    markup.row(btn1)
                    bot.send_message(message.chat.id,
                                     f'Пользователя {cardid} нет в системе. Пожалуйста, проверьте правильность '
                                     'ввода данных и попробуйте ещё раз\n\nЕщё можно пепреслать сообщение пользователя.'
                                     ' Его данные возьмутся автоматически', reply_markup=markup)
                    bot.register_next_step_handler(message, admtagsinfo)
                else:
                    global i
                    i = 'default'
                    if 'vip' in info[1]:
                        i = 'vip'
                    elif 'special' in info[1]:
                        i = 'special'
                    global cups, cupsav
                    cups = info[0]
                    cupsav = cups // cups_max[i]
                    markup = types.InlineKeyboardMarkup()
                    if cups > 0:
                        btn1 = types.InlineKeyboardButton('Удалить кружки X', callback_data='admincupsdelete')
                        markup.row(btn1)
                    else:
                        pass
                    n2 = '\n\n'
                    n = '\n'
                    bot.send_message(message.chat.id, f'Пользователь: {cardid}\n'
                                                      f'Выпито кружек: {cups} / {cups_max[i]} \n'
                                                      f'Доступно беспл. кружек: {cups // cups_max[i]}'
                                                      f'{f"{n2}" "Роли:" if info[1] != " " else ""}'
                                                      f'{f"{n}" "Администратор" if "admin" in info[1] else ""}'
                                     ,
                                     reply_markup=markup)



    else:
        bot.send_message(message.chat.id, f'Пользователь ен зарегистрирован в системе. <a href="tg://user?id={message.forward_from.id}">Профиль пользователя</a>',
                         parse_mode='html')


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    if callback.data == 'cupadd':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, 'Введите количество выпитых кружек')
        bot.register_next_step_handler(callback.message, cupadd)
    if callback.data == 'cupdelete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        if cupsav > 0:
            cupdelete(callback.message)
        else:
            bot.send_message(callback.message.chat.id, f'Введите количество кружек для выдачи (от 1 до {cupsav}')
            bot.register_next_step_handler(callback.message, cupdelete)
    if callback.data == 'cupaddyes':
        newcups = cups + drunkcups
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        global tags
        markup = types.ReplyKeyboardMarkup()
        if 'admin' in tags:
            btn1 = types.InlineKeyboardButton('Выйти ', callback_data='exit')
            markup.row(btn1)
        bot.send_message(callback.message.chat.id, f'Готово!\nВведи номер карты пользователя, чтобы добавить или выдать кружки', reply_markup=markup)
        bot.register_next_step_handler(callback.message, cupsinfo)
        # ДОБАВИТЬ ЗАПИСЬ В ЛОГ
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET cups = {newcups} WHERE cardid = {cardid}")
        conn.commit()
        cur.close()
        conn.close()
    if callback.data == 'cupaddno':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        startcustomer(callback.message)
    if callback.data == 'cupdeleteyes':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        authcode = random.randint(1000, 9999)
        bot.send_message(callback.message.chat.id, f'Выслали код пользователю {cardid} ☕' '\n\n Введи его, пожалуйста')
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()

        cur.execute("SELECT tgid FROM users WHERE cardid=?", (cardid,))

        info = cur.fetchone()

        cur.close()
        conn.close()

        tgidus = info[0]

        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET authcode = {authcode} WHERE cardid = {cardid}")
        conn.commit()
        cur.close()
        conn.close()
        bot.send_message(tgidus, 'Привет 🍃\n'f'Твой код авторизации {authcode}' '\nСообщи его, чтобы получить' f' {drunkcups} ☕ бесплатно')
        bot.register_next_step_handler(callback.message, cupdeleteaccept)
    if callback.data == 'cupdeleteno':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        startcustomer(callback.message)
    if callback.data == 'admtags':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        markup = types.ReplyKeyboardMarkup()
        btn1 = types.KeyboardButton('Выйти')
        markup.row(btn1)
        bot.send_message(callback.message.chat.id,'Управление ролями 🍃\n\nПерешлите сообщение пользователя (данные подтянутся автоматически) или введите номер карты, чтобы просмотреть роли или изменить их', reply_markup=markup)
        bot.register_next_step_handler(callback.message, admtagsinfo)
    if callback.data == 'admincupsdelete':
        bot.delete_message(callback.message.chat.id, callback.message.message_id)
        bot.send_message(callback.message.chat.id, f'Введите количество кружек для удаления (от 1 до {cups}')
        bot.register_next_step_handler(callback.message, cupdelete)
        '''
        conn = sqlite3.connect('heypopei.sql')
        cur = conn.cursor()
        cur.execute(f"UPDATE users SET cups = {newcups} WHERE cardid = {cardid}")
        conn.commit()
        cur.close()
        conn.close()
        '''
    """
    conn = sqlite3.connect('heypopei.sql')
    cur = conn.cursor()

    cur.execute('SELECT * FROM users')
    users = cur.fetchall()

    info = ''
    for el in users:
        info += f'TGID: {el[1]} ID Кабинета: {el[2]} Чашки: {el[3]} Тэги:{el[4]}\n'

    cur.close()
    conn.close()

    bot.send_message(callback.message.chat.id, info)
    """

bot.infinity_polling()
