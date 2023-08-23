from rest_framework_nested import routers
from . import views


router = routers.DefaultRouter()

router.register('comments', views.CommentViewSet, basename='comments')

urlpatterns = [] + router.urls


