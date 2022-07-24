import json
import requests
from main_handlers import *
domclick_link = "https://api.domclick.ru/calc/api/v8/calculate"
EXIT_DIALOG = -1 # Стандартный код для фреймворка, используемый для выхода из диалога
def get_domclick_response(client_descr):
    # Используемая ниже структура данных иммитирует формат посылаемого json в запросе на сервер домклика
    default_dict = {'calculationParams': {'productId': -1,
                                          'discountsActivity': {'1': True},
                                          'subsidyIds': [],
                                          'categoryCode': 'salaryClient',
                                          'loanConditions': {'realtyCost': -1,
                                                             'deposit': -1,
                                                             'maternalFund': -1,
                                                             'creditTerm': -1},
                                          # В данной версии не используется регион, чтобы не усложнять лишним
                                          'regionNumber': 0,
                                          'subproductCode': None,
                                          'subproductId': -1,
                                          'additionalServicesParams': None,
                                          'externalDiscountIds': []}}
    # Ниже копирование данных, полученных от пользователя, в нужную структуру
    default_dict['calculationParams']['categoryCode'] = client_descr['categoryCode']
    default_dict['calculationParams']['discountsActivity'] = {}
    default_dict['calculationParams']['productId'] = client_descr['productId']
    default_dict['calculationParams']['subproductId'] = client_descr['subproductId']
    # Далее формируется список с флагами-скидками для пользователя в соответствии с
    # выбранной ипотечной программой
    if not client_descr['productId'] == 10:
        default_dict['calculationParams']['discountsActivity'].update({
            2: '2' in client_descr['discountsActivity'],
            7: '7' in client_descr['discountsActivity']
        })
    else:
        default_dict['calculationParams']['discountsActivity'].update({
            7: '7' in client_descr['discountsActivity']
        })
    if client_descr['productId'] == 3:
        default_dict['calculationParams']['discountsActivity'].update({
            1: '1' in client_descr['discountsActivity']
        })
    # Ниже копирование данных, полученных от пользователя, в нужную структуру
    default_dict['calculationParams']['loanConditions']['realtyCost'] = client_descr['realtyCost']
    default_dict['calculationParams']['loanConditions']['deposit'] = client_descr['deposit'] + client_descr[
        'maternalFund']
    default_dict['calculationParams']['loanConditions']['maternalFund'] = client_descr['maternalFund']
    default_dict['calculationParams']['loanConditions']['creditTerm'] = client_descr['creditTerm']
    data = json.dumps(default_dict)  # Перевод в json
    # Далее отправляется запрос на сервер
    domclick_response = requests.post(domclick_link, headers={'Content-Type': 'application/json'}, data=data)
    return json.loads(domclick_response.text)

def make_mortgage_report(response):
    # Тут формируется отчет по результатам ответа от сервера
    response = response["data"]["calculationResult"]
    report = f'Отлично, условия рассчитаны!\n\nДля Вас ежемесячный платеж составит {response["monthlyPayment"]} руб.\n'
    report += f'Процентная ставка {response["creditRate"]}% годовых\n'
    report += f'Сумма кредита: {response["creditSum"]} руб.\n'
    tax_deduction = response["propertyTaxDeduction"] + response["mortgageInterestTaxDeduction"]
    report += f'Налоговый вычет: {tax_deduction} руб.\n'
    report += f'Необходимый доход: {response["requiredIncome"]} руб.\n'
    report += f'Переплата: {response["overpayment"]} руб.'
    return report
def is_correct_data(data):
    # В этой функции можно проверить корректность данных,
    # для простоты проверки не производится
    return True  # default

def calc_cat_details(update, context):
    # Уточнить, новостройка или вторичка для семейной/господдержки
    type_estate = classifier(update.message.text, REALTY_TYPE, multi_label=False)['labels'][0] == REALTY_TYPE[0]
    chat_id = update.effective_message.chat_id
    if type_estate:
        # Вторичка, базовая ставка
        STORAGE[chat_id]['productId'] = 3
        STORAGE[chat_id]['subproductId'] = 1
        # спросить про домклик
        update.message.reply_text(ASK_DOMCLICK)
        return CALC_DOMCLICK

    elif STORAGE[chat_id]['CreditType'] == label_transform[LABELS[2]]:
        # Новостройка, семейная ставка
        STORAGE[chat_id]['productId'] = 10
        STORAGE[chat_id]['subproductId'] = 8
        # Спросить про электронную регистрацию
        update.message.reply_text(ASK_EREG)
        return CALC_EREG
    else:
        # Новостройка, ставка с господдержкой
        STORAGE[chat_id]['productId'] = 16
        STORAGE[chat_id]['subproductId'] = 12
        update.message.reply_text(ASK_INSURANCE)
        return CALC_INSURANCE


def calc_insurance(update, context):
    # Узнать про использоание страхования жизни и здоровья
    chat_id = update.effective_message.chat_id
    use_insurance = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if use_insurance:
        if 'discountsActivity' in STORAGE[chat_id].keys():
            STORAGE[chat_id]['discountsActivity'].append('2')
        else:
            STORAGE[chat_id]['discountsActivity'] = ['2']
    update.message.reply_text(ASK_EREG)
    return CALC_EREG


def calc_domclick(update, context):
    # Узнать про домклик
    chat_id = update.effective_message.chat_id
    use_domclick = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if use_domclick:
        if 'discountsActivity' in STORAGE[chat_id].keys():
            STORAGE[chat_id]['discountsActivity'].append('1')
        else:
            STORAGE[chat_id]['discountsActivity'] = ['1']
    update.message.reply_text(ASK_INSURANCE)
    return CALC_INSURANCE


def calc_ereg(update, context):
    # Узнать про использоание электронной регистрации сделки
    chat_id = update.effective_message.chat_id
    use_ereg = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if use_ereg:
        if 'discountsActivity' in STORAGE[chat_id].keys():
            STORAGE[chat_id]['discountsActivity'].append('7')
        else:
            STORAGE[chat_id]['discountsActivity'] = ['7']
    else:
        if not 'discountsActivity' in STORAGE[chat_id].keys():
            STORAGE[chat_id]['discountsActivity'] = []
    # Спросить про зарплатную карту
    update.message.reply_text(ASK_CARD)
    return CALC_SBERCLIENT


def calc_sberclient(update, context):
    # Есть ли зп карта ?
    chat_id = update.effective_message.chat_id
    answer = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if answer:
        STORAGE[chat_id]['categoryCode'] = 'salaryClient'
        if STORAGE[chat_id]['productId'] in [4, 3]:
            # Есть возможность использования маткапитала - спросить
            update.message.reply_text(ASK_MATCAP)
            return CALC_MATCAP
        update.message.reply_text(ASK_FUNDS)
        STORAGE[chat_id]['maternalFund'] = 0 # не использовать маткапитал
        return CALC_OWNFUNDS
    else:
        STORAGE[chat_id]['maternalFund'] = 0 # не использовать маткапитал
        # Узнать возможность подтверждения доходов, если нет карты
        update.message.reply_text(ASK_PROVE)
        return CALC_PROVESALARY


def calc_provesalary(update, context):
    # Возможность подтверждения дохода
    chat_id = update.effective_message.chat_id
    answer = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if answer:
        # Есть возможность подтверждения дохода
        STORAGE[chat_id]['categoryCode'] = 'canConfirmIncome'
    else:
        # нет возможности подтверждения дохода
        STORAGE[chat_id]['categoryCode'] = 'cannotConfirmIncome'
    if STORAGE[chat_id]['productId'] in [4, 3]:
        # Есть возможность использования маткапитала
        update.message.reply_text(ASK_MATCAP)
        return CALC_MATCAP
    STORAGE[chat_id]['maternalFund'] = 0
    update.message.reply_text(ASK_FUNDS)
    return CALC_OWNFUNDS


def calc_matcap(update, context):
    # Узнать размер маткапитала
    chat_id = update.effective_message.chat_id
    answer = classifier(update.message.text, YESNO, multi_label=False)['labels'][0] == YESNO[0]
    if answer:
        # Если используется, то уточнить сумму
        update.message.reply_text(ASK_MATCAPSUM)
        return CALC_GETMATCAP
    else:
        # Если не используется, уточнить первоначальный взнос
        STORAGE[chat_id]['maternalFund'] = 0
        update.message.reply_text(ASK_FUNDS)
        return CALC_OWNFUNDS


def calc_getmatcap(update, context):
    chat_id = update.effective_message.chat_id
    try:
        matcap = int(update.message.text)
    except:
        update.message.reply_text(SAY_INCORRECT)
        return EXIT_DIALOG
    STORAGE[chat_id]['maternalFund'] = matcap
    update.message.reply_text(ASK_FUNDS)
    return CALC_OWNFUNDS


def calc_ownfunds(update, context):
    # Получить сумму взноса
    chat_id = update.effective_message.chat_id
    try:
        deposit = int(update.message.text)
    except:
        # Введена некорректная сумма
        update.message.reply_text(SAY_INCORRECT)
        return EXIT_DIALOG
    STORAGE[chat_id]['deposit'] = deposit
    update.message.reply_text(ASK_COST)
    return CALC_COST


def calc_cost(update, context):
    # Узнать стоимость приобретаемой недвижимости
    chat_id = update.effective_message.chat_id
    try:
        deposit = int(update.message.text)
    except:
        # Введена некорректная сумма
        update.message.reply_text(SAY_INCORRECT)
        return EXIT_DIALOG
    STORAGE[chat_id]['realtyCost'] = deposit
    update.message.reply_text('Укажите срок кредита (в годах):')
    return CALC_TERM

def calc_term(update, context):
    # Узнать срок ипотеки
    chat_id = update.effective_message.chat_id
    try:
        years = int(update.message.text)
    except:
        # Введено некорректное число
        update.message.reply_text(SAY_INCORRECT)
        return EXIT_DIALOG
    # Запомнить введенные данные
    STORAGE[chat_id]['creditTerm'] = years
    # Проверка корректности заполнения данных пользователем
    if is_correct_data(STORAGE[chat_id]):
        domclick_response = get_domclick_response(STORAGE[chat_id])
        # чтобы не накапливались данные (или если это нелегально) удаляем данные пользователя
        del STORAGE[chat_id]
        if domclick_response['success']:
            # Запрос обработан
            report = make_mortgage_report(domclick_response)
            update.message.reply_text(report)
        else:
            # Что-то пошло не так - можно добавить свои обработччики
            try:
                error_message = domclick_response['errors'][0]['message']
            except:
                # Если вдруг нет нужного поля, то тогда что-то не то -
                # можно предупредить или послать запрос заново
                error_message = DOMCLICK_ERROR_MSG
            update.message.reply_text(error_message)
        return EXIT_DIALOG
    else:
        # Тут можно рассказать, что именно не так во входных данных
        update.message.reply_text(INCORRECT_INPUT_MSG)
    return EXIT_DIALOG