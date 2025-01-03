# Generated by Django 4.1.13 on 2024-12-02 06:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('team_media_collection', '0001_initial'),
        ('team_media', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='teammedia',
            name='team_media_collection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='%(data_name)s', to='team_media_collection.teammediacollection'),
        ),
        migrations.AlterUniqueTogether(
            name='teammedia',
            unique_together={('team_media_collection', 'external_id')},
        ),
    ]
