# Additive per-user SCA case progress; existing textbook HTML remains untouched.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('startHere', '0005_akt_flashcards'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SCATextbookProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_complete', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('textbook', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sca_progress_entries',
                    to='startHere.textbook',
                )),
                ('user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sca_textbook_progress',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
        ),
        migrations.AddConstraint(
            model_name='scatextbookprogress',
            constraint=models.UniqueConstraint(
                fields=('user', 'textbook'),
                name='unique_sca_textbook_progress',
            ),
        ),
    ]
