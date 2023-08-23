from rest_framework import serializers
from .models import Category, Record, Option, Question, QuestionImage, Note, Report, TextBook

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
    class Meta:
        model = QuestionImage
        fields = ['id', 'title', 'src']

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
    class Meta:
        model = TextBook
        fields = ('id', 'content', 'created_at', 'updated_at')

class SimpleCategorySerializerForTextBook(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'title')

class TextBookSearchSerializer(serializers.ModelSerializer):
    category = SimpleCategorySerializerForTextBook()
    class Meta:
        model = TextBook
        fields = ('id', 'category')