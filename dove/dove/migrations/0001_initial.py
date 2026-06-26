import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(max_length=200, verbose_name='Assunto')),
                ('preview_text', models.CharField(blank=True, max_length=200, verbose_name='Texto de Preview')),
                ('body_html', models.TextField(verbose_name='Corpo HTML')),
                ('body_text', models.TextField(blank=True, verbose_name='Corpo Texto Simples')),
                ('status', models.CharField(
                    choices=[
                        ('draft', 'Rascunho'),
                        ('scheduled', 'Agendado'),
                        ('sending', 'Enviando'),
                        ('sent', 'Enviado'),
                    ],
                    default='draft', max_length=20, verbose_name='Status'
                )),
                ('scheduled_at', models.DateTimeField(blank=True, null=True, verbose_name='Agendado para')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Enviado em')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Campanha',
                'verbose_name_plural': 'Campanhas',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='CampaignSend',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField()),
                ('status', models.CharField(
                    choices=[
                        ('queued', 'Na Fila'),
                        ('sent', 'Enviado'),
                        ('failed', 'Falhou'),
                    ],
                    default='queued', max_length=20
                )),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('error', models.TextField(blank=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('campaign', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sends',
                    to='dove.campaign',
                )),
            ],
            options={
                'verbose_name': 'Envio',
                'verbose_name_plural': 'Envios',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='campaignsend',
            constraint=models.UniqueConstraint(fields=['campaign', 'email'], name='dove_campaignsend_campaign_email_uniq'),
        ),
        migrations.CreateModel(
            name='Unsubscribe',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(unique=True)),
                ('token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Descadastro',
                'verbose_name_plural': 'Descadastros',
                'ordering': ['-created_at'],
            },
        ),
    ]
