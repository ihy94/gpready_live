# Additive AKT textbook tables. Existing Category and TextBook rows are untouched.
import ckeditor_uploader.fields
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('startHere', '0003_alter_questionimage_src'),
        ('subscription', '0003_remove_package_is_demo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AKTTextbookChapter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('chapter_id', models.SlugField(help_text='Stable import ID, for example cardio-hypertension-diagnosis.', max_length=180, unique=True)),
                ('curriculum_area', models.CharField(max_length=180)),
                ('topic', models.CharField(max_length=220)),
                ('curriculum_outcomes', models.TextField(blank=True)),
                ('title', models.CharField(max_length=255)),
                ('position', models.PositiveIntegerField(default=0)),
                ('content', ckeditor_uploader.fields.RichTextUploadingField()),
                ('sources', models.TextField(blank=True)),
                ('is_published', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('package', models.ManyToManyField(blank=True, related_name='akt_textbook_chapters', to='subscription.package')),
            ],
            options={
                'ordering': ['curriculum_area', 'topic', 'position', 'title'],
                'indexes': [models.Index(fields=['curriculum_area', 'topic', 'position'], name='startHere_akt_area_topic_idx')],
            },
        ),
        migrations.CreateModel(
            name='AKTTextbookProgress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_complete', models.BooleanField(default=False)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
                ('chapter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='progress_entries', to='startHere.akttextbookchapter')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='akt_textbook_progress', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='akttextbookprogress',
            constraint=models.UniqueConstraint(fields=('user', 'chapter'), name='unique_akt_chapter_progress'),
        ),
    ]
