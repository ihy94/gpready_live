from django.contrib import admin
from quizy.models import Quiz, Answer, Progress, QuizSession

admin.site.register(Quiz)
admin.site.register(Answer)
admin.site.register(Progress)
admin.site.register(QuizSession)

