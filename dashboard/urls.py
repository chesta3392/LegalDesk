from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.logout_view, name="logout"),

    path("dashboard/", views.dashboard, name="dashboard"),

    path("cases/", views.case_list, name="case_list"),
    path("cases/add/", views.case_create, name="case_create"),
    path("cases/<int:case_id>/", views.case_detail, name="case_detail"),
    path("cases/<int:case_id>/hearing/add/", views.hearing_create, name="hearing_create"),
    path("cases/<int:case_id>/note/add/", views.note_create, name="note_create"),
    path("cases/<int:case_id>/document/add/", views.document_create, name="document_create"),

    path("tasks/", views.task_list, name="task_list"),
    path("tasks/add/", views.task_create, name="task_create"),
    path("tasks/<int:task_id>/toggle/", views.task_toggle, name="task_toggle"),

    path("fees/", views.fee_list, name="fee_list"),
    path("fees/add/", views.fee_create, name="fee_create"),
    path("fees/<int:fee_id>/toggle/", views.fee_toggle, name="fee_toggle"),

    path("client/portal/", views.client_portal, name="client_portal"),
]
