from django import forms
from django.contrib.auth.models import User
from .models import Case, Hearing, CaseNote, Document, Task, FeeRecord, AdvocateProfile, ClientProfile


class StyledFormMixin:
    """Applies consistent CSS classes to every field's widget automatically."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "checkbox")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "select")
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault("class", "textarea")
                widget.attrs.setdefault("rows", 4)
            elif isinstance(widget, forms.ClearableFileInput):
                widget.attrs.setdefault("class", "file-input")
            else:
                widget.attrs.setdefault("class", "input")
            if field.required and not isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("placeholder", field.label or name.replace("_", " ").title())


class SignupForm(StyledFormMixin, forms.Form):
    ROLE_CHOICES = [("ADVOCATE", "Advocate"), ("CLIENT", "Client")]

    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    first_name = forms.CharField(max_length=100, label="Full name")
    email = forms.EmailField()
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password")
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm password")

    # Advocate-only fields
    law_firm = forms.CharField(max_length=150, required=False, label="Law firm / chambers")
    bar_registration = forms.CharField(max_length=100, required=False, label="Bar registration no.")

    # Client-only fields
    phone = forms.CharField(max_length=20, required=False)
    address = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}), required=False)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1, p2 = cleaned.get("password1"), cleaned.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        if p1 and len(p1) < 8:
            self.add_error("password1", "Password must be at least 8 characters.")
        return cleaned

    def save(self):
        data = self.cleaned_data
        user = User.objects.create_user(
            username=data["username"],
            email=data["email"],
            password=data["password1"],
            first_name=data["first_name"],
        )
        if data["role"] == "ADVOCATE":
            AdvocateProfile.objects.create(
                user=user,
                law_firm=data.get("law_firm", ""),
                bar_registration=data.get("bar_registration", ""),
                phone=data.get("phone", ""),
            )
        else:
            ClientProfile.objects.create(
                user=user,
                phone=data.get("phone", ""),
                address=data.get("address", ""),
            )
        return user


class CaseForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Case
        fields = ["client", "case_number", "title", "case_type", "court", "opposite_party", "status", "description"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class HearingForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Hearing
        fields = ["hearing_date", "purpose", "notes", "client_visible"]
        widgets = {"hearing_date": forms.DateInput(attrs={"type": "date"})}


class CaseNoteForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = CaseNote
        fields = ["note", "private"]


class DocumentForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ["title", "file", "client_visible"]


class TaskForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = Task
        fields = ["case", "assigned_to", "title", "priority", "due_date", "completed"]
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, advocate=None, **kwargs):
        super().__init__(*args, **kwargs)
        if advocate is not None:
            self.fields["case"].queryset = Case.objects.filter(advocate=advocate)
            self.fields["assigned_to"].queryset = User.objects.filter(clientprofile__isnull=True)
            self.fields["assigned_to"].initial = advocate.pk


class FeeRecordForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = FeeRecord
        fields = ["case", "amount", "description", "paid"]

    def __init__(self, *args, advocate=None, **kwargs):
        super().__init__(*args, **kwargs)
        if advocate is not None:
            self.fields["case"].queryset = Case.objects.filter(advocate=advocate)
