# forms.py
import re

from django import forms

from utils.enums import ActivityType

from .models.fill_in_the_blank import FillInTheBlankActivity

BLANK_PATTERN = re.compile(r"\[\[(.+?)\]\]")


class FillInTheBlankActivityForm(forms.ModelForm):
    authoring_text = forms.CharField(
        label="Texto (usa [[respuesta]] para el hueco)",
        widget=forms.Textarea(attrs={"rows": 6}),
        help_text="Ej: 'La capital de Francia es [[París]]'.",
        required=True,
    )

    class Meta:
        model = FillInTheBlankActivity
        fields = (
            "title",
            "instructions",
            "difficulty",
            "feedback",
            "points",
            "module",
            "authoring_text",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inst = getattr(self, "instance", None)
        if inst and inst.pk and inst.text and inst.correct_answers:
            parts = inst.text.split("{{blank}}")
            rebuilt = []
            for i, part in enumerate(parts):
                rebuilt.append(part)
                if str(i) in inst.correct_answers:
                    ans = inst.correct_answers[str(i)]
                    rebuilt.append(f"[[{ans}]]")
            self.fields["authoring_text"].initial = "".join(rebuilt)

    def clean(self):
        cleaned = super().clean()
        src = cleaned.get("authoring_text") or ""
        if not src:
            raise forms.ValidationError(
                "Debes ingresar el texto con al menos un [[hueco]]."
            )

        answers = {}
        idx = 0

        def replace_match(m):
            nonlocal idx
            raw = m.group(1).strip()
            if not raw:
                raise forms.ValidationError("Se encontró [[ ]] vacío.")
            if "|" in raw:
                raise forms.ValidationError("Solo una respuesta por hueco. Quita '|'.")
            answers[str(idx)] = raw
            idx += 1
            return "{{blank}}"

        normalized_text = BLANK_PATTERN.sub(replace_match, src)
        if idx == 0:
            raise forms.ValidationError(
                "Incluye al menos un hueco usando [[respuesta]]."
            )

        cleaned["text"] = normalized_text
        cleaned["correct_answers"] = answers
        return cleaned

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.text = self.cleaned_data["text"]
        instance.correct_answers = self.cleaned_data["correct_answers"]
        instance.type = ActivityType.FILL
        if commit:
            instance.save()
            self.save_m2m()
        return instance
