from django import forms

from users.models import User

from .models import Person, Student


class PersonAdminForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = "__all__"

    existing_user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        label="Usuario existente (buscar por username)",
    )

    new_username = forms.CharField(required=False, label="Nuevo username")
    new_email = forms.EmailField(required=False, label="Nuevo email")
    new_password = forms.CharField(
        required=False, label="Nuevo password", widget=forms.PasswordInput
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.user:
            self.fields["existing_user"].initial = self.instance.user

    def clean(self):
        cleaned_data = super().clean()
        existing_user = cleaned_data.get("existing_user")
        new_username = cleaned_data.get("new_username")
        new_email = cleaned_data.get("new_email")
        new_password = cleaned_data.get("new_password")

        if existing_user and (new_username or new_email or new_password):
            raise forms.ValidationError(
                "No puedes seleccionar un usuario existente y crear uno nuevo al mismo tiempo."  # noqa: E501
            )

        if not existing_user and not new_username:
            raise forms.ValidationError(
                "Debes seleccionar un usuario existente o crear uno nuevo."
            )

        return cleaned_data

    def save(self, commit=True):
        existing_user = self.cleaned_data.get("existing_user")
        if existing_user:
            self.instance.user = existing_user
        else:
            user = User.objects.create_user(
                username=self.cleaned_data["new_username"],
                email=self.cleaned_data.get("new_email", ""),
                password=self.cleaned_data.get("new_password", None),
            )
            self.instance.user = user
        return super().save(commit)


class StudentAdminForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = "__all__"

    search_fields = (
        "person__first_name",
        "person__last_name",
        "person__user__email",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        f = self.fields.get("active_course")
        if f:
            f.disabled = True
            f.help_text = "Se calcula automáticamente y no puede modificarse."
