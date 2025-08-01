import telebot
import os
import json
import datetime

user = os.getlogin()
folder = "C:/Users/" + user + "/Desktop/1/Gop-Coin"
bot = telebot.TeleBot("TOKEN")
date = datetime.datetime.now()

help_text = """Команды гоп-коин бота:
/help - посмотреть команды бота.
/balance - посмотреть свой баланс.
/error - сообщить об ошибке.
/donate - задонатить на игру.
/send "сумма" "ник" - перевести гоп-коин человеку.
/list - посмотреть список доната.
/info - посмотреть информацию о гоп-коине.
/ids - посмотреть список id.
/setgame - сделать статус игры."""

def history(text, iid):
    try:
        with open(folder + "/data/history.txt", 'a', encoding='utf-8') as file:
            file.write(f"\n[{datetime.datetime.now()}] | [{iid}] : {text}")
    except Exception as e:
        print(f"Error : {e}")

def is_whitelisted(user_id):
    try:
        with open(folder + "/data/white_list.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        w_list = data.get("white_list", [])
        return str(user_id) in w_list
    except (FileNotFoundError, json.JSONDecodeError):
        return False

@bot.message_handler(commands=['start'])
def start(message):
    history(message.text, message.from_user.id)
    if is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Привет, я бот для обмена/перевода/доната гоп-коинов. Напиши /help для получения списка команд👋")
    else:
        bot.reply_to(message, "Вы не в белом списке❌")
        print(f"New ID : {message.from_user.id}")

@bot.message_handler(commands=['help'])
def send_welcome(message):
    history(message.text, message.from_user.id)
    if is_whitelisted(message.from_user.id):
        bot.reply_to(message, help_text)
    else:
        bot.reply_to(message, "Вы не в белом списке❌")

@bot.message_handler(commands=['balance'])
def get_balance(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    
    try:
        with open(folder + "/data/balance.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        user_balance = data.get(str(message.from_user.id), 0)
        if isinstance(user_balance, (list, tuple)):
            user_balance = user_balance[0]
        bot.reply_to(message, f"Ваш баланс : {user_balance} GNC")
    except Exception as e:
        bot.reply_to(message, f"Ошибка : {str(e)}")

@bot.message_handler(commands=['ids'])
def send_ids(message):
    history(message.text, message.from_user.id)
    if is_whitelisted(message.from_user.id):
        ids = """Вот список id :
IDS"""
        bot.reply_to(message, ids)
    else:
        bot.reply_to(message, "Вы не в белом списке❌")

@bot.message_handler(commands=['send'])
def send(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    
    try:
        split = message.text.split()
        if len(split) < 3:
            bot.reply_to(message, "Использование: /send <сумма> <ID получателя>")
            return
            
        try:
            gop = float(split[1])  # Принимаем как float
            to = split[2]
        except (ValueError, IndexError):
            bot.reply_to(message, "Ошибка формата. Используйте: /send <число> <ID получателя>")
            return
        
        if not is_whitelisted(to):
            bot.reply_to(message, "Получатель не существует или не в белом списке❌, напишите /ids чтобы узнать id")
            return
            
        min_gop = 0.0005
        if gop < min_gop:
            bot.reply_to(message, f"Минимальная сумма перевода: {min_gop} GNC (1 копейка)")
            return
            
        # Обновляем балансы
        with open(folder + "/data/balance.json", 'r+', encoding='utf-8') as file:
            balance_data = json.load(file)
            sender_balance = balance_data.get(str(message.from_user.id), 0)
            if isinstance(sender_balance, (list, tuple)):
                sender_balance = sender_balance[0]
            else:
                sender_balance = float(sender_balance)
            
            if gop <= 0:
                bot.reply_to(message, "Сумма должна быть положительной!")
                return
                
            if sender_balance < gop:
                bot.reply_to(message, "Недостаточно средств!")
                return
                
            balance_data[str(message.from_user.id)] = round(sender_balance - gop, 4)
            receiver_balance = balance_data.get(to, 0)
            if isinstance(receiver_balance, (list, tuple)):
                receiver_balance = receiver_balance[0]
            else:
                receiver_balance = float(receiver_balance)
            balance_data[to] = round(receiver_balance + gop, 4)
            
            file.seek(0)
            json.dump(balance_data, file, indent=4, ensure_ascii=False)
            file.truncate()

        formatted_gop = "{0:.4f}".format(gop).rstrip('0').rstrip('.') if '.' in "{0:.4f}".format(gop) else "{0:.4f}".format(gop)
        
        # Обновляем общую сумму переводов (sended)
        try:
            with open(folder + "/data/info.json", 'r+', encoding='utf-8') as file:
                info_data = json.load(file)
                current_sended = info_data.get("sended", 0)
                if isinstance(current_sended, (list, tuple)):
                    current_sended = current_sended[0]
                info_data["sended"] = round(float(current_sended) + gop, 4)
                
                file.seek(0)
                json.dump(info_data, file, indent=4, ensure_ascii=False)
                file.truncate()
        except Exception as e:
            bot.reply_to(message, f"Ошибка при обновлении статистики: {e}")
            return
        
        bot.reply_to(message, f"Успешно переведено {formatted_gop} GNC пользователю {to}")
        
        try:
            bot.send_message(
                to, 
                f"🔔 Вам перевели {formatted_gop} GNC от пользователя @{message.from_user.username}\n"
                f"Ваш новый баланс: {balance_data[to]} GNC"
            )
        except Exception as e:
            bot.reply_to(message, f"Не удалось отправить уведомление получателю {to}: {e}")

    except Exception as e:
        bot.reply_to(message, f"Ошибка : {str(e)}")
        print(f"Error in send: {e}")

@bot.message_handler(commands=['info'])
def info_command(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    try:
        with open(folder + "/data/info.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        gnk = data.get("gnk", 0)
        sell = data.get("sell", 0)
        course = data.get("course", 0)
        working = data.get("working", 0)
        launch_date = data.get("data", 0)
        game = data.get("game", 0)
        sended = data.get("sended", 0)
        
        info_message = f"""Информация о гоп-коине
В наличие : {gnk} GNC
Проданно : {sell} GNC
Цена : {course} RUB
Работает : {working}
Дата запуска : {launch_date}
Текущая игра : {game}
Всего переведено гоп-коинов : {sended}
"""
        bot.reply_to(message, info_message)
    except Exception as e:
        bot.reply_to(message, f"Ошибка : {str(e)}")

@bot.message_handler(commands=['setgame'])
def setgame(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    
    try:
        split = message.text.split(maxsplit=1)
        if len(split) < 2:
            bot.reply_to(message, "Использование: /setgame <название игры>")
            return
        game_name = split[1]
        with open(folder + "/data/info.json", 'r', encoding='utf-8') as file:
            data = json.load(file)
        data['game'] = game_name
        with open(folder + "/data/info.json", 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)
        bot.reply_to(message, f"Статус игры изменён на: {game_name}")
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {str(e)}")

@bot.message_handler(commands=['list'])
def list_command(message):  # Переименовал, чтобы не конфликтовало со list()
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    donate_list = """Список донатов в наших играх!
/donate <название доната>

rebirth - возрождение (в гопнике/тёте зине)

slow - замедление (гопник/шизик/тётя зина) (секунды)"""
    bot.reply_to(message, donate_list)

@bot.message_handler(commands=['donate'])
def donate(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    try:
        split = message.text.split(maxsplit=2)  # Разбиваем максимум на 3 части
        donat = split[1]
        sec = split[2] if len(split) > 2 else None
        
        bot.reply_to(message, f"Заявка на донат '{donat}' подана.")
        with open(folder + "/data/history.txt", "a", encoding='utf-8') as file:
            file.write(f"\n[{datetime.datetime.now()}] Заявка от {message.from_user.id} на донат '{donat}' (сек: {sec})")
    except Exception as e:
        bot.reply_to(message, f"Использование: /donate <название> [секунды]\nОшибка: {e}")

@bot.message_handler(commands=['error'])
def error_report(message):
    history(message.text, message.from_user.id)
    if not is_whitelisted(message.from_user.id):
        bot.reply_to(message, "Вы не в белом списке❌")
        return
    try:
        error_desc = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else "Не указано"
        bot.reply_to(message, f"Заявка на ошибку принята: {error_desc}")
        with open(folder + "/data/history.txt", "a", encoding='utf-8') as file:
            file.write(f"\n[{datetime.datetime.now()}] Ошибка от {message.from_user.id}: {error_desc}")
    except Exception as e:
        bot.reply_to(message, f"Использование: /error <описание>\nОшибка: {e}")

print("Bot activated!")
bot.infinity_polling()
