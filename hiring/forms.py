from django import forms
from django.db.models import Q

from hiring.models import Candidate, JobOpening, Skill


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ["name"]

    def clean_name(self):
        # The database constraint is on Lower("name"), which Django reports as a
        # form-wide error. Checking here puts the error next to the name field.
        name = self.cleaned_data["name"]
        duplicates = Skill.objects.filter(name__iexact=name).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A skill with this name already exists.")
        return name


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = [
            "first_name",
            "last_name",
            "email",
            "phone",
            "source",
            "source_details",
            "resume_url",
        ]

    def clean_email(self):
        # Same reason as SkillForm.clean_name: keep the error on the email field.
        email = self.cleaned_data["email"]
        duplicates = Candidate.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A candidate with this email already exists.")
        return email


class JobOpeningForm(forms.ModelForm):
    class Meta:
        model = JobOpening
        fields = ["title", "department", "location", "employment_type", "description", "skills"]
        widgets = {"skills": forms.CheckboxSelectMultiple(attrs={"class": "checkbox checkbox-sm"})}


class CandidateFilterForm(forms.Form):
    STATUS_ACTIVE = "active"
    STATUS_CHOICES = [(STATUS_ACTIVE, "Active"), ("archived", "Archived"), ("all", "All")]

    q = forms.CharField(required=False, label="Search")
    source = forms.ChoiceField(
        required=False, choices=[("", "All sources"), *Candidate.Source.choices]
    )
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)

    def filter(self, queryset):
        data = self.cleaned_data if self.is_valid() else {}
        if q := data.get("q", "").strip():
            queryset = queryset.filter(
                Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q)
            )
        if source := data.get("source"):
            queryset = queryset.filter(source=source)
        status = data.get("status") or self.STATUS_ACTIVE
        if status == self.STATUS_ACTIVE:
            queryset = queryset.filter(archived=False)
        elif status == "archived":
            queryset = queryset.filter(archived=True)
        return queryset


class JobFilterForm(forms.Form):
    STATUS_OPEN = JobOpening.Status.OPEN
    STATUS_CHOICES = [*JobOpening.Status.choices, ("all", "All")]

    q = forms.CharField(required=False, label="Search")
    status = forms.ChoiceField(required=False, choices=STATUS_CHOICES)

    def filter(self, queryset):
        data = self.cleaned_data if self.is_valid() else {}
        if q := data.get("q", "").strip():
            queryset = queryset.filter(Q(title__icontains=q) | Q(department__icontains=q))
        status = data.get("status") or self.STATUS_OPEN
        if status != "all":
            queryset = queryset.filter(status=status)
        return queryset
