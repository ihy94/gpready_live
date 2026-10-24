from django.db import models
from django.conf import settings
from django.utils import timezone
from ckeditor_uploader.fields import RichTextUploadingField
from cloudinary.models import CloudinaryField


class Category(models.Model):

    package = models.ManyToManyField('subscription.Package', related_name='categories')
    
    title = models.CharField(max_length=255)

    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name='sub_categories')

    is_demo = models.BooleanField(default=False)

    def __unicode__(self):  
        return str(self.title)

    def __str__(self):
        return str(self.title)

        
    def children(self): #replies
        return Category.objects.filter(parent=self)
    

    @property
    def questions_count(self):
        return self.questions.count()

    @property
    def is_parent(self):
        if self.parent is not None:
            return False
        return True

class Question(models.Model):

    category = models.ForeignKey(
                        Category,
                        on_delete=models.CASCADE,
                        related_name='questions')

    content = models.TextField(
                        max_length=1600,
                        blank=False,
                        help_text=("Enter the question text that "
                                    "you want displayed"),
                        verbose_name=('Question'))
    
    explanation = models.TextField(
                        default='',
                        max_length=2000,
                        null=True,
                        blank=True,
                        help_text=("Explanation to be shown "
                                    "after the question has "
                                    "been answered."),
                        verbose_name=('Explanation'))
    
    class Meta:
        verbose_name = ("Question")
        verbose_name_plural = ("Questions")
       
         
    def __str__(self):
        return self.content
    
class Option(models.Model):

    question = models.ForeignKey(
        Question, 
        verbose_name=("Question"), 
        on_delete=models.CASCADE,
        related_name='options'
        )

    content = models.TextField(
        max_length=6000,
        blank=False,
        help_text=("Enter the answer text that "
                        "you want displayed"),
        verbose_name=("Content"))

    is_correct = models.BooleanField(
        default=False,
        help_text=("Is this a correct answer?"),
        verbose_name=("Correct"))


    user_select_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.content

    class Meta:
        verbose_name = ("Option")
        verbose_name_plural = ("Options")

class QuestionImage(models.Model): 
    
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name='images')

    title = models.TextField(
                        max_length=255,
                        blank=True,
                        null=True,
                        help_text=("Enter the title that "
                                    "you want displayed"),
                        verbose_name=('Question Image'))
    
    # src = models.ImageField(upload_to ='question_images/')
    src = CloudinaryField('image')

class Record(models.Model): 
    category = models.ForeignKey(
        Category, 
        verbose_name=("User Record Per Category"), 
        null=True,
        on_delete=models.SET_NULL,
        related_name='records'
    )    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name=('User'))
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = [['category', 'user']]

class Report(models.Model):
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


    question = models.ForeignKey(
                        Question,
                        on_delete=models.CASCADE,
                        related_name='reports'
                        )

    comment = models.TextField(
                        max_length=2000,
                       verbose_name=('Comment'))

class Note(models.Model):
    question = models.ForeignKey(Question, on_delete=models.SET_NULL, null=True, related_name='notes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField(max_length=3000)
    created_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.content
    

    class Meta:
        unique_together = [['question', 'user']]

class TextBook(models.Model):

    title = models.CharField(max_length=255)

    package = models.ManyToManyField('subscription.Package', related_name='textbooks')

    category = models.OneToOneField(
                        Category,
                        on_delete=models.CASCADE,
                        related_name='textbooks')
    

    content =  RichTextUploadingField()

    created_at = models.DateField(auto_now_add=True)
    
    updated_at = models.DateField(auto_now=True)


    def __str__(self) -> str:
        return self.category.title


class SCATextbookProgress(models.Model):
    """Per-learner completion state for an existing SCA textbook case."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sca_textbook_progress',
    )
    textbook = models.ForeignKey(
        TextBook,
        on_delete=models.CASCADE,
        related_name='sca_progress_entries',
    )
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'textbook'], name='unique_sca_textbook_progress'),
        ]

    def __str__(self):
        state = 'complete' if self.is_complete else 'in progress'
        return f'{self.user} — {self.textbook} — {state}'


class AKTTextbookChapter(models.Model):
    """Curriculum-mapped AKT chapters, kept separate from the existing textbook."""

    chapter_id = models.SlugField(
        max_length=180,
        unique=True,
        help_text="Stable import ID, for example cardio-hypertension-diagnosis.",
    )
    curriculum_area = models.CharField(max_length=180)
    topic = models.CharField(max_length=220)
    curriculum_outcomes = models.TextField(blank=True)
    title = models.CharField(max_length=255)
    position = models.PositiveIntegerField(default=0)
    content = RichTextUploadingField()
    sources = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    package = models.ManyToManyField(
        'subscription.Package',
        related_name='akt_textbook_chapters',
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['curriculum_area', 'topic', 'position', 'title']
        indexes = [
            models.Index(fields=['curriculum_area', 'topic', 'position']),
        ]

    def __str__(self):
        return f'{self.curriculum_area} — {self.title}'


class AKTTextbookProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='akt_textbook_progress',
    )
    chapter = models.ForeignKey(
        AKTTextbookChapter,
        on_delete=models.CASCADE,
        related_name='progress_entries',
    )
    is_complete = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'chapter'], name='unique_akt_chapter_progress'),
        ]

    def __str__(self):
        return f'{self.user} — {self.chapter} — {"complete" if self.is_complete else "in progress"}'


class AKTFlashcard(models.Model):
    """Shared AKT flashcard content, independent of learner review history."""

    DIFFICULTY_CHOICES = [
        ('Foundation', 'Foundation'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
    ]
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Reviewed', 'Reviewed'),
        ('Published', 'Published'),
    ]

    card_id = models.SlugField(max_length=180, unique=True)
    deck = models.CharField(max_length=180)
    topic = models.CharField(max_length=220)
    front = models.TextField()
    clue = models.TextField(blank=True)
    answer = models.TextField()
    learning_point = models.TextField(blank=True)
    source = models.TextField(blank=True)
    tags = models.CharField(max_length=500, blank=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='Intermediate')
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='Draft')
    package = models.ManyToManyField(
        'subscription.Package', related_name='akt_flashcards', blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['deck', 'topic', 'card_id']
        indexes = [models.Index(fields=['deck', 'topic'], name='startHere_akt_deck_topic_idx')]

    def __str__(self):
        return f'{self.deck} — {self.topic}: {self.card_id}'


class AKTFlashcardReview(models.Model):
    """Per-user scheduling and saved state for one shared flashcard."""

    RATING_CHOICES = [
        ('again', 'Again'),
        ('hard', 'Hard'),
        ('good', 'Good'),
        ('easy', 'Easy'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='akt_flashcard_reviews',
    )
    card = models.ForeignKey(
        AKTFlashcard, on_delete=models.CASCADE, related_name='review_states',
    )
    due_at = models.DateTimeField(default=timezone.now)
    interval_days = models.PositiveIntegerField(default=0)
    repetitions = models.PositiveIntegerField(default=0)
    lapses = models.PositiveIntegerField(default=0)
    last_rating = models.CharField(max_length=8, choices=RATING_CHOICES, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    is_bookmarked = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'card'], name='unique_akt_flashcard_review'),
        ]
        indexes = [models.Index(fields=['user', 'due_at'], name='startHere_akt_user_due_idx')]

    def __str__(self):
        return f'{self.user} — {self.card.card_id}'
        
