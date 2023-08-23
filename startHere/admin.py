from django.contrib import admin
from .models import Category, Question, Option, QuestionImage, Record,  Note, TextBook, Report
from django import forms
from django.utils.html import format_html
from django_object_actions import DjangoObjectActions
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from django.db import transaction
import pandas as pd
import openpyxl as xl
import re

class FileUploader(forms.Form):
    file = forms.FileField()


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4

class ImageInline(admin.TabularInline):
    model = QuestionImage
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    search_fields = ['content__icontains']
    autocomplete_fields = ["category"]
    inlines = [OptionInline,ImageInline]


@admin.register(TextBook)
class TextbookAdmin(admin.ModelAdmin):
    search_fields = ['content__icontains']
    autocomplete_fields = ["category"]




@admin.register(Option)    
class OptionAdmin(admin.ModelAdmin):
    search_fields = ['content__icontains','content__istartswith']



@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['user','question','comment','question_url']

    def question_url(self, report):
        url = f'/admin/startHere/question/{report.question.id}/change/'
        return format_html('<a href="{}">Edit question</a>', url)


admin.site.register(QuestionImage)
admin.site.register(Record)
admin.site.register(Note)

@admin.register(Category)
class CategoryAdmin(DjangoObjectActions, admin.ModelAdmin):
    autocomplete_fields = ["parent"]
    search_fields = ['title__icontains']

    def imports(modeladmin, request, queryset): 
        if request.method == "POST":
            file = request.FILES["file"]
        
            if not file.name.endswith('.xlsx'):
                messages.warning(request, 'The wrong file type was uploaded')
                return HttpResponseRedirect(request.path_info)
            
            
            data = pd.read_excel(file)
                        
            required_columns = ['category', 'question', 'a', 'b', 'c', 'd', 'e', 'f', 'correct','explanation']

        #     # Check if all required columns are present
            missing_columns = [col for col in required_columns if col not in data.columns]
            if missing_columns:
                messages.warning(request,f"The Excel file is missing the following required columns: {', '.join(missing_columns)}")
                return HttpResponseRedirect(request.path_info)
          
            with transaction.atomic():
                parent_category = Category.objects.get(id=queryset.id)                            
        #         # Create a list to hold the objects
                options_list = []
                         
        #         # Iterate through the rows in the Excel file
                for index, row in data.iterrows():
                    
                    if pd.isna(row['category']):
                        messages.warning(request,f"The field topic must not be empty")
                        return HttpResponseRedirect(request.path_info)
                    
                    if pd.isna(row['question']):
                        messages.warning(request,f"The field question must not be empty")
                        return HttpResponseRedirect(request.path_info)
                    
                    if pd.isna(row['correct']):
                        messages.warning(request,f"The field correct is empty for the question {row['question']}")
                        return HttpResponseRedirect(request.path_info)
                    else:
                        pattern = r'^[a-zA-Z]$'
                        if(bool(re.match(pattern, row['correct'].rstrip())) == False):
                            messages.warning(request,f"The field correct should contain only one alphabetic. {row['question']}")
                            return HttpResponseRedirect(request.path_info)
                            
                                        
                    category, _ = Category.objects.get_or_create(title=row['category'], parent=parent_category)
                    question, created = Question.objects.get_or_create(
                        category=category, 
                        content=row['question'],
                        explanation=row['explanation'] if pd.notna(row['explanation']) else None,
                    )

                    if created:
                        for option in ['a','b','c','d','e','f']:
                            if pd.notna(row[option]):
                                option = Option(
                                    question=question,
                                    content=row[option],
                                    is_correct=True if option == row['correct'] else False
                                )
                                options_list.append(option)
                            
                        
                        Option.objects.bulk_create(options_list)
                        options_list.clear()
                           
            messages.success(request, 'The file uploaded successfuly')
            return HttpResponseRedirect(request.path_info) 
            
        form = FileUploader()
        data = {"form": form}
        return render(request, "admin/upload.html",data)
        
        
    change_actions = ('imports', )












# @admin.register(Subject)
# class SubjectAdmin(DjangoObjectActions, admin.ModelAdmin):
#     inlines = [TopicInline]
#     list_display = ['title', 'subject_thumbnail']
#     search_fields = ['title__icontains']

#     def subject_thumbnail(self, instance):
#         return format_html(f'<img src={instance.thumbnail.url} class="thumbnail" />')

#     def exports(modeladmin, request, queryset):
#         subject = Subject.objects.get(id=queryset.id)
#         aphabetics = 'abcdefghijklmnopqrstuvwxyz'
          
#         data = []
#         for topic in subject.topics.all():
#             for question in topic.questions.all():
#                 options = question.options.all().values_list('content', flat=True)
#                 options_dict = {}
#                 # correct = ' '
#                 for index, option in enumerate(options):
#                     options_dict[aphabetics[index]] = option
#                 data.append({
#                     'topic': topic.title,
#                     'question': question.content,
#                     **options_dict,
#                     'correct' : ' '.join(aphabetics[index] for index, option in enumerate(question.options.all()) if option.is_correct),
#                     'year' : question.year_of_question,
#                     'type' : question.type,
#                     'explanation' : question.explanation
#                 })
        
            
#         # Create a DataFrame from the data
#         df = pd.DataFrame(data)

#         # Convert the DataFrame to an Excel file
#         with pd.ExcelWriter(f'{subject.title}.xlsx',  engine='openpyxl') as writer:
#             df.to_excel(writer, index=False)

#         # Return the Excel file as a response
#         with open(f'{subject.title}.xlsx', 'rb') as f:
#             response = HttpResponse(f.read(
#             ), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
#             response['Content-Disposition'] = f'attachment; filename={subject.title}.xlsx'
#             return response

    
#     def imports(modeladmin, request, queryset): 
#         if request.method == "POST":
#             file = request.FILES["file"]
        
#             if not file.name.endswith('.xlsx'):
#                 messages.warning(request, 'The wrong file type was uploaded')
#                 return HttpResponseRedirect(request.path_info)
            
            
#             data = pd.read_excel(file)
                        
#             required_columns = ['topic', 'question', 'a', 'b', 'c', 'd', 'e', 'f', 'correct','explanation']

#             # Check if all required columns are present
#             missing_columns = [col for col in required_columns if col not in data.columns]
#             if missing_columns:
#                 messages.warning(request,f"The Excel file is missing the following required columns: {', '.join(missing_columns)}")
#                 return HttpResponseRedirect(request.path_info)
          
#             with transaction.atomic():  
#                 subject = Subject.objects.get(id=queryset.id)
                            
#                 # Create a list to hold the objects
#                 options_list = []
                         
#                 # Iterate through the rows in the Excel file
#                 for index, row in data.iterrows():
                    
#                     if  pd.isna(row['topic']):
#                         messages.warning(request,f"The field topic must not be empty")
#                         return HttpResponseRedirect(request.path_info)
                    
#                     if  pd.isna(row['question']):
#                         messages.warning(request,f"The field question must not be empty")
#                         return HttpResponseRedirect(request.path_info)
                    
#                     if  pd.isna(row['correct']):
#                         messages.warning(request,f"The field correct is empty for the question {row['question']}")
#                         return HttpResponseRedirect(request.path_info)
#                     else:
#                         pattern = r'^[a-zA-Z]( [a-zA-Z])*$'
#                         if(bool(re.match(pattern, row['correct'].rstrip())) == False):
#                             messages.warning(request,f"The field correct should contain only alphabetic characters separated by spaces. {row['question']}")
#                             return HttpResponseRedirect(request.path_info)
                            
                                        
#                     topic, created = Topic.objects.get_or_create(title=row['topic'], subject=subject)
#                     question = Question.objects.create(
#                         topic=topic, 
#                         content=row['question'],
#                         explanation=row['explanation'] if pd.notna(row['explanation']) else None,
#                     )
                    
#                     for option in ['a','b','c','d','e','f']:
#                         if  pd.notna(row[option]):
                            
#                             option = Option(
#                                 question=question,
#                                 content=row[option],
#                                 is_correct=True if option in row['correct'].split(' ') else False
#                             )
#                             options_list.append(option)
                        
                    
#                     Option.objects.bulk_create(options_list)
#                     options_list.clear()
                           
#             messages.success(request, 'The file uploaded successfuly')
#             return HttpResponseRedirect(request.path_info) 
            
#         form = FileUploader()
#         data = {"form": form}
#         return render(request, "admin/upload.html",data)
        
        
#     change_actions = ('imports', )
#     # change_actions = ('imports', 'exports' ,)

    
#     class Media:
#         css = {
#             'all' : ['quizy/styles.css']
#         }

