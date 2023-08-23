from django.urls import path
from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register('quizzes', views.QuizViewSet, basename='quizzes')

router.register('playlist', views.PlaylistViewSet, basename='playlist')

router.register('questions_sessions', views.QuestionSessionViewSet, basename='questions_sessions')

router.register('quiz_detail', views.GetQuizDetailViewSet, basename='quiz_detail')


# URLConf
urlpatterns = [
    path('get_progress/<pk>/', views.GetProgress.as_view()),
    path('update_progress/', views.UpdateProgress.as_view()),
    path('update_playlist/', views.UpdatePlaylist().as_view()),
    path('result/<pk>/', views.Results.as_view()),
    path('answer/', views.CreateOrUpdateAnswer.as_view()),
    path('bulk_answers/', views.BulkMultipleAnswers.as_view()),
    path('reset_history/', views.ResetHistory.as_view()),
] + router.urls 