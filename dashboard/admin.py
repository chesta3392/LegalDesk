from django.contrib import admin
from .models import AdvocateProfile, ClientProfile, Case, Hearing, CaseNote, Document, Task, FeeRecord


@admin.register(AdvocateProfile)
class AdvocateProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "bar_registration", "phone", "law_firm")
    search_fields = ("user__username", "user__first_name", "user__last_name")


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name")


class HearingInline(admin.TabularInline):
    model = Hearing
    extra = 0


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 0


@admin.register(Case)
class CaseAdmin(admin.ModelAdmin):
    list_display = ("case_number", "title", "client", "advocate", "status", "court", "created_at")
    list_filter = ("status", "case_type")
    search_fields = ("case_number", "title", "client__user__first_name", "client__user__last_name")
    inlines = [HearingInline, DocumentInline]


@admin.register(Hearing)
class HearingAdmin(admin.ModelAdmin):
    list_display = ("case", "hearing_date", "purpose", "client_visible")
    list_filter = ("client_visible",)


@admin.register(CaseNote)
class CaseNoteAdmin(admin.ModelAdmin):
    list_display = ("case", "author", "private", "created_at")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("case", "title", "uploaded_by", "client_visible", "uploaded_at")


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "case", "assigned_to", "priority", "due_date", "completed")
    list_filter = ("priority", "completed")


@admin.register(FeeRecord)
class FeeRecordAdmin(admin.ModelAdmin):
    list_display = ("case", "amount", "paid", "created_at")
    list_filter = ("paid",)
