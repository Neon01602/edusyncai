from django import forms
from .models import Classroom, Classwork

class ClassroomForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ['name', 'subject']
        
class ClassworkForm(forms.ModelForm):
    class Meta:
        model = Classwork
        fields = ['title', 'description', 'file', 'deadline', "category"]
