from rest_framework.viewsets import ReadOnlyModelViewSet
from . import serializers
from .models import AKTFlashcard, AKTFlashcardReview, AKTTextbookChapter, AKTTextbookProgress, SCATextbookProgress, Category, Record, Report, Note, TextBook
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import Exists, OuterRef, Prefetch, Sum
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet, GenericViewSet
from .filters import NoteFilter
from . import serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from startHere.permissions import HasActivePackageSubscription, IsSubcribed, hasActiveSubscription
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet 
from django.db.models import Q 
from .pagination import DefaultPagination
from subscription.models import Subscription
from startHere.services import filter_questions
from datetime import timedelta
from math import ceil


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


class ScoreComparisonView(APIView):
    """Return anonymous package-level score aggregates for the current learner."""

    permission_classes = [IsAuthenticated & IsSubcribed]
    minimum_attempts = 20
    minimum_peers = 30

    def get(self, request, format=None):
        package = request.query_params.get('package')
        try:
            package_id = int(package)
            if package_id < 1:
                raise ValueError
        except (TypeError, ValueError):
            return Response({'detail': 'A valid package is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Category.package is a many-to-many field, so filter through package__id.
        category_ids = list(
            Category.objects.filter(parent__isnull=True, package__id=package_id)
            .values_list('id', flat=True)
        )
        if not category_ids:
            return Response({
                'available': False,
                'reason': 'no_categories',
                'attempts': 0,
                'accuracy': None,
            })

        own = Record.objects.filter(
            user_id=request.user.id,
            category_id__in=category_ids,
        ).aggregate(correct=Sum('correct_answers'), wrong=Sum('wrong_answers'))
        correct = own['correct'] or 0
        wrong = own['wrong'] or 0
        attempts = correct + wrong
        accuracy = round((correct / attempts) * 100) if attempts else None

        if attempts < self.minimum_attempts:
            return Response({
                'available': False,
                'reason': 'minimum_attempts',
                'minimum_attempts': self.minimum_attempts,
                'attempts': attempts,
                'accuracy': accuracy,
            })

        other_records = (
            Record.objects.filter(category_id__in=category_ids)
            .exclude(user_id=request.user.id)
            .values('user_id')
            .annotate(correct=Sum('correct_answers'), wrong=Sum('wrong_answers'))
        )
        peer_scores = []
        for record in other_records.iterator():
            peer_correct = record['correct'] or 0
            peer_attempts = peer_correct + (record['wrong'] or 0)
            if peer_attempts >= self.minimum_attempts:
                peer_scores.append(round(peer_correct / peer_attempts * 100))

        # Suppress the comparison until the cohort is large enough for privacy.
        if len(peer_scores) < self.minimum_peers:
            return Response({
                'available': False,
                'reason': 'small_cohort',
                'attempts': attempts,
                'accuracy': accuracy,
            })

        histogram = [0] * 10
        for score in peer_scores:
            histogram[min(score // 10, 9)] += 1

        below = sum(score < accuracy for score in peer_scores)
        equal = sum(score == accuracy for score in peer_scores)
        percentile = round(((below + equal / 2) / len(peer_scores)) * 100)

        return Response({
            'available': True,
            'attempts': attempts,
            'accuracy': accuracy,
            'cohort_size': len(peer_scores),
            'cohort_average': round(sum(peer_scores) / len(peer_scores)),
            'percentile': percentile,
            'histogram': histogram,
        })

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
        queryset = TextBook.objects.all()

        if package:
            queryset = queryset.filter(package__id=package)

        if query:
            queryset = queryset.filter(
                Q(content__icontains=query) |
                Q(content__istartswith=query)
            )
        
        if self.kwargs.get('category_pk'):
            queryset = queryset.filter(category_id=self.kwargs['category_pk'])

        return queryset.annotate(
            is_complete=Exists(
                SCATextbookProgress.objects.filter(
                    textbook_id=OuterRef('pk'),
                    user=self.request.user,
                    is_complete=True,
                )
            )
        ).distinct()

    def _valid_package_access(self, package_id):
        try:
            package_id = int(package_id)
            if package_id < 1:
                return False
        except (TypeError, ValueError):
            return False

        return self.request.user.subscriptions.filter(
            package_id=package_id,
            active=True,
            expiry_date__gt=timezone.now(),
        ).exists()

    @action(detail=False, methods=['get'], url_path='progress')
    def progress_summary(self, request):
        package_id = request.query_params.get('package')
        if not self._valid_package_access(package_id):
            return Response({'detail': 'A valid active package is required.'}, status=status.HTTP_403_FORBIDDEN)

        cases = TextBook.objects.filter(package__id=package_id).annotate(
            is_complete=Exists(
                SCATextbookProgress.objects.filter(
                    textbook_id=OuterRef('pk'),
                    user=request.user,
                    is_complete=True,
                )
            )
        ).distinct()
        completed_ids = list(cases.filter(is_complete=True).values_list('id', flat=True))
        return Response({
            'total_cases': cases.count(),
            'completed_cases': len(completed_ids),
            'completed_textbook_ids': completed_ids,
        })

    @action(detail=True, methods=['post'], url_path='progress')
    def update_progress(self, request, pk=None):
        package_id = request.query_params.get('package')
        if not self._valid_package_access(package_id):
            return Response({'detail': 'A valid active package is required.'}, status=status.HTTP_403_FORBIDDEN)

        textbook = self.get_object()
        if not textbook.package.filter(id=package_id).exists():
            return Response({'detail': 'This case is not part of the selected package.'}, status=status.HTTP_404_NOT_FOUND)

        is_complete = request.data.get('is_complete')
        if not isinstance(is_complete, bool):
            return Response({'detail': 'is_complete must be true or false.'}, status=status.HTTP_400_BAD_REQUEST)

        progress, _ = SCATextbookProgress.objects.update_or_create(
            user=request.user,
            textbook=textbook,
            defaults={
                'is_complete': is_complete,
                'completed_at': timezone.now() if is_complete else None,
            },
        )
        return Response({
            'textbook_id': textbook.id,
            'category_id': textbook.category_id,
            'is_complete': progress.is_complete,
            'completed_at': progress.completed_at,
        })


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


class AKTFlashcardViewSet(ReadOnlyModelViewSet):
    """Published cards for an active package, with private user scheduling."""

    serializer_class = serializers.AKTFlashcardSerializer
    permission_classes = [IsAuthenticated, HasActivePackageSubscription]
    lookup_field = 'card_id'

    def _base_queryset(self):
        return AKTFlashcard.objects.filter(
            status='Published',
            package__id=getattr(self, 'package_id', self.request.query_params.get('package')),
        ).distinct()

    def get_queryset(self):
        queryset = self._base_queryset()
        mode = self.request.query_params.get('mode', 'all')
        user = self.request.user
        now = timezone.now()
        if mode == 'due':
            user_review = AKTFlashcardReview.objects.filter(user=user, card_id=OuterRef('pk'))
            due_review = user_review.filter(Q(last_reviewed_at__isnull=True) | Q(due_at__lte=now))
            return queryset.annotate(
                has_user_review=Exists(user_review),
                has_due_review=Exists(due_review),
            ).filter(Q(has_user_review=False) | Q(has_due_review=True))
        if mode == 'saved':
            return queryset.filter(review_states__user=user, review_states__is_bookmarked=True).distinct()
        if mode != 'all':
            return queryset.none()
        return queryset

    @action(detail=False, methods=['get'])
    def summary(self, request):
        cards = self._base_queryset()
        now = timezone.now()
        user_review = AKTFlashcardReview.objects.filter(user=request.user, card_id=OuterRef('pk'))
        reviewed_state = user_review.filter(last_reviewed_at__isnull=False)
        due_review = user_review.filter(Q(last_reviewed_at__isnull=True) | Q(due_at__lte=now))
        saved_review = user_review.filter(is_bookmarked=True)
        return Response({
            'total_count': cards.count(),
            'new_count': cards.annotate(has_reviewed=Exists(reviewed_state)).filter(has_reviewed=False).count(),
            'due_count': cards.annotate(
                has_user_review=Exists(user_review),
                has_due_review=Exists(due_review),
            ).filter(Q(has_user_review=False) | Q(has_due_review=True)).count(),
            'saved_count': cards.annotate(has_saved_review=Exists(saved_review)).filter(has_saved_review=True).count(),
        })

    @action(detail=True, methods=['post'])
    def review(self, request, card_id=None):
        card = self.get_object()
        rating = str(request.data.get('rating', '')).lower()
        if rating not in {'again', 'hard', 'good', 'easy'}:
            return Response(
                {'detail': 'rating must be again, hard, good or easy.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        review, _ = AKTFlashcardReview.objects.get_or_create(user=request.user, card=card)
        previous_interval = review.interval_days
        now = timezone.now()
        if rating == 'again':
            review.due_at = now + timedelta(minutes=10)
            review.interval_days = 0
            review.repetitions = 0
            review.lapses += 1
        else:
            if rating == 'hard':
                interval = max(1, ceil(previous_interval * 1.2)) if previous_interval else 1
            elif rating == 'good':
                interval = max(3, ceil(previous_interval * 2.5)) if previous_interval else 3
            else:
                interval = max(7, ceil(previous_interval * 3.5)) if previous_interval else 7
            review.interval_days = interval
            review.due_at = now + timedelta(days=interval)
            review.repetitions += 1
        review.last_rating = rating
        review.last_reviewed_at = now
        review.save()
        return Response({
            'card_id': card.card_id,
            'rating': rating,
            'due_at': review.due_at,
            'interval_days': review.interval_days,
            'repetitions': review.repetitions,
            'lapses': review.lapses,
        })

    @action(detail=True, methods=['post'])
    def bookmark(self, request, card_id=None):
        card = self.get_object()
        is_bookmarked = request.data.get('is_bookmarked')
        if not isinstance(is_bookmarked, bool):
            return Response(
                {'detail': 'is_bookmarked must be true or false.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        review, _ = AKTFlashcardReview.objects.get_or_create(user=request.user, card=card)
        review.is_bookmarked = is_bookmarked
        review.save(update_fields=['is_bookmarked'])
        return Response({'card_id': card.card_id, 'is_bookmarked': review.is_bookmarked})
