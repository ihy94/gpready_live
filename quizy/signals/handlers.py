from django.db.models.signals import post_save
from django.dispatch import receiver
from quizy.models import Progress, Quiz
from startHere.models import Record, Option
from quizy.signals import answer_saved
from django.shortcuts import get_object_or_404


@receiver(post_save, sender=Quiz)
def create_progress_for_quiz(sender, **kwargs):
    if kwargs['created']:
        Progress.objects.create(quiz=kwargs['instance'],data=None)


@receiver(answer_saved)
def update_record_by_question_answer(sender, answer, **kwargs):
    category = answer.question.category
    user = answer.user
    
    if kwargs['created']:
        op = get_object_or_404(Option, id=kwargs['option_id']) 
        op.user_select_count += 1
        op.save()
        update_record(category, user, answer)
       
                
def update_record(category, user, answer):
    record, _ = Record.objects.get_or_create(category=category, user=user)      
    if answer.is_correct:
        record.correct_answers += 1    
    else:
        record.wrong_answers += 1
        
    record.save()
        
        
    if category.parent:
        record, _ = Record.objects.get_or_create(category=category.parent, user=user)
        update_record(category.parent, user, answer)
            