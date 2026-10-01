import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0002_supportticket_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='supportticket',
            options={'ordering': ['-submitted_on']},
        ),
        migrations.AddField(
            model_name='supportticket',
            name='status',
            field=models.CharField(
                choices=[
                    ('OPEN', 'Open'),
                    ('IN_PROGRESS', 'In Progress'),
                    ('RESOLVED', 'Resolved'),
                    ('CLOSED', 'Closed'),
                ],
                default='OPEN',
                max_length=11,
            ),
        ),
        migrations.AddField(
            model_name='supportticket',
            name='updated_on',
            field=models.DateTimeField(
                auto_now=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='TicketComment',
            fields=[
                ('id', models.BigAutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID',
                )),
                ('body', models.TextField()),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('author', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='ticket_comments',
                    to=settings.AUTH_USER_MODEL,
                )),
                ('ticket', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='comments',
                    to='tickets.supportticket',
                )),
            ],
            options={
                'ordering': ['created_on'],
            },
        ),
    ]
