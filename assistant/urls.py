from django.urls import path
from . import views


urlpatterns = [
    path('settings/', views.settings, name='settings'),
    path("reject-submission/<int:submission_id>/", views.reject_submission, name="reject_submission"),
    path("classroom/<int:classwork_id>/my-feedback/", views.fetch_my_feedback, name="fetch_my_feedback"),
    # urls.py
    path('leave-class/<int:classroom_id>/', views.leave_classroom, name='leave_classroom'),

    path('save-feedback/<int:submission_id>/', views.save_feedback, name='save_feedback'),
    path("approve-submission/<int:submission_id>/", views.approve_submission, name="approve_submission"),
    path("approve-submission/<int:submission_id>/", views.approve_submission, name="approve_submission"),
    path('teacher/classrooms/', views.get_teacher_classrooms, name='teacher_classrooms'),
    path("analyze-work/<int:submission_id>/", views.analyze_student_work, name="analyze_student_work"),
    path('teacher/classroom/<int:classroom_id>/', views.teacher_classroom_detail, name='teacher_classroom_detail'),
    path("progress/", views.progress_page, name="progress_page"),
    path("progress/api/", views.get_class_progress, name="get_class_progress"),
    path('', views.main, name='base'),
    path('home/', views.home, name='home'),
    path('logout/', views.custom_logout, name='logout'),
    path("create_classroom/", views.create_classroom, name="create_classroom"),
    path("edit-class/<int:class_id>/", views.edit_classroom, name="edit_classroom"),
    path("join-class/<str:unique_code>/", views.join_classroom, name="join_classroom"),
    path("classrooms/", views.classroom_list, name="classroom_list"),
    path("get-user-classes/", views.get_user_classes, name="get_user_classes"),
    path("get-csrf-token/", views.get_csrf_token, name="get_csrf_token"),
    path("view-classroom/<str:class_code>/", views.view_classroom, name="view_classroom"), 
    path("delete-account/", views.delete_account, name="delete_account"),
    path('api/user-profile/', views.get_user_profile, name='get_user_profile'),
    path("join_class/", views.join_class, name="join_class"),
    path("get_joined_classes/", views.get_joined_classes, name="get_joined_classes"),
    path("leave-class/", views.leave_class, name="leave_class"),
    path('leave-class/<str:class_code>/', views.leave_class, name='leave_classroom'),
    path('classroom/<int:classroom_id>/add_work/', views.add_classwork, name='add_classwork'),
    path('classroom/<int:classroom_id>/view_work/', views.view_classwork, name='view_classwork'),
    path('api/get_class_students/<str:class_code>/', views.get_class_students, name='get_class_students'),
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("api/chatbot/", views.chatbot_api, name="chatbot_api"),
    path('delete-classwork/', views.delete_classwork, name='delete_classwork'),
    path('upload-work/', views.upload_student_work, name='upload_student_work'),
    path("delete-classroom/", views.delete_classroom, name="delete_classroom"),
    path('fetch-student-work/', views.fetch_student_work, name='fetch_student_work'),
    path('profile/', views.profile_view, name='profile'),
    path('submit-review/', views.submit_testimonial, name='submit_review'),

]


