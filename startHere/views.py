from rest_framework.viewsets import ReadOnlyModelViewSet
from . import serializers
from .models import AKTTextbookChapter, AKTTextbookProgress, Category, Record, Report, Note, TextBook
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import Exists, OuterRef, Prefetch
from django.utils import timezone
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


class AKTTextbookChapterViewSet(ReadOnlyModelViewSet):
    """Published AKT chapters; the existing TextBook routes are left intact."""

    serializer_class = serializers.AKTTextbookChapterSerializer
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    lookup_field = 'chapter_id'

    def get_serializer_class(self):
        if self.action == 'list':
            return serializers.AKTTextbookChapterListSerializer
        return serializers.AKTTextbookChapterSerializer

    def get_queryset(self):
        active_package_ids = self.request.user.subscriptions.filter(
            active=True,
            expiry_date__gt=timezone.now(),
        ).values_list('package_id', flat=True)
        queryset = AKTTextbookChapter.objects.filter(
            is_published=True,
            package__in=active_package_ids,
        ).annotate(
            is_complete=Exists(
                AKTTextbookProgress.objects.filter(
                    chapter_id=OuterRef('pk'),
                    user=self.request.user,
                    is_complete=True,
                )
            )
        )

        selected_package = self.request.query_params.get('package')
        if selected_package:
            queryset = queryset.filter(package__id=selected_package)

        return queryset.distinct()

    @action(detail=True, methods=['post'], url_path='progress')
    def update_progress(self, request, chapter_id=None):
        chapter = self.get_object()
        is_complete = request.data.get('is_complete')
        if not isinstance(is_complete, bool):
            return Response(
                {'detail': 'is_complete must be true or false.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        progress, _ = AKTTextbookProgress.objects.update_or_create(
            user=request.user,
            chapter=chapter,
            defaults={
                'is_complete': is_complete,
                'completed_at': timezone.now() if is_complete else None,
            },
        )
        return Response({
            'chapter_id': chapter.chapter_id,
            'is_complete': progress.is_complete,
            'completed_at': progress.completed_at,
        })
