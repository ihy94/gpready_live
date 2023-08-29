from rest_framework import serializers
from django.db import transaction
from startHere.serializers import  QuestionSerializer
from .models import Answer, Progress, Quiz, Result, QuizSession
from startHere.models import Question, Category
from django.core.paginator import Paginator
from urllib.parse import urlencode, urlparse, parse_qs
from django.db.models import Q 
from startHere.services import filter_questions

# timed test serializer

# QUIZ MODEL SERIALIZERS 

class QuizSessionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()
    class Meta:
        model = QuizSession
        fields = ['question']    

class SimpleQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'quiz_name', 'time', 'finished', 'created_at', 'updated_at']
        
class SimplePlaylistSerializer(serializers.ModelSerializer):
    questions_ids = serializers.SerializerMethodField(method_name='get_questions_ids')
    questions_count = serializers.SerializerMethodField(method_name='count_questions')

    class Meta:
        model = Quiz
        fields = ['id', 'subscription', 'quiz_name', 'created_at','updated_at','questions_ids','questions_count']

    def count_questions(self, quiz):
        return quiz.questions.count()
    
    def get_questions_ids(self, quiz):
        return  [item.question.id for item in quiz.questions.all()]
      
    def create(self, validated_data):
        return Quiz.objects.create(user_id=self.context['user_id'],is_playlist=True, **validated_data)
 
class QuizDetailSerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField('paginated_questions')
    questions_count = serializers.SerializerMethodField(method_name='count_questions')
    class Meta:
        model = Quiz
        fields = ['id', 'quiz_name', 'created_at', 'updated_at', 'questions_count', 'time', 'finished', 'questions']
    
    def count_questions(self, quiz):
        return quiz.questions.count()
    
    def paginated_questions(self, obj):
        page_size = self.context['request'].query_params.get('size') or 10
        paginator = Paginator(obj.questions.
            prefetch_related('question__options').prefetch_related('question__notes').prefetch_related('question__images').order_by('id'), page_size)
        page_number = self.context['request'].query_params.get('page') or 1
        questions = paginator.page(page_number)
        serializer = QuizSessionSerializer(questions, many=True)

        return {
            'count': paginator.count,
            'per_page' : page_size,
            'next': self.get_next_link(questions),
            'previous': self.get_previous_link(questions),
            'results': serializer.data,
        }

    def get_next_link(self, questions):
        if questions.has_next():
            page_number = questions.next_page_number()
            request = self.context.get('request')
            if request is not None:
                url = request.build_absolute_uri()
                url = self._replace_page_param(url, page_number)
                return url
        return None

    def get_previous_link(self, questions):
        if questions.has_previous():
            page_number = questions.previous_page_number()
            request = self.context.get('request')
            if request is not None:
                url = request.build_absolute_uri()
                url = self._replace_page_param(url, page_number)
                return url
        return None

    def _replace_page_param(self, url, page_number):
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        query_params['page'] = [str(page_number)]
        updated_query_string = urlencode(query_params, doseq=True)
        updated_url = parsed_url._replace(query=updated_query_string).geturl()
        return updated_url

class CreateQuizSerializer(serializers.Serializer):
    
    quiz_name = serializers.CharField()
    
    limit = serializers.IntegerField()

    time = serializers.IntegerField()
    
    subscription = serializers.IntegerField()

    category = serializers.IntegerField()
    
    def save(self, **kwargs):

        quiz_name = self.validated_data['quiz_name']

        limit = self.validated_data['limit']

        category = self.validated_data['category']
        
        subscription = self.validated_data['subscription']

        time = self.validated_data['time']
                                        
        children_categories_ids = Category.objects.filter(parent_id=category).values_list('id', flat=True)

        questions = (Question.objects.filter(category_id__in=children_categories_ids) | Question.objects.filter(category_id=category)).distinct().order_by('?') 



        if limit is not None:
            questions = questions.all()[:limit]


        with transaction.atomic():
            quiz = Quiz.objects.create(subscription_id=subscription ,quiz_name=quiz_name, user=self.context['user'], time=time*60, exam=True)
            quiz_session_items = [
            QuizSession(
                quiz=quiz,
                question = item
            ) for item in questions
            ]       
            QuizSession.objects.bulk_create(quiz_session_items)
            return quiz

class CreateQuestionSessionSerializer(serializers.Serializer):
    
    quiz_name = serializers.CharField()
        
    categories = serializers.ListField(child=serializers.CharField())

    sub_categories = serializers.ListField(child=serializers.CharField())

    subscription = serializers.IntegerField()

    filter_criteria = serializers.CharField()
    
    def save(self, **kwargs):

        filter_criteria = self.validated_data['filter_criteria']

        subscription = self.validated_data['subscription']

        quiz_name = self.validated_data['quiz_name']

        categories = self.validated_data['categories']

        sub_categories = self.validated_data['sub_categories']

        questions = filter_questions(
            user=self.context['user'],
            filter_criteria=filter_criteria,
            categories=categories,
            sub_categories=sub_categories
        )

        questions = questions.order_by('?') 
        
        with transaction.atomic():
            question_session = Quiz.objects.create(subscription_id=subscription , quiz_name=quiz_name,user=self.context['user'])
            question_session_items = [
            QuizSession(
                quiz=question_session,
                question = question
            ) for question in questions
            ]       
            QuizSession.objects.bulk_create(question_session_items)
            return question_session


# # # # # # # # # # # # ## # # # # # # # # # ## # # # # # # #  # #  #  # # # # # # # # # # # # # #  # # # # # # #

class ProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Progress
        fields = ['id','quiz_id','data']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = '__all__'
        
class ResultSerializer(serializers.ModelSerializer):
    quiz_name = serializers.SerializerMethodField(method_name='get_quiz_name')
    questions_count = serializers.SerializerMethodField(method_name='count_questions')

    def get_quiz_name(self, result):
        return result.quiz.quiz_name

    def count_questions(self, result):
        return result.quiz.questions.count()


    class Meta:
        model = Result
        fields = ['id', 'correct_answers_count','wrong_answers_count','not_answered_count','percentage','quiz_name','questions_count']

class UpdatePlaylistSerializer(serializers.Serializer):
 
    question_id = serializers.IntegerField()

    to_add = serializers.ListField(child=serializers.CharField())
    
    to_remove = serializers.ListField(child=serializers.CharField())

    def save(self, **kwargs):
        to_add = self.validated_data['to_add']
        question_id = self.validated_data['question_id']
        to_remove = self.validated_data['to_remove']
        
        if len(to_remove) > 0:
            QuizSession.objects.filter(question_id = question_id, quiz_id__in=to_remove).delete()
            
        playlists = Quiz.objects.filter(id__in=to_add)
        
        quiz_session_items = [
        QuizSession(
            quiz=item,
            question_id = question_id
        ) for item in playlists
        ]       
        QuizSession.objects.bulk_create(quiz_session_items)
               

class CreateAnswersSerializer(serializers.Serializer):
    
    quiz = serializers.IntegerField()
    questions_ids = serializers.ListField(child=serializers.CharField())
    answers = serializers.JSONField()
    
    def save(self, **kwargs):
        quiz = self.validated_data['quiz']
        questions_ids = self.validated_data['questions_ids']
        answers = self.validated_data['answers']
                
        answers_list = []
        for question_id in questions_ids:
            answers_list.append(
                Answer(
                    user=self.context['user'],
                    quiz_id=quiz,
                    question_id=question_id,
                    is_correct=answers[question_id]['is_correct'],
                    exam=True
                )     
            )
                 
        if len(answers_list) > 0:  
            with transaction.atomic():     
                Answer.objects.bulk_create(answers_list)

        return {"msg" : 'bulked'}
   
