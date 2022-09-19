from django.conf import settings
from apscheduler.schedulers.background import BackgroundScheduler
from shared.models import BotSetting
from .bot_api import search_for_issues, check_issues, reminder, cfg
import telebot

bot = telebot.TeleBot(cfg.token)


def start():
    scheduler = BackgroundScheduler()
    scheduler.remove_all_jobs()
    scheduler.start()
    scheduler.add_job(search_for_issues, 'interval', minutes=1)
    scheduler.add_job(check_issues, 'interval', minutes=1)
    scheduler.add_job(reminder, 'interval', minutes=1)
    print('bot jobs:')
    scheduler.print_jobs()
    jobs = scheduler.get_jobs()
    for j in jobs:
        print('Job id = %s' % (j.id))
        print('Job name is "%s"' % (j.name))