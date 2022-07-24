from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from transformers import pipeline

TOKEN = '5505680893:AAFMcsZTss1SKbbri5C3sqIjO7GddutERs4'  #

EXIT_DIALOG = -1  # Стандартный код для фреймворка, используемый для выхода из диалога
# Формулировки с сайта для удобстpва именования
LABELS_ALIAS = ["Вторичное жильё", "Новостройки", "Семейная ипотека", "Ипотека с господдержкой"]
# Лейблы должны быть достаточно представительными, чтобы zero-shot классификация работала хорошо
# эксперементально подобраны такие
LABELS = ["Ипотека на вторичное жильё", "Ипотека на новое жильё", "Ипотека для семьи", "Ипотека с господдержкой"]
# Словарь перехода между лейблами, нужен для удобства передачи информации между
# интерфейсом и внутренним хранением информации
label_transform = {label1: label2 for label1, label2 in zip(LABELS, LABELS_ALIAS)}
# Эти лейблы используются для классификиции типа информации, требуемой пользователем (ставка и/или взнос)
# также подобраны экспериментально
INFO_TYPE_LABELS = ['ставка', 'взнос', 'ставка и взнос']
interest_rate = 'процентная ставка'
to_pay = 'первоначальный взнос'
# Нужно для перехода между интерфейсом и внутренним хранением информации
YESNO = ['Да', 'Нет']
REALTY_TYPE = ["Вторичное жильё", "Новостройки"]
# Ниже определены строковые константы, использующиеся в формулировках бота
# Можно менять текст в соответствии с предпочтениями
ASK_REALTY_TYPE = 'Вы планируете покупать вторичное жилье или новостройку?'
ASK_DOMCLICK = 'Планируете воспользоваться скидкой 0,3% при покупке недвижимости на Домклик?'
ASK_INSURANCE = 'Планируете оформить страхование жизни и здоровья (-1% к ставке)?'
ASK_EREG = 'Будете ли использовать электронную регистрацию сделки (-0.3% к ставке)?'
ASK_CARD = 'Есть ли у Вас зарплатная карта СберБанка?'
ASK_MATCAP = 'Хотите использовать материнский капитал?'
ASK_FUNDS = 'Укажите первоначальный взнос (личные средства) в рублях:'
ASK_PROVE = 'Можете ли Вы подтвердить Ваш доход?'
ASK_MATCAPSUM = 'Введите сумму материнского капитала (одним числом, без пробелов или разделителей):'
SAY_INCORRECT = "Некорректные данные, рассчет окончен."
ASK_COST = 'Укажите стоимость недвижимости в рублях:'
DOMCLICK_ERROR_MSG = 'Введненные данные некорректны, сервер обработал запрос с ошибкой'
INCORRECT_INPUT_MSG = 'Ваши данные некорректны'
CANCEL_MSG = "Команды отменены. Рад был помочь!"
# Нумерация состояний в диалоге
CLASSIFIER, ERROR_STATE, ASKED_CATEGORY, ASKED_INFOTYPE, ASKED_CALCULATOR = range(5)
CALC_CAT_DETAILS, CALC_DOMCLICK, CALC_INSURANCE, CALC_EREG, CALC_SBERCLIENT = range(5, 10)
CALC_PROVESALARY, CALC_OWNFUNDS, CALC_COST, CALC_TERM, CALC_MATCAP, CALC_GETMATCAP = range(10, 16)
# Ставки и первоначальные взносы, взяты с сайта
RATES_PAYMENT = {
    "Вторичное жильё": [10.5, 0],
    "Новостройки": [10.5, 0],
    "Семейная ипотека": [5.3, 15],
    "Ипотека с господдержкой": [6.3, 15]
}
# Удобно для перехода между интерфейсом и внутренним хранением информации
adapt_word = {
    'ставка': 'процентную ставку',
    'взнос': to_pay
}
full_words = {
    'ставка': interest_rate,
    'взнос': to_pay
}
sentence_codes = {
    key: str(i) for i, key in enumerate(LABELS)
}
sentence_codes.update({INFO_TYPE_LABELS[i]: str(i + 4) for i in range(3)})
reverse_sentence_codes = {value: key for key, value in sentence_codes.items()}
# Здесь для каждого диалога будет хранится нужная для рассчетов информация, она удаляется
# после рассчетов
STORAGE = {}

classifier = pipeline(task="zero-shot-classification", device=-1, model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")


# Справочная информация при старте
def at_start_hello(update, context):
    htext = f"Добро пожаловать в СберБот, {update.effective_user.first_name}!\n"
    htext += "Это телеграм-приложение для получения справки по ипотеке.\n"
    htext += "Чтобы получить консультацию напишите в чате \"Получить консультацию\" или "
    htext += "выберите соответствующую команду в меню. Описание работы доступно по команде /help."
    buttons = [['Получить консультацию', ]]
    keyboard = ReplyKeyboardMarkup(buttons)
    update.message.reply_text(htext, reply_markup=keyboard)


# Справочная информация по комманде help
def help_command(update, context):
    htext = "Данный чатбот позволяет получить консультацию по ипотечному кредитованию\.\n"
    htext += "Чтобы получить консультацию нажмите кнопку \"Получить консультацию\" в меню или напишите это текстом\.\n"
    htext += "После начала диалога опишите в свободной форме, какой тип ипотечного кредитования Вас интересует, или просто опишите ваши условия"
    htext += " \(например, \"Я учитель, хочу узнать ставку по ипотеке\"\)\. После этого Вам будет предложен тариф, который вы можете скорректировать\.\n"
    htext += "После получения информации можно рассчитать с помощью встроенного калькулятора более подробные условия\.\n"
    htext += "Обращаем Ваше внимание, что данная информация носит справочный характер, более подробные рассчеты можно получить на сайте [Домклик](https://domclick.ru/ipoteka/calculator) "
    htext += "или в отделении банка\.\nДля старта нажмите /start\."
    update.message.reply_text(htext, parse_mode="MarkdownV2")


# Функция обработки входа в диалог
def got_user_query(update, context):
    buttons = [['Получить консультацию'], ['Отмена']]
    keyboard = ReplyKeyboardMarkup(buttons)
    update.message.reply_text("Что Вам хотелось бы узнать?", reply_markup=keyboard)

    return CLASSIFIER  # go to classifier stage


# В зависимости от нажатой кнопки, после уточнения информации, происходит печать ответа и предложение
# использовать дополнительные возможности
def ask_user(update, context):
    button_type, data = update.callback_query.data.split(':')
    # Если нужно печатать результат
    if button_type == 'print':
        category, info_type = data.split('|')
        category = reverse_sentence_codes[category]
        info_type = reverse_sentence_codes[info_type]
        rate, payment = RATES_PAYMENT[label_transform[category]]
        possible_add_info = ''
        if info_type == INFO_TYPE_LABELS[2]:
            response_text = f'В таком случае {interest_rate} от {rate}% годовых, а {to_pay} от {payment}%.'
        elif info_type == INFO_TYPE_LABELS[0]:
            response_text = f'В таком случае {interest_rate} от {rate}% годовых.'
            possible_add_info = 'взнос'
        else:
            response_text = f'В таком случае {to_pay} от {payment}%.'
            possible_add_info = 'ставка'
        if not update.effective_message.chat_id in STORAGE.keys():
            STORAGE[update.effective_message.chat_id] = {}
        STORAGE[update.effective_message.chat_id]['CreditType'] = label_transform[category]
        additive_buttons = [[InlineKeyboardButton('Рассчитать ипотеку', callback_data='catculate:0')]]
        if possible_add_info:
            additive_buttons += [[InlineKeyboardButton(f'Узнать {adapt_word[possible_add_info]}',
                                                       callback_data=f'get_more:{sentence_codes[category]}|{sentence_codes[possible_add_info]}')]]
        keyboard = InlineKeyboardMarkup(additive_buttons)
        context.bot.send_message(
            text=response_text,
            chat_id=update.effective_message.chat_id,
            reply_markup=keyboard
        )
    # Если нужно получить дополнительную информацию
    elif button_type == 'get_more':
        category, info_type = data.split('|')
        category = reverse_sentence_codes[category]
        info_type = reverse_sentence_codes[info_type]
        num_info = RATES_PAYMENT[label_transform[category]]
        if info_type == 'взнос':
            num_info = num_info[1]
        else:
            num_info = num_info[0]
        response = f'Для выбранной ипотеки {full_words[info_type]} составляет от {num_info}% годовых.'
        context.bot.send_message(
            text=response,
            chat_id=update.effective_message.chat_id
        )
        return EXIT_DIALOG
    #  Иначе перейти к рассчету ипотеки
    else:
        chat_id = update.effective_message.chat_id
        if STORAGE[chat_id]['CreditType'] == label_transform[LABELS[2]] or STORAGE[chat_id]['CreditType'] == \
                label_transform[LABELS[3]]:
            # Если вторичка, то базовая ставка
            context.bot.send_message(
                text=ASK_REALTY_TYPE,
                chat_id=update.effective_message.chat_id
            )
            return CALC_CAT_DETAILS
        elif STORAGE[chat_id]['CreditType'] == label_transform[LABELS[0]]:
            # Вторичка, базовая ставка
            STORAGE[chat_id]['productId'] = 3
            STORAGE[chat_id]['subproductId'] = 1
            # спросить про домклик
            context.bot.send_message(
                text=ASK_DOMCLICK,
                chat_id=update.effective_message.chat_id
            )
            return CALC_DOMCLICK

        else:
            # Новостройка, базовая ставка
            STORAGE[chat_id]['productId'] = 4
            STORAGE[chat_id]['subproductId'] = 2
            # Спросить про страхование жизни и здоровья
            context.bot.send_message(
                text=ASK_INSURANCE,
                chat_id=update.effective_message.chat_id
            )
            return CALC_INSURANCE


def cancel(update, context):
    update.message.reply_text(CANCEL_MSG)
    return EXIT_DIALOG


def got_user_response(update, context):
    if update.message.text.lower() == 'отмена':
        return EXIT_DIALOG
    clfd_cat = classifier(update.message.text, LABELS, multi_label=False)

    update.message.reply_text(f"Скорее всего вам подойдет программа \"{label_transform[clfd_cat['labels'][0]]}\"")
    clfd_query = classifier(update.message.text, INFO_TYPE_LABELS, multi_label=False)['labels'][0]
    # Уточнить, правильно ли определена категория ипотеки
    correct_keyboard = [[InlineKeyboardButton("Да, подойдет",
                                              callback_data=f'print:{sentence_codes[clfd_cat["labels"][0]]}|{sentence_codes[clfd_query]}')]]

    correct_keyboard += [
        [InlineKeyboardButton(f"Лучше \"{label_transform[clfd_cat['labels'][i]]}\"",
                              callback_data=f'print:{sentence_codes[clfd_cat["labels"][i]]}|{sentence_codes[clfd_query]}')]
        for i in range(1, 4)
    ]
    # sorted on probability
    ask_category = InlineKeyboardMarkup(correct_keyboard)
    update.message.reply_text("Верно?", reply_markup=ask_category)  # await  and async
    return ASKED_CATEGORY
