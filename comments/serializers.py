from .models import Comment
from rest_framework import serializers



class SimpleCommentSerializer(serializers.ModelSerializer):
    poster = serializers.SerializerMethodField(method_name='get_poster')
    class Meta:
        model = Comment
        fields = ['id', 'content', 'poster', 'question',  'parent', 'timestamp']
        

    def get_poster(self, comment):
        return comment.user.username

    def create(self, validated_data):
        return Comment.objects.create(user=self.context['user'], **validated_data)
        

class CommentChildSerializer(serializers.ModelSerializer):
    poster = serializers.SerializerMethodField(method_name='get_poster')
    class Meta:
        model = Comment
        fields = [
            'id',
            'content',
            'poster',
            'timestamp',
        ]
    
    def get_poster(self, comment):
        return comment.user.username


class CommentSerializer(SimpleCommentSerializer):
    replies =   serializers.SerializerMethodField(method_name='get_replies')
    reply_count = serializers.SerializerMethodField(method_name='get_reply_count')


    def get_replies(self, obj):
        if obj.is_parent:
            return CommentChildSerializer(obj.replies, many=True).data
        return None
    

    def get_reply_count(self, obj):
        if obj.is_parent:
            return obj.replies.count()
        return 0
        
    class Meta(SimpleCommentSerializer.Meta):
        model = Comment
        fields = SimpleCommentSerializer.Meta.fields + ['reply_count', 'replies']
        
   
            
