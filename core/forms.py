from django import forms

from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("name", "email", "phone", "subject", "message")
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Ton nom", "autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"placeholder": "ton.email@domaine.com", "autocomplete": "email"}),
            "phone": forms.TextInput(
                attrs={
                    "placeholder": "243 812 345 678",
                    "autocomplete": "tel",
                    "inputmode": "tel",
                }
            ),
            "subject": forms.TextInput(attrs={"placeholder": "Sujet du message"}),
            "message": forms.Textarea(attrs={"placeholder": "Parle-moi du projet, du stage, de l'idée…", "rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["phone"].required = True
        for field in self.fields.values():
            field.widget.attrs["class"] = "field-input"
            field.label = ""
