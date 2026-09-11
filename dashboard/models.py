from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone


class AdvocateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bar_registration = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    law_firm = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Case(models.Model):
    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("HEARING", "Hearing"),
        ("PENDING", "Pending"),
        ("CLOSED", "Closed"),
    ]
    advocate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="advocate_cases")
    client = models.ForeignKey(ClientProfile, on_delete=models.PROTECT, related_name="cases")
    case_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    case_type = models.CharField(max_length=100)
    court = models.CharField(max_length=255)
    opposite_party = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case_number} - {self.title}"

    def get_absolute_url(self):
        return reverse("case_detail", args=[self.id])

    @property
    def next_hearing(self):
        return self.hearings.filter(hearing_date__gte=timezone.localdate()).order_by("hearing_date").first()

    @property
    def status_css(self):
        return {
            "ACTIVE": "green",
            "HEARING": "warn",
            "PENDING": "blue",
            "CLOSED": "muted-badge",
        }.get(self.status, "")

    @property
    def open_task_count(self):
        return self.tasks.filter(completed=False).count()

    @property
    def total_fees(self):
        return sum((f.amount for f in self.fees.all()), 0)

    @property
    def pending_fees(self):
        return sum((f.amount for f in self.fees.filter(paid=False)), 0)


class Hearing(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="hearings")
    hearing_date = models.DateField()
    purpose = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    client_visible = models.BooleanField(default=True)

    class Meta:
        ordering = ["hearing_date"]

    def __str__(self):
        return f"{self.case.case_number} — {self.hearing_date}"

    @property
    def is_upcoming(self):
        return self.hearing_date >= timezone.localdate()


class CaseNote(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    note = models.TextField()
    private = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Document(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="documents")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="case_documents/")
    client_visible = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    @property
    def filename(self):
        return self.file.name.rsplit("/", 1)[-1]


class Task(models.Model):
    PRIORITY_CHOICES = [("LOW", "Low"), ("MEDIUM", "Medium"), ("HIGH", "High")]

    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="tasks", null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="MEDIUM")
    due_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["completed", "due_date"]

    def __str__(self):
        return self.title

    @property
    def is_overdue(self):
        return bool(self.due_date and not self.completed and self.due_date < timezone.localdate())


class FeeRecord(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE, related_name="fees")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255, blank=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.case.case_number} — ₹{self.amount}"
