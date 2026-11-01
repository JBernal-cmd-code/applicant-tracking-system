from django.contrib import messages
from django.contrib.auth.views import LoginView


class StaffLoginView(LoginView):
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Welcome back, {form.get_user().get_username()}.")
        return response
