# Generated by Django 3.2.5 on 2022-09-14 22:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0005_auto_20220902_1132'),
    ]

    operations = [
        migrations.AddField(
            model_name='reportlog',
            name='type',
            field=models.CharField(default=None, max_length=4),
        ),
        migrations.AlterField(
            model_name='issueslog',
            name='type',
            field=models.CharField(default=None, max_length=2),
        ),
        migrations.AlterField(
            model_name='reportlog',
            name='issue',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bot.issueslog'),
        ),
    ]
