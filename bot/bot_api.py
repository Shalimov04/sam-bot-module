import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from shared.models import Genre, Log, Instance, Sequence, BotSetting
from bot.models import IssuesLog, ReportLog

cfg = BotSetting.objects.get()


def report(instance, timestamp, text=None):
    from .bot import bot
    ids = BotSetting.objects.all().last().recipients.split()
    for id in ids:
        message = f'🔗 {instance}\n⏱ {timestamp}'
        if text:
            message += f'\n{text}'

        bot.send_message(id, message)


def check_instance(instance):
    log = Log.objects.filter(instance=instance).latest('timestamp')
    if not log.is_responding:
        logs = Log.objects.filter(instance=instance, timestamp__gte=datetime.datetime.now() - \
                                                                    datetime.timedelta(minutes=cfg.max_downtime))
        for log in logs:
            if log.is_responding:
                return None
        try:
            issue = IssuesLog.objects.filter(instance=instance, type='dt').latest('timestamp')
        except IssuesLog.DoesNotExist:
            issue = None
        if not issue:
            report(instance, datetime.datetime.now(), '❌ недоступен больше допустимого времени')
            new_issue = IssuesLog(timestamp=datetime.datetime.now(), instance=instance, type='dt')
            new_issue.save()
            new_rlog = ReportLog(issue=new_issue, timestamp=new_issue.timestamp, type='new')
            new_rlog.save()
        else:
            rlog = ReportLog.objects.filter(issue=issue).latest('timestamp')
            if rlog.type == 'new':
                pass
            elif rlog.type == 'gone' and \
                    (datetime.datetime.now() - rlog.timestamp) >= datetime.timedelta(minutes=cfg.max_downtime):
                report(instance, datetime.datetime.now(), '❌ недоступен больше допустимого времени')
                new_issue = IssuesLog(timestamp=datetime.datetime.now(), instance=instance, type='dt')
                new_issue.save()
                new_rlog = ReportLog(issue=new_issue, timestamp=new_issue.timestamp, type='new')
                new_rlog.save()

    elif log.queued_tasks:
        if log.queued_tasks > cfg.max_tasks:
            logs = Log.objects.filter(instance=instance, timestamp__gte=datetime.datetime.now() - \
                                                                        datetime.timedelta(minutes=cfg.qtasks_max_time))
            for log in logs:
                if log.queued_tasks == 0:
                    return None
            try:
                issue = IssuesLog.objects.filter(instance=instance, type='qt').latest('timestamp')
            except IssuesLog.DoesNotExist:
                issue = None
            if not issue:
                report(instance, datetime.datetime.now(), f'😟 queued_tasks стабильно больше {cfg.max_tasks}')
                new_issue = IssuesLog(timestamp=datetime.datetime.now(), instance=instance, type='qt')
                new_issue.save()
                new_rlog = ReportLog(issue=new_issue, timestamp=new_issue.timestamp, type='new')
                new_rlog.save()
            else:
                rlog = ReportLog.objects.filter(issue=issue).latest('timestamp')
                if rlog.type == 'new':
                    pass
                elif rlog.type == 'gone' and \
                        (datetime.datetime.now() - rlog.timestamp) >= datetime.timedelta(minutes=cfg.qtasks_max_time):
                    report(instance, datetime.datetime.now(), f'😟 queued_tasks стабильно больше {cfg.max_tasks}')
                    new_issue = IssuesLog(timestamp=datetime.datetime.now(), instance=instance, type='qt')
                    new_issue.save()
                    new_rlog = ReportLog(issue=new_issue, timestamp=new_issue.timestamp, type='new')
                    new_rlog.save()


def reminder():
    issues = IssuesLog.objects.filter(is_solved=False)
    for issue in issues:
        last_report = ReportLog.objects.filter(issue=issue).latest('timestamp')

        if issue.type == 'dt':
            if (datetime.datetime.now() - last_report.timestamp) >= \
                    datetime.timedelta(minutes=cfg.problem_not_gone_delay):
                report(issue.instance, datetime.datetime.now(), '⏰ проблема не решена (downtime)')
                new_rlog = ReportLog(issue=issue, timestamp=datetime.datetime.now(), type='old')
                new_rlog.save()

        elif issue.type == 'qt':
            if (datetime.datetime.now() - last_report.timestamp) >= \
                    datetime.timedelta(minutes=cfg.problem_not_gone_delay):
                report(issue.instance, datetime.datetime.now(), '⏰ проблема не решена (queued tasks)')
                new_rlog = ReportLog(issue=issue, timestamp=datetime.datetime.now(), type='old')
                new_rlog.save()

        else:
            pass


def check_issues():
    issues = IssuesLog.objects.filter(is_solved=False, type='dt') | \
             IssuesLog.objects.filter(is_solved=False, type='qt')
    for issue in issues:
        log = Log.objects.filter(instance=issue.instance).latest('timestamp')
        if issue.type == 'dt':
            if log.is_responding:
                issue.is_solved = True
                issue.save()
                try:
                    last_report = ReportLog.objects.filter(issue=issue, type='gone').latest('timestamp')
                    if (datetime.datetime.now() - last_report.timestamp) >= \
                            datetime.timedelta(minutes=cfg.problem_gone_delay):
                        report(log.instance, datetime.datetime.now(), '✔ поднялся')
                        new_rlog = ReportLog(timestamp=datetime.datetime.now(), issue=issue, type='gone')
                        new_rlog.save()
                except ReportLog.DoesNotExist:
                    report(log.instance, datetime.datetime.now(), '✔ поднялся')
                    new_rlog = ReportLog(timestamp=datetime.datetime.now(), issue=issue, type='gone')
                    new_rlog.save()
        elif issue.type == 'qt':
            if log.queued_tasks == 0:
                issue.is_solved = True
                issue.save()
                try:
                    last_report = ReportLog.objects.filter(issue=issue, type='gone').latest('timestamp')
                    if (datetime.datetime.now() - last_report.timestamp) >= \
                            datetime.timedelta(minutes=cfg.problem_gone_delay):
                        report(log.instance, datetime.datetime.now(), '✔ queued_tasks = 0')
                        new_rlog = ReportLog(timestamp=datetime.datetime.now(), issue=issue, type='gone')
                        new_rlog.save()
                except ReportLog.DoesNotExist:
                    report(log.instance, datetime.datetime.now(), '✔ queued_tasks = 0')
                    new_rlog = ReportLog(timestamp=datetime.datetime.now(), issue=issue, type='gone')
                    new_rlog.save()
        else:
            pass


def search_for_issues():
    print(f'Issues search started at {datetime.datetime.now()}')
    for inst in Instance.objects.exclude(user_id='default'):
        check_instance(inst)
