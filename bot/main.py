from telegram.ext import Updater, CommandHandler, ConversationHandler
from telegram.ext import CallbackQueryHandler
from telegram.ext.messagehandler import MessageHandler
from telegram.ext.filters import Filters
from telegram.ext.filters import MessageFilter
from telegram import Bot
from main_handlers import *
from calculator_handlers import *

# Этот класс используется для отбора сообщений, в которых обращение к боту.
# Его можно легко дополнить при необходимости реализации дополнительного функционала.
class FilterRequest(MessageFilter):
    def filter(self, message):
        return 'получить консультацию' in message.text.lower()

# Этот класс используется для выхода из диалога (его можно тоже настроить), используется,
# когда не найдено обработчика в диалоге
class FilterExit(MessageFilter):
    def filter(self, message):
        return (not 'получить консультацию' in message.text.lower())


if __name__ == "__main__":
    # Ниже регистрация диалога, в котором бот узнает от пользователя все нужные данные
    CH = ConversationHandler(entry_points=[MessageHandler(FilterRequest(), got_user_query)],
                             states={
                                 # В этом обработчике классификация запроса - определение подходящей программы
                                 # ипотечного кредитования и типа запрашиваемой информации (ставка и/или взнос)
                                 CLASSIFIER: [MessageHandler(Filters.text, got_user_response)],
                                 #  В этом обрабочике у пользователя уточняется, подойдет ли ему подобранная
                                 # программа, а также тип информации. Затем предлагается запрос недостающей
                                 # информации или рассчет ипотеки с помощью домклика
                                 ASKED_CATEGORY: [CallbackQueryHandler(callback=ask_user, pass_chat_data=True)],
                                 # В этом обработчике уточняется желание осуществить сделку через
                                 # домклик, ответ на вопрос в произвольной форме
                                 CALC_DOMCLICK: [MessageHandler(Filters.text, calc_domclick, pass_chat_data=True)],
                                 # В этом обработчике уточняется тип недвижимости (вторичная/новостройка), если из
                                 # предыдущей информации это неизвестно, ответ на вопрос в произвольной форме
                                 CALC_CAT_DETAILS: [
                                     MessageHandler(Filters.text, calc_cat_details, pass_chat_data=True)],
                                 # В этом обработчике уточняется желание страхования
                                 # ответ на вопрос в произвольной форме
                                 CALC_INSURANCE: [MessageHandler(Filters.text, calc_insurance, pass_chat_data=True)],
                                 # В этом обработчике уточняется желание электронной регистриции
                                 # сделки, ответ на вопрос в произвольной форме
                                 CALC_EREG: [MessageHandler(Filters.text, calc_ereg, pass_chat_data=True)],
                                 # В этом обработчике уточняется наличие зарплатной карты в СберБанке
                                 # ответ на вопрос в произвольной форме
                                 CALC_SBERCLIENT: [MessageHandler(Filters.text, calc_sberclient, pass_chat_data=True)],
                                 # В этом обработчике уточняется возможность подтверждения дохода,
                                 # если нет зарплатнной карты, ответ на вопрос в произвольной форме
                                 CALC_PROVESALARY: [
                                     MessageHandler(Filters.text, calc_provesalary, pass_chat_data=True)],
                                 # В этом обработчике уточняется желание использовать маткапитал,
                                 # если это возможно, ответ на вопрос в произвольной форме
                                 CALC_MATCAP: [MessageHandler(Filters.text, calc_matcap, pass_chat_data=True)],
                                 # В этом обработчике уточняется размер маткапитала при его использовании,
                                 # ответ в форме целого числа (легко можно настроить свой формат)
                                 CALC_GETMATCAP: [MessageHandler(Filters.text, calc_getmatcap, pass_chat_data=True)],
                                 # В этом обработчике уточняется размер первоначального взноса,
                                 # ответ в форме целого числа (легко можно настроить свой формат)
                                 CALC_OWNFUNDS: [MessageHandler(Filters.text, calc_ownfunds, pass_chat_data=True)],
                                 # В этом обработчике уточняется стоимость жилья,
                                 # ответ в форме целого числа (легко можно настроить свой формат)
                                 CALC_COST: [MessageHandler(Filters.text, calc_cost, pass_chat_data=True)],
                                 # В этом обработчике уточняется срок кредитования,
                                 # ответ в форме целого числа (легко можно настроить свой формат)
                                 CALC_TERM: [MessageHandler(Filters.text, calc_term, pass_chat_data=True)],
                                 # Это состояние ошибки, сюда можно переводить граф диалога при необходимости,
                                 # при этом можно предупредить об этом пользователя и использовать его данные
                                 ERROR_STATE: [MessageHandler(Filters.text, cancel)]
                             },
                             fallbacks=[CommandHandler("stop", cancel), MessageHandler(FilterExit(), cancel)],
                             allow_reentry=True)
    bot = Bot(token=TOKEN)
    updater = Updater(bot=bot)
    dispatcher = updater.dispatcher
    # Ниже регистрация обработчиков на стандарные команды start и help
    dispatcher.add_handler(CommandHandler("start", at_start_hello))
    dispatcher.add_handler(CommandHandler("help", help_command))
    # Регистрация диалога
    dispatcher.add_handler(CH)
    # Запуск приложения на сервере
    updater.start_polling()
    updater.idle()
