from .models import Category, Question
from django.db.models import Q 

def filter_questions(user, filter_criteria, categories, sub_categories):
    children_categories_ids = Category.objects.filter(parent_id__in=categories).values_list('id', flat=True)
        
    qs1  = Question.objects.filter(category_id__in=children_categories_ids) | Question.objects.filter(category_id__in=categories) 

    qs2 = Question.objects.filter(category_id__in=sub_categories)

    questions = (qs1 | qs2).distinct()

    if filter_criteria == 'marked_wrong_questions':
        questions = questions.prefetch_related('answer_set').only('id')
        questions = questions.filter(answer__exam=False, answer__user=user,answer__is_correct=False).distinct()
            

    if filter_criteria == 'only_new_questions':
        questions = questions.prefetch_related('answer_set').only('id')
        correct_false_questions = (questions.filter(answer__exam=False, answer__user=user,answer__is_correct=False) | (questions.filter(answer__exam=False, answer__user=user,answer__is_correct=True))).distinct()
        questions = questions.filter(~Q(id__in=correct_false_questions))


    return questions