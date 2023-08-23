from django.conf import settings
from django.db import models
from startHere.models import Question


class CommentManager(models.Manager):
    def all(self):
        return super().get_queryset().filter(parent=None)
       

    def filter_by_instance(self, instance):
        return super().get_queryset().filter(question=instance).filter(parent=None)
   


class Comment(models.Model):
    user = models.ForeignKey(
                settings.AUTH_USER_MODEL,
                on_delete=models.CASCADE,
                verbose_name=('User'))
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='comments')
    parent      = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    content     = models.TextField()
    timestamp   = models.DateTimeField(auto_now_add=True)

    # objects = CommentManager()

    class Meta:
        ordering = ['-timestamp']


    def __unicode__(self):  
        return str(self.content)

    def __str__(self):
        return str(self.content)

        
    def children(self): 
        return Comment.objects.filter(parent=self)

    @property
    def is_parent(self):
        if self.parent is not None:
            return False
        return True




