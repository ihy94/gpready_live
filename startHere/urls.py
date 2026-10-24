from django.urls import path
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register('report', views.ReportViewSet, basename='reports')

router.register('note', views.NoteViewSet, basename='notes')

router.register('categories', views.CategoryViewSet, basename='categories')

router.register('textbooks', views.TextBookViewSet, basename='textbooxs')

categories_router = routers.NestedDefaultRouter(router, 'categories', lookup='category')

categories_router.register('textbook', views.TextBookViewSet, basename='category-textbook')


urlpatterns = [
    path('count_questions/', views.CountQuestions.as_view()),
    path('score_comparison/', views.ScoreComparisonView.as_view()),
] + router.urls + categories_router.urls 

