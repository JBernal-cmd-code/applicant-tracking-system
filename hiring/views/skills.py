from django.contrib import messages
from django.db.models import IntegerField, Value
from django.shortcuts import get_object_or_404, redirect, render

from hiring.forms import SkillForm
from hiring.models import Skill


def skill_list(request):
    # Job openings arrive in Phase 4; this becomes Count("job_openings") then.
    skills = Skill.objects.annotate(job_count=Value(0, output_field=IntegerField()))
    return render(request, "hiring/skill_list.html", {"skills": skills})


def skill_create(request):
    form = SkillForm(request.POST or None)
    if form.is_valid():
        skill = form.save()
        messages.success(request, f"Skill “{skill}” added.")
        return redirect("hiring:skill_list")
    return render(request, "hiring/skill_form.html", {"form": form})


def skill_edit(request, pk):
    skill = get_object_or_404(Skill, pk=pk)
    form = SkillForm(request.POST or None, instance=skill)
    if form.is_valid():
        form.save()
        messages.success(request, f"Skill “{skill}” saved.")
        return redirect("hiring:skill_list")
    return render(request, "hiring/skill_form.html", {"form": form, "skill": skill})
