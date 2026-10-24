from rest_framework import serializers
from .models import (
    AKTFlashcard,
    AKTFlashcardReview,
    AKTTextbookChapter,
    Category,
    Record,
    Option,
    Question,
    QuestionImage,
    Note,
    Report,
    TextBook,
)

class RecordSerializer(serializers.ModelSerializer):
    attempted_questions =  serializers.SerializerMethodField(method_name='get_attemted_questions')
    class Meta:
        model = Record
        fields = (  
            'id',
            'user',
            'correct_answers',
            'wrong_answers',
            'attempted_questions'
        )

    def get_attemted_questions(self, record):
        return record.correct_answers + record.wrong_answers

class SimpleCategorySerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField(method_name='get_questions_count')
    class Meta:
        model = Category
        fields = (  
            'id',
            'title',
            'questions_count',
        ) 

    def get_questions_count(self, category):
        if not category.is_parent:
            return category.questions_count
        
        sub_count = sum(sub.questions_count for sub in category.sub_categories.all())
        return category.questions_count + sub_count

class WithRecordsCategorySerializer(serializers.ModelSerializer):
    records = RecordSerializer(many=True)
    questions_count = serializers.SerializerMethodField(method_name='get_questions_count')
    class Meta:
        model = Category
        fields = (  
            'id',
            'title',
            'parent',
            'records',
            'questions_count',
        ) 
    
    def get_questions_count(self, category):
        if not category.is_parent:
            return category.questions_count
        
        sub_count = sum(sub.questions_count for sub in category.sub_categories.all())
        return category.questions_count + sub_count

class WithRecordsSubCategorySerializer(WithRecordsCategorySerializer):              
    class Meta(WithRecordsCategorySerializer.Meta):
        model = Category
        fields = WithRecordsCategorySerializer.Meta.fields

class WithRecodsSubCategoryCategroySerializer(WithRecordsCategorySerializer):    
    sub_categories =  serializers.SerializerMethodField(method_name='get_sub_categories')
    
    def get_sub_categories(self, category):
        if category.is_parent:
            return WithRecordsSubCategorySerializer(category.sub_categories, many=True).data
        return None
    
    class Meta(WithRecordsCategorySerializer.Meta):
        model = Category
        fields = WithRecordsCategorySerializer.Meta.fields + ('sub_categories',)

class TTNestedSubCategroySerializer(SimpleCategorySerializer):    
    sub_categories =  serializers.SerializerMethodField(method_name='get_sub_categories')
    
    def get_sub_categories(self, category):
        return  SimpleCategorySerializer(category.sub_categories, many=True).data
    
    class Meta(SimpleCategorySerializer.Meta):
        model = Category
        fields = SimpleCategorySerializer.Meta.fields + ('sub_categories',)

class NestedSubCategroySerializer(SimpleCategorySerializer):    
    sub_categories =  serializers.SerializerMethodField(method_name='get_sub_categories')
    
    def get_sub_categories(self, category):
        return TTNestedSubCategroySerializer(category.sub_categories, many=True).data
    
    class Meta(SimpleCategorySerializer.Meta):
        model = Category
        fields = SimpleCategorySerializer.Meta.fields + ('sub_categories',)

class WithNestedSubCategoryCategroySerializer(SimpleCategorySerializer):    
    sub_categories =  serializers.SerializerMethodField(method_name='get_sub_categories')
    
    def get_sub_categories(self, category):
        return NestedSubCategroySerializer(category.sub_categories, many=True).data
    
    class Meta(SimpleCategorySerializer.Meta):
        model = Category
        fields = SimpleCategorySerializer.Meta.fields + ('sub_categories',)
                           
class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = '__all__'
        
class ImageSerializer(serializers.ModelSerializer):
    src = serializers.SerializerMethodField(method_name='get_src')
    class Meta:
        model = QuestionImage
        fields = ['id', 'title', 'src']

    
    def get_src(self, obj):
        return obj.src.url
        

class BaseQuestionSerializer(serializers.ModelSerializer):
    options = OptionSerializer(many=True)
    class Meta:
        model = Question
        fields = ('id', 'content', 'options')
            
    def get_topic(self, question):
        pass
    
    def get_module(self, question):
        pass
    
    
class SimpleQuestionSerializer(BaseQuestionSerializer):
    category = serializers.StringRelatedField()    
    class Meta(BaseQuestionSerializer.Meta):
        model = Question
        fields = BaseQuestionSerializer.Meta.fields + ('category',)
        
class QuestionSerializer(BaseQuestionSerializer):
    images = ImageSerializer(many=True)
    notes = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta(BaseQuestionSerializer.Meta):
        model = Question
        fields = BaseQuestionSerializer.Meta.fields +  (
            "explanation",
            "notes",
            'images',
        )

class SimpleNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id','content','question','created_at']

    def create(self, validated_data):
        obj = Note.objects.create(user=self.context['user'], **validated_data)
        return obj
        
class NoteSerializer(serializers.ModelSerializer):
    question = SimpleQuestionSerializer()
    class Meta:
        model = Note
        fields = ['id','content','question','created_at']
      

    def create(self, validated_data):
        obj = Note.objects.create(user=self.context['user'], **validated_data)
        return obj
  
class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id','question','comment']
        
    def create(self, validated_data):
        return Report.objects.create(user=self.context['user'], **validated_data)

class TextBookSerializer(serializers.ModelSerializer):
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = TextBook
        fields = ('id', 'content', 'created_at', 'updated_at', 'is_complete')

class SimpleCategorySerializerForTextBook(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title')

class TextBookSearchSerializer(serializers.ModelSerializer):
    category = SimpleCategorySerializerForTextBook()
    class Meta:
        model = TextBook
        fields = ('id', 'category')


class AKTTextbookChapterSerializer(serializers.ModelSerializer):
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = AKTTextbookChapter
        fields = (
            'chapter_id',
            'curriculum_area',
            'topic',
            'curriculum_outcomes',
            'title',
            'position',
            'content',
            'sources',
            'is_complete',
        )


class AKTFlashcardSerializer(serializers.ModelSerializer):
    is_bookmarked = serializers.SerializerMethodField()
    due_at = serializers.SerializerMethodField()
    interval_days = serializers.SerializerMethodField()
    repetitions = serializers.SerializerMethodField()

    class Meta:
        model = AKTFlashcard
        fields = (
            'card_id', 'deck', 'topic', 'front', 'clue', 'answer',
            'learning_point', 'source', 'tags', 'difficulty',
            'is_bookmarked', 'due_at', 'interval_days', 'repetitions',
        )

    def _review(self, card):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        return AKTFlashcardReview.objects.filter(user=request.user, card=card).first()

    def get_is_bookmarked(self, card):
        review = self._review(card)
        return review.is_bookmarked if review else False

    def get_due_at(self, card):
        review = self._review(card)
        return review.due_at if review else None

    def get_interval_days(self, card):
        review = self._review(card)
        return review.interval_days if review else 0

    def get_repetitions(self, card):
        review = self._review(card)
        return review.repetitions if review else 0


class AKTTextbookChapterListSerializer(serializers.ModelSerializer):
    is_complete = serializers.BooleanField(read_only=True)

    class Meta:
        model = AKTTextbookChapter
        fields = (
            'chapter_id',
            'curriculum_area',
            'topic',
            'curriculum_outcomes',
            'title',
            'position',
            'is_complete',
        )
