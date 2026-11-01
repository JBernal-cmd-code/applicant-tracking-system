from django import forms

from hiring.models import Skill


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
