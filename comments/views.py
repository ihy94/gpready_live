from .models import Comment
from . import serializers
from rest_framework.viewsets import ModelViewSet
from comments.permissions import hasActiveSubscription
from rest_framework.permissions import IsAuthenticated
from .pagination import DefaultPagination

# Create your views here.
class CommentViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated & hasActiveSubscription]
    # pagination_class = DefaultPagination
    
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return serializers.SimpleCommentSerializer
        
        return serializers.CommentSerializer
    
    
    def get_queryset(self):
        queryset = Comment.objects.prefetch_related('replies').filter(user=self.request.user, parent=None)
        question_id = self.request.query_params.get('question_id')
        if question_id:
            return Comment.objects.prefetch_related('replies').filter(question_id=question_id, parent=None)
        return queryset
    

    def get_serializer_context(self):
        return {'user':self.request.user}
      
        








