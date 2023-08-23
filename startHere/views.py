from rest_framework.viewsets import ReadOnlyModelViewSet
from . import serializers
from .models import Category, Record, Report, Note,  TextBook
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Prefetch
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from .filters import NoteFilter
from . import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from startHere.permissions import IsSubcribed, hasActiveSubscription
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet 
from django.db.models import Q 
from .pagination import DefaultPagination
from subscription.models import Subscription
from startHere.services import filter_questions


class ReportViewSet(mixins.CreateModelMixin,GenericViewSet):
    queryset = Report.objects.all()
    serializer_class = serializers.ReportSerializer
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    
    def get_serializer_context(self):
        return {'user':self.request.user}
        
class NoteViewSet(ModelViewSet):
    pagination_class = DefaultPagination
    http_method_names = ['get', 'post', 'patch','put', 'delete', 'head', 'options']
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = NoteFilter
    permission_classes = [IsAuthenticated & hasActiveSubscription]

  
    def create(self, request, *args, **kwargs):
            try:
                # Try to fetch the object using unique fields (e.g., primary key)
                question = request.data.get('question')  # Replace 'unique_field' with your unique field name
                
                existing_object = Note.objects.get(user=request.user, question_id=question)

                # If the object already exists, update its fields with the new data
                serializer = self.get_serializer(existing_object, data=request.data)
            except Note.DoesNotExist:
                # If the object does not exist, create a new object
                serializer = self.get_serializer(data=request.data)

            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)

            return Response(serializer.data)

    def get_serializer_class(self): 
        if self.request.method == 'GET':
            return serializers.NoteSerializer
        
        return serializers.SimpleNoteSerializer

    def get_serializer_context(self):
        return {'user':self.request.user}
   
    def get_queryset(self):
        queryset = Note.objects.select_related('question').prefetch_related('question__options').prefetch_related('question__category').filter(user=self.request.user).order_by('-id')
        question_id = self.request.GET.get('question_id')
        if question_id:
            queryset = queryset.filter(question_id=question_id)
        return  queryset
            
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        question_id = self.request.GET.get('question_id')
        if question_id:
            serializer = serializers.SimpleNoteSerializer(queryset.first())
            return Response(serializer.data)
        return super().list(request, *args, **kwargs)

class CategoryViewSet(ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated & IsSubcribed]

    def get_queryset(self):
        query = self.request.query_params.get('package')
        user = self.request.user

        for sub in Subscription.objects.filter(user_id=user, package_id=query):
            if sub.has_expired():
                sub.active = False
                sub.save()

        queryset = Category.objects.select_related('parent').prefetch_related('questions', 'sub_categories__questions').prefetch_related(
            Prefetch('records', queryset=Record.objects.filter(user=user)),
            Prefetch('sub_categories__records', queryset=Record.objects.filter(user=user))
        ).filter(parent=None)

        if query:
            queryset = queryset.filter(package=query)

        return queryset

    

    def get_serializer_class(self):
        source = self.request.GET.get('source')
        if source == 'questionsbank':
            return serializers.WithRecodsSubCategoryCategroySerializer
        if source == 'timedtest':
            return serializers.SimpleCategorySerializer
        if source == 'textbook':
            return serializers.WithNestedSubCategoryCategroySerializer
                
        return serializers.SimpleCategorySerializer

class CountQuestions(APIView):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    def post(self, request, format=None):

        categories = request.data.get('categories')
        sub_categories = request.data.get('sub_categories')
        filter_criteria = request.data.get('filter_criteria')

        questions = filter_questions(
            user=self.request.user,
            filter_criteria=filter_criteria,
            categories=categories,
            sub_categories=sub_categories
        )

        print(questions)

        return Response(questions.count())

class TextBookViewSet(ReadOnlyModelViewSet):
    serializer_class = serializers.TextBookSerializer
    permission_classes = [IsAuthenticated & hasActiveSubscription]



    def get_serializer_class(self):
        query = self.request.query_params.get('query', '')
        if query:
            return serializers.TextBookSearchSerializer
        return serializers.TextBookSerializer
    
    def get_queryset(self):
        query = self.request.query_params.get('query', '')
        package = self.request.query_params.get('package')
        if query and package:
            return TextBook.objects.filter(
                Q(content__icontains=query) |
                Q(content__istartswith=query),
                package=package, 
            ).distinct()
        
        if self.kwargs.get('category_pk'):
            return TextBook.objects.filter(category_id=self.kwargs['category_pk'])


        return TextBook.objects.all()