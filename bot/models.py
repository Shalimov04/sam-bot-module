from django.db import models
from shared.models import Log, Instance
import datetime


'''
Боты рапортуют в телеграм, если:
* на каком-то сервере стабильно в течение двух часов число задач в очереди 1 или более
* какой-то сервер более чем полчаса не доступен

Требования к ботам:
* их настройки должны храниться в базе сервиса sam в таблице BotSettings и редактироваться через админку сервиса
* они должны сообщать о проблеме раз в сутки, если проблема не уходит
* если проблема уходит, должны сообщать об уходе проблемы, но не чаще раза в час
* не должны съедать ресурсов сервера в 10 раз больше мониторинга
'''


class IssuesLog(models.Model):
    timestamp = models.DateTimeField()
    instance = models.ForeignKey(to=Instance, on_delete=models.CASCADE)
    type = models.CharField(default=None, max_length=2) #dt/qt (downtime/queued tasks)
    is_solved = models.BooleanField(default=False)


class ReportLog(models.Model):
    timestamp = models.DateTimeField()
    issue = models.ForeignKey(to=IssuesLog, on_delete=models.CASCADE)
    type = models.CharField(default=None, max_length=4)  # new/old/gone (новая/старая/ушла)



