# Django
from django.shortcuts import get_object_or_404

# DRF
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from rest_framework import mixins
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

# files 
from .models import Progress, Quiz, Result, Answer
from startHere.models import Record
from quizy import serializers
from quizy.signals import answer_saved
from .pagination import DefaultPagination

from quizy.permissions import IsSubcribed, hasActiveSubscription

from django.conf import settings

# Third party 
from django_filters.rest_framework import DjangoFilterBackend


class PlaylistViewSet(ModelViewSet):
    pagination_class = DefaultPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']    
    serializer_class = serializers.SimplePlaylistSerializer
    # permission_classes = [IsAuthenticated & IsSubcribed]
    

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('subscription')

        queryset = Quiz.objects.prefetch_related('questions').filter(user=user.id, is_playlist=True, exam=False).order_by('-created_at')
        if query:
            queryset = queryset.filter(subscription_id=query)
        return queryset


    def get_serializer_context(self):
        return {
            "user_id" : self.request.user.id,
        }
    
class QuizViewSet(ModelViewSet):
    pagination_class = DefaultPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']    
    filter_backends = [DjangoFilterBackend, SearchFilter]
    # permission_classes = [IsAuthenticated & IsSubcribed]
   

    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateQuizSerializer(
            data=request.data,
            context={'user': self.request.user})
        serializer.is_valid(raise_exception=True)
        quiz = serializer.save()
        serializer = serializers.SimpleQuizSerializer(quiz)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateQuizSerializer

        return serializers.SimpleQuizSerializer
        
    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('subscription')
        queryset = Quiz.objects.prefetch_related('questions').filter(user=user.id, is_playlist=False, exam=True).order_by('-updated_at')
        if query:
            queryset = queryset.filter(subscription_id=query)
        return queryset

class QuestionSessionViewSet(ModelViewSet):
    pagination_class = DefaultPagination
    http_method_names = ['get', 'post', 'patch', 'delete', 'head', 'options']    
    filter_backends = [DjangoFilterBackend, SearchFilter]
    permission_classes = [IsAuthenticated & IsSubcribed]

    def create(self, request, *args, **kwargs):
        serializer = serializers.CreateQuestionSessionSerializer(
            data=request.data,
            context={'user': self.request.user})
        serializer.is_valid(raise_exception=True)
        question_session = serializer.save()
        serializer = serializers.SimpleQuizSerializer(question_session)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.CreateQuestionSessionSerializer

        return serializers.SimpleQuizSerializer
    

    def get_queryset(self):
        user = self.request.user
        query = self.request.query_params.get('subscription')
        queryset = Quiz.objects.prefetch_related('questions').filter(user=user.id, is_playlist=False, exam=False).order_by('-updated_at')
        if query:
            queryset = queryset.filter(subscription_id=query)
        return queryset

class UpdateProgress(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def post(self, request, format=None):
        progress =  get_object_or_404(Progress,quiz_id=request.data['quiz_id'])
        serializer = serializers.ProgressSerializer(progress, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class GetProgress(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def get(self, request, pk, format=None):
        progress, _ = Progress.objects.get_or_create(quiz_id=pk)
        serializer = serializers.ProgressSerializer(progress)
        return Response(serializer.data)

class Results(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def get(self, request, pk, *args, **kwargs):
        answers = Answer.objects.filter(quiz_id=pk)
        quiz = Quiz.objects.get(id=pk)
        correct_answers = answers.filter(is_correct=True)
        wrong_answers = answers.filter(is_correct=False)

        result = Result (
            quiz = quiz,
            correct_answers_count = correct_answers.count(),
            wrong_answers_count =  wrong_answers.count(),
            not_answered_count =  0,
            percentage = 0,
        )

        serializer = serializers.ResultSerializer(result)

        return Response(serializer.data)

class UpdatePlaylist(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def post(self, request, format=None):
        serializer = serializers.UpdatePlaylistSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GetQuizDetailViewSet(mixins.RetrieveModelMixin, GenericViewSet):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    queryset = Quiz.objects.all()
    serializer_class = serializers.QuizDetailSerializer


    def get_queryset(self):
        return Quiz.objects.filter(user_id=self.request.user.id)

class CreateOrUpdateAnswer(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def post(self, request):
        self.request.data['user'] = request.user.id
        try:
            answer = Answer.objects.get(
                user_id= request.data['user'],
                quiz_id=self.request.data['quiz'],
                question_id=self.request.data['question']
            )
            serializer = serializers.AnswerSerializer(answer, data=request.data)
            
            if serializer.is_valid():
                answer = serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Answer.DoesNotExist:
            serializer = serializers.AnswerSerializer(data=request.data)

            if serializer.is_valid():
                answer = serializer.save()

                if not answer.exam:
                    answer_saved.send(
                        sender=self.__class__,
                        answer=answer,
                        created=True,
                        option_id=self.request.data['option_id']
                    )

                return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
  
class BulkMultipleAnswers(APIView):
    def post(self, request):
        serializer = serializers.CreateAnswersSerializer(
            data=request.data,
            context={'user': self.request.user})
            
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
    

class ResetHistory(APIView):
    def post(self, request):
        quizzes = Quiz.objects.filter(user=request.user) 
        records = Record.objects.filter(user=request.user)
        quizzes.delete()
        records.delete()
        return Response({"msg":"history reset"}, status=status.HTTP_200_OK)