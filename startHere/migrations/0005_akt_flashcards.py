# Additive AKT flashcard tables; existing question and textbook data is untouched.
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('startHere', '0004_akt_textbook_chapters'),
        ('subscription', '0003_remove_package_is_demo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AKTFlashcard',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('card_id', models.SlugField(max_length=180, unique=True)),
                ('deck', models.CharField(max_length=180)),
                ('topic', models.CharField(max_length=220)),
                ('front', models.TextField()),
                ('clue', models.TextField(blank=True)),
                ('answer', models.TextField()),
                ('learning_point', models.TextField(blank=True)),
                ('source', models.TextField(blank=True)),
                ('tags', models.CharField(blank=True, max_length=500)),
                ('difficulty', models.CharField(choices=[('Foundation', 'Foundation'), ('Intermediate', 'Intermediate'), ('Advanced', 'Advanced')], default='Intermediate', max_length=20)),
                ('status', models.CharField(choices=[('Draft', 'Draft'), ('Reviewed', 'Reviewed'), ('Published', 'Published')], default='Draft', max_length=12)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('package', models.ManyToManyField(blank=True, related_name='akt_flashcards', to='subscription.package')),
            ],
            options={
                'ordering': ['deck', 'topic', 'card_id'],
                'indexes': [models.Index(fields=['deck', 'topic'], name='startHere_akt_deck_topic_idx')],
            },
        ),
        migrations.CreateModel(
            name='AKTFlashcardReview',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('due_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('interval_days', models.PositiveIntegerField(default=0)),
                ('repetitions', models.PositiveIntegerField(default=0)),
                ('lapses', models.PositiveIntegerField(default=0)),
                ('last_rating', models.CharField(blank=True, choices=[('again', 'Again'), ('hard', 'Hard'), ('good', 'Good'), ('easy', 'Easy')], max_length=8)),
                ('last_reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('is_bookmarked', models.BooleanField(default=False)),
                ('card', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='review_states', to='startHere.aktflashcard')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='akt_flashcard_reviews', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='aktflashcardreview',
            constraint=models.UniqueConstraint(fields=('user', 'card'), name='unique_akt_flashcard_review'),
        ),
        migrations.AddIndex(
            model_name='aktflashcardreview',
            index=models.Index(fields=['user', 'due_at'], name='startHere_akt_user_due_idx'),
        ),
    ]
