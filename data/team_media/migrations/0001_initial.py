# Generated by Django 4.1.13 on 2024-12-02 06:04

from django.db import migrations, models
import systems.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TeamMedia',
            fields=[
                ('created', models.DateTimeField(editable=False, null=True)),
                ('updated', models.DateTimeField(editable=False, null=True)),
                ('id', models.CharField(editable=False, max_length=64, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=256)),
                ('external_id', models.CharField(default=None, max_length=256, null=True)),
                ('description', models.TextField(default=None, null=True)),
                ('content', models.TextField(default=None, null=True)),
                ('topics', systems.models.fields.DictionaryField(default=dict)),
                ('hash', models.CharField(default=None, max_length=65, null=True)),
                ('type', models.CharField(default='file', max_length=256)),
                ('sentences', systems.models.fields.ListField(default=list)),
            ],
            options={
                'verbose_name': 'team media',
                'verbose_name_plural': 'team medias',
                'db_table': 'publisher_team_media',
                'ordering': ['id'],
                'abstract': False,
            },
        ),
    ]
