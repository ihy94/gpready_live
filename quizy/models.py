from django.db import models
from django.conf import settings

# send package in params and filter using params also , give permission using params 

class Quiz(models.Model):
    
    subscription = models.ForeignKey('subscription.Subscription', on_delete=models.SET_NULL, related_name='subscriptionquizzes', null=True)

    user = models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                related_name='quizzes',
                verbose_name=('User'))

    quiz_name = models.CharField(
                    max_length=255,
                    help_text=("Enter the quiz name that "
                                "you want displayed"),
                    verbose_name=('Quiz name'))
    
    is_playlist = models.BooleanField(default=False)
    
    exam =  models.BooleanField(default=False, help_text=("time in seconds"))

    finished = models.BooleanField(
                    null=True,
                    blank=True)
    
    time = models.PositiveIntegerField(default=600)

    created_at = models.DateTimeField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f'{self.quiz_name}'
    

    class Meta:
        verbose_name = ("Quiz")
        verbose_name_plural = ("Quizzes")

class QuizSession(models.Model):
    question = models.ForeignKey(
                    'startHere.Question',
                    on_delete=models.CASCADE,)
    
    quiz = models.ForeignKey(
                    Quiz, 
                    on_delete=models.CASCADE, 
                    related_name='questions') 

    
    class Meta:
        unique_together = [['question', 'quiz']]

class Progress(models.Model):
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE)
    data = models.JSONField(null=True)
    
class Result(models.Model):
    quiz = models.OneToOneField(Quiz, on_delete=models.CASCADE)
    correct_answers_count = models.PositiveIntegerField(default=0)
    wrong_answers_count = models.PositiveIntegerField(default=0)
    not_answered_count = models.PositiveIntegerField(default=0)
    time_spent = models.PositiveIntegerField(default=0)
    percentage = models.PositiveIntegerField(default=0)

class Answer(models.Model):
    
    user = models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                verbose_name=('User'))

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)

    question = models.ForeignKey('startHere.Question', on_delete=models.CASCADE)
    
    is_correct = models.BooleanField(null=True, default=None)
    
    created_at = models.DateTimeField(auto_now=True)

    exam = models.BooleanField(default=False)






