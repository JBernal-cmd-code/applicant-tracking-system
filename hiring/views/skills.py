from django.contrib import messages
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render

from hiring.forms import SkillForm
from hiring.models import Skill


def skill_list(request):
    # Meta.ordering is ignored on aggregated queries, so order explicitly.
    skills = Skill.objects.annotate(job_count=Count("job_openings")).order_by("name")
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
