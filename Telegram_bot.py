import logging
from telegram.ext import Updater, CommandHandler
import os
import csv

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

def send_plot(update, context):
    try:
        file = context.args[0]
        os.system("telegram-send --image " + (str(file).upper() + '.png') + " --caption " + str(file).upper())
        print((str(file).upper() + '.png'))
    except Exception as e:
        update.message.reply_text(e)
        
def update_owned_list(update, context):
    try:
        ff = context.args
        file = open('owned.csv', 'w+', newline ='') 
        with file:
            write = csv.writer(file)
            write.writerow(ff)
        file.close()
        owned(update, context)
    except Exception as e:
        update.message.reply_text(e)

def owned(update, context):
    try:
        os.system("cat owned.csv | telegram-send --stdin")
    except Exception as e:
        update.message.reply_text(e)
        
def main():
    updater = Updater("2134101372:AAHmfj0j7CEBzETwqdTKKdmtznVieDfbtvs", use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("plot", send_plot))
    dp.add_handler(CommandHandler("owned_update", update_owned_list))
    dp.add_handler(CommandHandler("owned", owned))
    dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
