from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from allauth.socialaccount.models import SocialToken
from django.shortcuts import render
import requests
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from django.contrib.auth import logout
from django.views.decorators.cache import never_cache
from .forms import ClassroomForm
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Classroom, Classwork, StudentWork
from django.http import JsonResponse, HttpResponseRedirect
import json
from django.middleware.csrf import get_token
from .forms import ClassworkForm
from django.http import HttpResponse
import os
from django.core.exceptions import ValidationError
from django.utils.timezone import now


GEMINI_API_KEY = "AIzaSyDHYLmJVPAPV9hj722jgSWgsEMg3EqU1R0"

@csrf_exempt
@login_required
def chatbot_api(request):
    if request.method == "POST":
        try:
            # Extract username of the logged-in user
            user = request.user
            username = user.username if user.is_authenticated else "Guest"

            # Parse user input
            data = json.loads(request.body)
            user_input = data.get("query", "").strip()

            # Prepend system prompt for Syncrona behavior
            system_prompt = (
                """You are Syncrona, the AI educational assistant developed by Sahayak.AI, founded by Ahmad Abdullah. Sahayak.AI is a cutting-edge educational platform designed to empower students and teachers by providing AI-powered tools for learning, including:

Auto-generated notes for lectures and study materials.

Smart quizzes to evaluate understanding.

Learning insights to track progress and suggest improvements.

Your task:

Respond only with accurate, relevant educational content. Focus on the subject matter in the user’s query.

Avoid providing opinions, personal commentary, or unrelated content such as movies, games, entertainment, or non-educational topics.

Keep responses concise, structured, and student-friendly. Use clear explanations suitable for school or college-level learners.

Provide examples, definitions, and step-by-step explanations if needed, but do not go off-topic.

When responding to queries about Sahayak.AI or its features, mention that it was founded by Ahmad Abdullah and is focused on AI-assisted classroom learning.

If a user asks something outside education, politely redirect the response to an educational perspective or context.

Maintain a professional yet approachable tone, making content easy to understand and engaging for students. Dont provide unless asked about any details"""
            )

            # Combine system prompt with user input
            formatted_input = f"{system_prompt}\nUser ({username}): {user_input}"

            # API Request to Gemini
            api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
            headers = {"Content-Type": "application/json"}
            payload = {"contents": [{"parts": [{"text": formatted_input}]}]}

            response = requests.post(api_url, json=payload, headers=headers)
            response_data = response.json()

            # Extract chatbot response safely
            answer = (
                response_data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "I couldn't find an answer.")
            )

            return JsonResponse({"response": answer})
        
        except Exception as e:
            return JsonResponse({"response": "Error connecting to Syncrona."})

    return JsonResponse({"error": "Invalid request"}, status=400)
def chatbot_view(request):
    return render(request, "chatbot.html")

@login_required
def view_classroom(request, class_code):
    print("Received class code:", class_code)  # Debugging
    classwork_id = request.GET.get('classwork_id')  # or another method
    try:
        classwork_id = int(classwork_id)
    except (TypeError, ValueError):
        classwork_id = None

    try:
        classroom = Classroom.objects.get(unique_code=class_code)
        print("Classroom found:", classroom.name)  # Confirm it exists
    except Classroom.DoesNotExist:
        print("Classroom does not exist!")  # Should not happen
        return HttpResponse("Classroom not found!", status=404)

    is_teacher = request.user == classroom.teacher  

    return render(request, 'classroom_list.html', {
        'classroom': classroom,
        'is_teacher': is_teacher,
        'classwork_id': classwork_id,
        
    })
    
    
def get_class_students(request, class_code):
    try:
        classroom = Classroom.objects.get(unique_code=class_code)
        students = classroom.students.all().values('id', 'username', 'first_name', 'last_name', 'profile_picture')
        
        return JsonResponse({'students': list(students)}, safe=False)
    except Classroom.DoesNotExist:
        return JsonResponse({'error': 'Classroom not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@login_required
def delete_account(request):
    if request.method == "POST":
        try:
            user = request.user
            user.delete()
            return JsonResponse({"message": "Account deleted successfully."}, status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request."}, status=400)


@login_required
def leave_class(request, class_code):  # Accept class_code from URL
    classroom = get_object_or_404(Classroom, unique_code=class_code)
    user = request.user

    if user in classroom.students.all():
        classroom.students.remove(user)  # Remove user from the class
        
        # Redirect to home page after leaving the class
        return redirect('home')  # Make sure 'home' is a valid URL name in urls.py

    return JsonResponse({"error": "You are not a member of this class."}, status=400)

@login_required
def add_classwork(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)

    if request.user != classroom.teacher:
        return JsonResponse({'error': 'You are not allowed to add work!'}, status=403)

    if request.method == "POST":
        form = ClassworkForm(request.POST, request.FILES)
        if form.is_valid():
            classwork = form.save(commit=False)
            classwork.classroom = classroom
            classwork.teacher = request.user

            if classwork.category in ["test", "assignment"] and not classwork.deadline:
                return JsonResponse(
                    {"error": "Deadline is required for Tests and Assignments."},
                    status=400
                )

            classwork.save()
            return JsonResponse({'message': 'Classwork added successfully!'})
        else:
            return JsonResponse({'error': form.errors}, status=400)

    form = ClassworkForm()
    return render(request, 'add_classwork_modal.html', {'form': form, 'classroom': classroom})



@login_required
def view_classwork(request, classroom_id):
    classroom = get_object_or_404(Classroom, id=classroom_id)
    if request.user != classroom.teacher and request.user not in classroom.students.all():
        return JsonResponse({'error': 'Unauthorized access!'}, status=403)

    classworks = Classwork.objects.filter(classroom=classroom).order_by('-created_at')
    
    # ✅ Return JSON response for AJAX
    data = {
        "classworks": [
            {
                "id": work.id,
                "title": work.title,
                "description": work.description,
                "created_at": work.created_at.strftime("%B %d, %Y %H:%M"),
                "file_url": request.build_absolute_uri(work.file.url) if work.file else None
            }
            for work in classworks
        ]
    }
    return JsonResponse(data)


def join_class(request):
    if request.method == "POST":
        class_code = request.POST.get("class_code", "").strip()
        classroom = Classroom.objects.filter(unique_code=class_code).first()

        if classroom:
            user = request.user
            print(f"DEBUG: User {user.username} is attempting to join {classroom.name}")  # Debug

            if user in classroom.students.all():
                print("DEBUG: User already joined this class")  # Debug
                return JsonResponse({"exists": True, "already_joined": True})
            else:
                classroom.students.add(user)
                classroom.save()  # Ensure the save() method is called

                print(f"DEBUG: {user.username} has been added to {classroom.name}")  # Debug

                return JsonResponse({"exists": True, "already_joined": False, "name": classroom.name, "subject": classroom.subject, "unique_code": class_code})
        else:
            print("DEBUG: Invalid class code entered")  # Debug
            return JsonResponse({"exists": False})

    return JsonResponse({"error": "Invalid request"}, status=400)


def get_joined_classes(request):
    user = request.user
    joined_classes = Classroom.objects.filter(students=user).values("name", "subject", "unique_code")

    print(f"DEBUG: {user.username} has joined these classes:", list(joined_classes))  # Debug

    return JsonResponse({"joined_classes": list(joined_classes)})


@login_required
def create_classroom(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            subject = data.get("subject")

            if not name or not subject:
                return JsonResponse({"error": "Both name and subject are required."}, status=400)

            classroom = Classroom.objects.create(
                teacher=request.user, 
                name=name, 
                subject=subject
            )

            return JsonResponse({
                "message": "Class created successfully!",
                "class_id": classroom.id,
                "name": classroom.name,
                "subject": classroom.subject,
                "unique_code": classroom.unique_code
            })

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)

@login_required
def get_user_classes(request):
    """Fetch classes created by the logged-in user along with the teacher's name"""
    teacher = request.user
    user_classes = Classroom.objects.filter(teacher=teacher).values(
        "id", "name", "subject", "unique_code"
    )

    return JsonResponse({"classes": list(user_classes), "teacher_name": teacher.get_full_name() or teacher.username})

# CSRF Token View (optional)
def get_csrf_token(request):
    return JsonResponse({'csrftoken': get_token(request)})

@login_required
def edit_classroom(request, class_id):
    """ Allows only the class creator (teacher) to edit details """
    classroom = get_object_or_404(Classroom, id=class_id)

    if request.user != classroom.teacher:
        messages.error(request, "You do not have permission to edit this class.")
        return redirect("classroom_list")

    if request.method == "POST":
        classroom.name = request.POST.get("name", classroom.name)
        classroom.subject = request.POST.get("subject", classroom.subject)
        classroom.save()
        messages.success(request, "Class updated successfully!")

    return redirect("classroom_detail", class_id=class_id)


@login_required
def join_classroom(request, unique_code):
    """ Allows students to join a class using the unique link """
    classroom = get_object_or_404(Classroom, unique_code=unique_code)

    if request.user not in classroom.students.all():
        classroom.students.add(request.user)
        messages.success(request, f"You have joined {classroom.name} successfully!")
    else:
        messages.warning(request, "You are already a member of this class.")

    return redirect("classroom_list")


@login_required
def classroom_list(request):
    """ Displays the classes the user created and the ones they joined """
    created_classes = Classroom.objects.filter(teacher=request.user)
    joined_classes = Classroom.objects.filter(students=request.user)

    return render(request, "classroom_list.html", {
        "created_classes": created_classes,
        "joined_classes": joined_classes
    })

    
    return render(request, 'create_class.html', {'form': form})

def classroom_courses(request):
    token = SocialToken.objects.get(account__user=request.user, account__provider='google')
    headers = {"Authorization": f"Bearer {token.token}"}
    response = requests.get("https://classroom.googleapis.com/v1/courses", headers=headers)
    data = response.json()
    return render(request, 'classroom.html', {'courses': data.get("courses", [])})

@login_required
def get_user_profile(request):
    user = request.user
    return JsonResponse({
        "first_name": user.first_name,  # ✅ Add first name
        "last_name": user.last_name,    # ✅ Add last name
        "username": user.username,
        "profile_picture": user.profile_picture if user.profile_picture else None,
        "email": user.email, 
    })
from django.core.exceptions import ObjectDoesNotExist
@login_required
def fetch_student_work(request):
    if request.method == "GET":
        try:
            classwork_id = request.GET.get("classwork_id")

            if not classwork_id:
                return JsonResponse({"error": "Missing classwork ID"}, status=400)

            classwork = get_object_or_404(Classwork, id=classwork_id)

            # ✅ FIX: Check against classwork.classroom.teacher
            if request.user != classwork.classroom.teacher:
                return JsonResponse({"error": "Unauthorized access"}, status=403)

            student_works = StudentWork.objects.filter(classwork=classwork).select_related("student")

            work_data = [
                {
                    "id": work.id,
                    "student_name": work.student.get_full_name() or work.student.username,
                    "file_url": work.file.url if work.file and hasattr(work.file, 'url') else None,
                    "status": work.status,
                    "feedback": work.feedback,
                    "submitted_at": work.submitted_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for work in student_works
            ]

            return JsonResponse({"student_works": work_data}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=400)


def main(request):
    testimonials = Testimonial.objects.order_by("-created_at")
    return render(request, "new.html", {"testimonials": testimonials})
def some_view(request):
    testimonials = Testimonial.objects.values('id', 'name', 'role', 'review', 'profile_picture', 'link')
    return render(request, 'your_template.html', {
        'testimonials': json.dumps(list(testimonials)),  # Important for {{ testimonials|safe }}
    })
# Create your views here.
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Testimonial

@login_required
@csrf_exempt  # Only keep if CSRF token is not used correctly in JS
def submit_testimonial(request):
    if request.method == "POST":
        name = request.POST.get("name", "")
        role = request.POST.get("role", "")
        review = request.POST.get("review", "")
        pfp = request.POST.get("profileImage", "")

        testimonial = Testimonial.objects.create(
            user=request.user,
            name=name,
            role=role,
            review=review,
            profile_picture=pfp
        )

        return JsonResponse({
            "name": testimonial.name,
            "role": testimonial.role,
            "review": testimonial.review,
            "profileImage": testimonial.profile_picture or "/static/default-profile.png"
        })

    return JsonResponse({"error": "Invalid request"}, status=400)

@login_required
def progress_page(request):
    """
    Renders the progress.html template.
    """
    return render(request, "progress.html")


def leave_classroom(request, classroom_id):
    classroom = Classroom.objects.filter(id=classroom_id).first()
    if not classroom:
        messages.error(request, "Classroom not found.")
        return redirect("my_classrooms")

    if request.method == "POST":
        classroom.students.remove(request.user)
        messages.success(request, f"You have left {classroom.name}.")
        return redirect("home")

    return redirect("classroom_detail", classroom_id=classroom.id)


@login_required
def get_class_progress(request):
    student = request.user
    joined_classes = Classroom.objects.filter(students=student)

    classes_data = []
    for cls in joined_classes:
        classworks = Classwork.objects.filter(classroom=cls)
        total_classworks = classworks.count()

        # ✅ Only count graded submissions
        graded_count = StudentWork.objects.filter(
            classwork__classroom=cls,
            student=student,
            status="graded"
        ).count()

        percent = round((graded_count / total_classworks) * 100) if total_classworks else 0

        categories = {}
        for cat in ["notes", "assignment", "test"]:
            cat_total = classworks.filter(category=cat).count()
            cat_graded = StudentWork.objects.filter(
                classwork__classroom=cls,
                classwork__category=cat,
                student=student,
                status="graded"  # ✅ only graded
            ).count()
            categories[cat] = {"total": cat_total, "graded": cat_graded}

        classes_data.append({
            "subject": cls.subject,
            "unique_code": cls.unique_code,
            "graded_count": graded_count,       # ✅ added
            "total_classworks": total_classworks,
            "percent": percent,
            "categories": categories
        })

    return JsonResponse({"classes": classes_data})

@login_required
def fetch_my_feedback(request, classwork_id):
    try:
        submission = StudentWork.objects.get(
            student=request.user,
            classwork_id=classwork_id
        )
        return JsonResponse({
            "submission": {
                "grade": submission.ai_grade,
                "feedback": submission.ai_feedback,
                "submitted_at": submission.submitted_at.strftime("%Y-%m-%d %H:%M"),
              
            }
        })
    except StudentWork.DoesNotExist:
        return JsonResponse({"error": "No submission found"}, status=404)


def home(request):
    return render(request, 'home.html') 

def settings(request):
    return render(request, 'settings.html') 

def custom_logout(request):
    logout(request) 
    request.session.flush()# Logs out the user
    return redirect('/') 

@csrf_exempt
def delete_classwork(request):
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)
            classwork_title = data.get("title")  # ✅ Fetch title from request body

            if not classwork_title:
                return JsonResponse({'error': 'Missing Classwork Title'}, status=400)

            classwork = Classwork.objects.filter(title=classwork_title).first()  # ✅ Fetch using title
            if not classwork:
                return JsonResponse({'error': 'Classwork not found'}, status=404)

            classwork.delete()
            return JsonResponse({'message': 'Classwork deleted successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def profile_view(request):
    
    return render(request, 'profile.html')

@login_required
def delete_classroom(request):
    """Delete a classroom using unique_code from request body."""
    if request.method == 'DELETE':
        try:
            data = json.loads(request.body)  # ✅ Parse JSON request body
            print("Received Data:", data)  # 🔍 Debugging

            unique_code = data.get("unique_code")  
            print("Extracted Unique Code:", unique_code)  # 🔍 Debugging

            if not unique_code:
                return JsonResponse({'error': '❌ Missing unique code'}, status=400)

            classroom = get_object_or_404(Classroom, unique_code=unique_code)

            if request.user != classroom.teacher:
                return JsonResponse({'error': '❌ Unauthorized'}, status=403)

            classroom.delete()
            return JsonResponse({'message': '✅ Classroom deleted successfully'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': '❌ Invalid request method'}, status=405)

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from .models import Classwork, StudentWork
import os
import requests
import base64
import pytesseract
from PIL import Image
from pdf2image import convert_from_path

# OCR setup
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\Program Files\poppler-25.07.0\Library\bin"

# Copyleaks credentials
COPYLEAKS_EMAIL = "ahmadabdullah007860@gmail.com"
COPYLEAKS_KEY = "11294cfb-f144-4985-8e50-eb3a94aafe24"

# Gemini API key



# ------------------- HELPERS -------------------
def extract_text_from_file(file_path):
    """Extract text from PDF/Image using OCR (Tesseract)."""
    pages = convert_from_path(file_path, 300, poppler_path=POPPLER_PATH)
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page) + "\n"
    return text.strip()


def analyze_text_with_gemini(text):
    """Send text to Gemini API for summary, grade, feedback."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": f"Analyze the following text:\n\n{text}\n\n1. Summarize\n2. Grade (0-10)\n3. Provide feedback"}
                ]
            }
        ]
    }

    res = requests.post(url, headers=headers, json=payload)
    res.raise_for_status()
    return res.json()


def get_copyleaks_token():
    res = requests.post(
        "https://id.copyleaks.com/v3/account/login/api",
        json={"email": COPYLEAKS_EMAIL, "key": COPYLEAKS_KEY}
    )
    res.raise_for_status()
    return res.json()["access_token"]

def check_plagiarism(text, scan_id="student-submission-001"):
    token = get_copyleaks_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # ✅ Correct endpoint (no /text/)
    url = f"https://api.copyleaks.com/v3/scans/submit/{scan_id}"

    payload = {
        "base64": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
        "filename": "submission.txt",
        "properties": {
            "sandbox": True  # testing mode
        }
    }

    res = requests.put(url, headers=headers, json=payload)

    # Debugging info if it still fails
    if res.status_code != 200 and res.status_code != 201:
        print("Copyleaks Error Response:", res.text)

    res.raise_for_status()
    return res.json() if res.text else {"status": "submitted"}


@login_required
def reject_submission(request, submission_id):
    if request.method == "POST":
        submission = get_object_or_404(StudentWork, id=submission_id)
        submission.status = "rejected"
        submission.save()
        return JsonResponse({"status": "ok"})

@csrf_exempt
def approve_submission(request, submission_id):
    if request.method == "POST":
        try:
            data = json.loads(request.body.decode("utf-8"))
            feedback = data.get("feedback", "")
            grade = data.get("grade", "")

            submission = StudentWork.objects.get(id=submission_id)
            submission.status = "graded"
            submission.ai_feedback = feedback
            submission.ai_grade = grade
            submission.save()

            return JsonResponse({
                "status": "approved",
                "feedback": submission.feedback,
                "grade": submission.ai_grade,
            })
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"error": "Invalid request"}, status=405)


@csrf_exempt
def save_feedback(request, submission_id):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)
    
    try:
        submission = get_object_or_404(StudentWork, id=submission_id)
        data = json.loads(request.body)
        feedback = data.get("feedback", "")
        grade = data.get("grade", "")

        # Save feedback and grade permanently
        submission.ai_feedback = feedback
        submission.ai_grade = grade
        if submission.status != "graded":
            submission.status = "graded"
        submission.save()

        # ✅ Print to console for debugging
        print(f"[DEBUG] Submission {submission_id} saved. Feedback: {feedback}, Grade: {grade}")

        return JsonResponse({
            "feedback": submission.ai_feedback or "",
            "grade": submission.ai_grade or ""
        })
    
    except Exception as e:
        print(f"[ERROR] Submission {submission_id} save failed: {e}")
        return JsonResponse({"error": str(e)}, status=500)

from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import StudentWork  # adjust if different

@csrf_exempt
def analyze_student_work(request, submission_id):
    """
    Loads submission from DB, runs analysis (fresh if not approved),
    else returns cached results.
    """
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    submission = get_object_or_404(StudentWork, id=submission_id)

    try:
        # ------------------- If already approved, return cached -------------------
        if submission.status == "graded":   # or whatever status you use for approved
            return JsonResponse({
                "summary": submission.ai_summary,
                "feedback": submission.ai_feedback,
                "grade": submission.ai_grade,
                "plagiarism_score": submission.plagiarism_score,
                "plagiarism_matches": submission.plagiarism_matches or []
            })

        # ------------------- Run analysis if not approved -------------------
        file_path = submission.file.path
        extracted_text = extract_text_from_file(file_path)

        # 1. Gemini Analysis
        gemini_result = analyze_text_with_gemini(extracted_text)
        summary, grade, feedback = None, None, None
        try:
            summary = gemini_result["candidates"][0]["content"]["parts"][0]["text"]
            grade = gemini_result.get("grade")
            feedback = gemini_result.get("feedback")
        except Exception as e:
            print("Gemini parsing error:", e)

        # 2. Copyleaks Plagiarism
        plagiarism_score, plagiarism_matches = None, []
        try:
            plagiarism_result = check_plagiarism(extracted_text, f"submission-{submission.id}")
            plagiarism_score = plagiarism_result.get("score")
            plagiarism_matches = plagiarism_result.get("results", [])
        except Exception as e:
            print("Copyleaks error:", e)
            plagiarism_score = -1
            plagiarism_matches = []

        # ------------------- Save Results -------------------
        submission.extracted_text = extracted_text
        submission.ai_summary = summary
        submission.ai_grade = grade
        submission.ai_feedback = feedback
        submission.plagiarism_score = plagiarism_score
        submission.plagiarism_matches = plagiarism_matches
        submission.save()

        return JsonResponse({
            "summary": summary,
            "feedback": feedback,
            "grade": grade,
            "plagiarism_score": plagiarism_score,
            "plagiarism_matches": plagiarism_matches
        })

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)





# ------------------- MAIN VIEW -------------------
@csrf_exempt
@login_required
def upload_student_work(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    try:
        student = request.user
        classwork_id = request.POST.get("classwork_id")
        file = request.FILES.get("file")
        feedback = request.POST.get("feedback", "")
        status = request.POST.get("status", "pending")

        if not classwork_id or not file:
            return JsonResponse({"error": "Missing classwork ID or file"}, status=400)

        classwork = Classwork.objects.filter(id=classwork_id).first()
        if not classwork:
            return JsonResponse({"error": "Classwork not found"}, status=404)

        allowed_extensions = ["pdf", "docx", "txt", "png", "jpg", "jpeg"]
        file_extension = os.path.splitext(file.name)[1][1:].lower()
        if file_extension not in allowed_extensions:
            return JsonResponse({"error": "Invalid file format."}, status=400)

        # Save or update submission
        student_work, created = StudentWork.objects.get_or_create(
            student=student,
            classwork=classwork,
            defaults={
                "file": file,
                "status": status,
                "feedback": feedback,
                "submitted_at": now(),
                "updated_at": now()
            }
        )

        if not created:
            student_work.file = file
            student_work.status = status
            student_work.feedback = feedback
            student_work.updated_at = now()
            student_work.save()
            message = "Work updated successfully!"
        else:
            message = "Work uploaded successfully!"

        # ✅ Only upload, no AI/plagiarism checks here
        return JsonResponse({
            "message": message,
            "file_url": student_work.file.url,
            "status": student_work.status
        }, status=201)

    except ValidationError as ve:
        return JsonResponse({"error": str(ve)}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
def approve_submission(request, submission_id):
    if request.method == "POST":
        try:
            submission = StudentWork.objects.get(id=submission_id)
            submission.status = "graded"
            submission.save()
            return JsonResponse({"success": True, "status": "graded"})
        except StudentWork.DoesNotExist:
            return JsonResponse({"error": "Submission not found"}, status=404)
    return JsonResponse({"error": "Invalid request"}, status=400)

    
@login_required
def get_teacher_classrooms(request):
    # DEBUG: remove 403 to see data
    classrooms = request.user.created_classes.all()
    data = [
        {
            "id": cls.id,
            "name": cls.name,
            "subject": cls.subject,
            "students_count": cls.students.count(),
            "unique_code": cls.unique_code,
        } for cls in classrooms
    ]
    return JsonResponse({"classrooms": data})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Classroom, Classwork, StudentWork

@login_required
def teacher_classroom_detail(request, classroom_id):
    # Ensure only the teacher who owns the classroom can access
    classroom = get_object_or_404(Classroom, id=classroom_id, teacher=request.user)
    
    # Get all students in the classroom
    students = classroom.students.all()
    
    # Get all classworks for this classroom
    classworks = Classwork.objects.filter(classroom=classroom, category__in=["test", "assignment"])

    # Prepare a list of classworks with student submission info
    classworks_data = []
    for work in classworks:
        students_data = []
        for student in students:
            submission = StudentWork.objects.filter(classwork=work, student=student).first()
            students_data.append({
                "student": student,
                "submission": submission  # Can be None if not submitted
            })
        classworks_data.append({
            "work": work,
            "students_data": students_data
        })

    context = {
        "classroom": classroom,
        "classworks_data": classworks_data
    }

    return render(request, "myclassroom.html", context)

