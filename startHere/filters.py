from django_filters.rest_framework import FilterSet
from quizy.models import Quiz
from .models import Note

class NoteFilter(FilterSet):
  class Meta:
    model = Note
    fields = {
      'question_id': ['exact'],
    }
  
  
