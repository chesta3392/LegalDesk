from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CaseForm, HearingForm, CaseNoteForm, DocumentForm, TaskForm, FeeRecordForm, SignupForm
from .models import Case, Hearing, CaseNote, Document, Task, FeeRecord


def is_client(user):
    return hasattr(user, "clientprofile")


def home(request):
    """Public marketing landing page. Signed-in users are sent straight to their workspace."""
    if request.user.is_authenticated:
        return redirect("client_portal" if is_client(request.user) else "dashboard")
    return render(request, "landing.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("username"), password=request.POST.get("password"))
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}.")
            return redirect("client_portal" if is_client(user) else "dashboard")
        messages.error(request, "Invalid username or password.")
    return render(request, "login.html")


def signup_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    if request.method == "POST":
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to LegalDesk, {user.first_name or user.username}!")
            return redirect("client_portal" if is_client(user) else "dashboard")
    else:
        form = SignupForm(initial={"role": "ADVOCATE"})
    return render(request, "signup.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("home")


@login_required
def dashboard(request):
    if is_client(request.user):
        return redirect("client_portal")

    cases = Case.objects.filter(advocate=request.user)
    today = timezone.localdate()

    context = {
        "cases": cases[:8],
        "case_count": cases.count(),
        "active_count": cases.filter(status="ACTIVE").count(),
        "hearing_today_count": Hearing.objects.filter(case__advocate=request.user, hearing_date=today).count(),
        "task_count": Task.objects.filter(assigned_to=request.user, completed=False).count(),
        "task_overdue_count": Task.objects.filter(
            assigned_to=request.user, completed=False, due_date__lt=today
        ).count(),
        "pending_fees": sum(
            (x.amount for x in FeeRecord.objects.filter(case__advocate=request.user, paid=False)), 0
        ),
        "upcoming": Hearing.objects.filter(
            case__advocate=request.user, hearing_date__gte=today
        ).select_related("case").order_by("hearing_date")[:5],
        "recent_tasks": Task.objects.filter(assigned_to=request.user, completed=False).order_by("due_date")[:5],
    }
    return render(request, "dashboard.html", context)


@login_required
def case_list(request):
    if is_client(request.user):
        return redirect("client_portal")
    qs = Case.objects.filter(advocate=request.user).select_related("client__user")
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "").strip()
    if q:
        qs = qs.filter(
            Q(case_number__icontains=q)
            | Q(title__icontains=q)
            | Q(client__user__first_name__icontains=q)
            | Q(client__user__last_name__icontains=q)
        )
    if status:
        qs = qs.filter(status=status)
    return render(request, "case_list.html", {
        "cases": qs, "q": q, "status": status, "status_choices": Case.STATUS_CHOICES,
    })


@login_required
def case_create(request):
    if is_client(request.user):
        return redirect("client_portal")
    form = CaseForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        case = form.save(commit=False)
        case.advocate = request.user
        case.save()
        messages.success(request, f"Case {case.case_number} created successfully.")
        return redirect("case_detail", case_id=case.id)
    return render(request, "form.html", {"form": form, "title": "Add New Case", "back_url": "case_list"})


@login_required
def case_detail(request, case_id):
    case = get_object_or_404(Case, id=case_id)
    if is_client(request.user):
        if case.client.user != request.user:
            return render(request, "403.html", status=403)
    elif case.advocate != request.user:
        return render(request, "403.html", status=403)

    hearings = case.hearings.all()
    client_view = is_client(request.user)
    if client_view:
        hearings = hearings.filter(client_visible=True)
        documents = case.documents.filter(client_visible=True)
        notes = []
        tasks = []
    else:
        documents = case.documents.all()
        notes = case.notes.all()
        tasks = case.tasks.all()

    return render(request, "case_detail.html", {
        "case": case, "hearings": hearings, "documents": documents, "notes": notes,
        "tasks": tasks, "client_view": client_view,
    })


def _advocate_case_or_403(request, case_id):
    return get_object_or_404(Case, id=case_id, advocate=request.user)


@login_required
def hearing_create(request, case_id):
    case = _advocate_case_or_403(request, case_id)
    form = HearingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        h = form.save(commit=False)
        h.case = case
        h.save()
        messages.success(request, "Hearing added.")
        return redirect("case_detail", case_id=case.id)
    return render(request, "form.html", {"form": form, "title": f"Add Hearing — {case.case_number}", "back_url": "case_detail", "back_arg": case.id})


@login_required
def note_create(request, case_id):
    case = _advocate_case_or_403(request, case_id)
    form = CaseNoteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        n = form.save(commit=False)
        n.case = case
        n.author = request.user
        n.save()
        messages.success(request, "Internal note saved.")
        return redirect("case_detail", case_id=case.id)
    return render(request, "form.html", {"form": form, "title": f"Add Internal Note — {case.case_number}", "back_url": "case_detail", "back_arg": case.id})


@login_required
def document_create(request, case_id):
    case = _advocate_case_or_403(request, case_id)
    form = DocumentForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        d = form.save(commit=False)
        d.case = case
        d.uploaded_by = request.user
        d.save()
        messages.success(request, "Document uploaded.")
        return redirect("case_detail", case_id=case.id)
    return render(request, "form.html", {"form": form, "title": f"Upload Document — {case.case_number}", "back_url": "case_detail", "back_arg": case.id, "is_file_form": True})


@login_required
def task_list(request):
    if is_client(request.user):
        return redirect("client_portal")
    tasks = Task.objects.filter(assigned_to=request.user).select_related("case").order_by("completed", "due_date")
    return render(request, "task_list.html", {
        "tasks": tasks,
        "open_count": tasks.filter(completed=False).count(),
        "today": timezone.localdate(),
    })


@login_required
def task_create(request):
    if is_client(request.user):
        return redirect("client_portal")
    form = TaskForm(request.POST or None, advocate=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Task created.")
        return redirect("task_list")
    return render(request, "form.html", {"form": form, "title": "Create Task", "back_url": "task_list"})


@login_required
@require_POST
def task_toggle(request, task_id):
    task = get_object_or_404(Task, id=task_id, assigned_to=request.user)
    task.completed = not task.completed
    task.save(update_fields=["completed"])
    return redirect(request.META.get("HTTP_REFERER") or "task_list")


@login_required
def fee_list(request):
    if is_client(request.user):
        return redirect("client_portal")
    fees = FeeRecord.objects.filter(case__advocate=request.user).select_related("case").order_by("-created_at")
    return render(request, "fee_list.html", {
        "fees": fees,
        "total_billed": sum((f.amount for f in fees), 0),
        "total_pending": sum((f.amount for f in fees if not f.paid), 0),
    })


@login_required
def fee_create(request):
    if is_client(request.user):
        return redirect("client_portal")
    form = FeeRecordForm(request.POST or None, advocate=request.user)
    if request.method == "POST" and form.is_valid():
        fee = form.save(commit=False)
        if fee.case.advocate != request.user:
            return render(request, "403.html", status=403)
        fee.save()
        messages.success(request, "Fee record added.")
        return redirect("fee_list")
    return render(request, "form.html", {"form": form, "title": "Add Fee Record", "back_url": "fee_list"})


@login_required
@require_POST
def fee_toggle(request, fee_id):
    fee = get_object_or_404(FeeRecord, id=fee_id, case__advocate=request.user)
    fee.paid = not fee.paid
    fee.save(update_fields=["paid"])
    return redirect(request.META.get("HTTP_REFERER") or "fee_list")


@login_required
def client_portal(request):
    if not is_client(request.user):
        return redirect("dashboard")
    cases = Case.objects.filter(client__user=request.user).select_related("advocate")
    return render(request, "client_portal.html", {"cases": cases})


def error_403(request, exception=None):
    return render(request, "403.html", status=403)


def error_404(request, exception=None):
    return render(request, "404.html", status=404)
