from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    profile_picture = models.URLField(null=True, blank=True)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return self.username
# Create your models here.

from django.db import models
from django.contrib.auth.models import User

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

from django.conf import settings
from django.db import models

import random
import string
from django.db import models
from django.conf import settings

def generate_unique_code():
    """Generate a random 6-character code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class Classroom(models.Model):
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="created_classes")
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="joined_classes", blank=True)
    name = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    unique_code = models.CharField(max_length=10, unique=True, blank=True, default=generate_unique_code)

    def __str__(self):
        return f"{self.name} ({self.subject}) - {self.teacher.username}"


    def save(self, *args, **kwargs):
        if not self.unique_code:
            import random, string
            self.unique_code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        super().save(*args, **kwargs)

from django.db import models
from django.conf import settings

class Classwork(models.Model):
    CATEGORY_CHOICES = [
        ("notes", "Notes"),
        ("test", "Test"),
        ("assignment", "Assignment"),
    ]

    classroom = models.ForeignKey(
        "Classroom", on_delete=models.CASCADE, related_name="classworks"
    )
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="assigned_classwork"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="classwork_files/", blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    deadline = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.classroom.name} ({self.teacher.username})"

def student_submission_path(instance, filename):
    """Store student submissions under a folder named after the student's email or ID."""
    return f"student_submissions/{instance.student.email}/{filename}"

class StudentWork(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('rejected', 'Rejected'),
    ]

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submitted_works"
    )
    classwork = models.ForeignKey(
        'Classwork',
        on_delete=models.CASCADE,
        related_name="submissions"
    )
    file = models.FileField(
        upload_to=student_submission_path,
        help_text="Upload your work file (PDF, DOCX, PNG, etc.)."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    feedback = models.TextField(blank=True, null=True)

    # ✅ New AI + Plagiarism fields
    extracted_text = models.TextField(blank=True, null=True)
    ai_summary = models.TextField(blank=True, null=True)
    ai_grade = models.CharField(max_length=10, blank=True, null=True)
    ai_feedback = models.TextField(blank=True, null=True)
    plagiarism_score = models.FloatField(blank=True, null=True)
    plagiarism_matches = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.student.email} - {self.classwork.title} ({self.get_status_display()})"

    
class Testimonial(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=255)
    review = models.TextField()
    profile_picture = models.URLField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
