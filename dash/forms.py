from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User

from menus.models import Dish, Allergen, Category, Subcategory, Menu_Type
from .models import AppSettings


# -------------------------
# Dish form
# -------------------------
class DishForm(forms.ModelForm):
    allergens = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )

    class Meta:
        model = Dish
        fields = [
            "name",
            "description",
            "allergens",
            "image",
            "status",
            "kcal",
            "slug",
            "menu_type",
            "category",
            "subcategory",
            # new dietary flags
            "is_vegan",
            "is_vegetarian",
            # future product linkage
            "supplier_name",
            "supplier_code",
            "product_barcode",
            "external_product_url",
        ]


# -------------------------
# Reason for change (used in confirmation step)
# -------------------------
class DishChangeReasonForm(forms.Form):
    reason = forms.CharField(
        required=True,
        label="Reason for change",
        widget=forms.TextInput(
            attrs={
                "placeholder": "E.g. Supplier changed ingredient / recipe updated",
            }
        ),
    )


# -------------------------
# Authentication
# -------------------------
class CustomLoginForm(AuthenticationForm):
    pass


# -------------------------
# Import form
# -------------------------
class ImportForm(forms.Form):
    file = forms.FileField(
        label="Select a CSV or JSON file",
        help_text="File should contain dish data for bulk upload/update.",
    )


# -------------------------
# User management forms (superuser only)
# -------------------------
class UserCreateForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            self.add_error("password2", "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name", "is_active"]


# -------------------------
# Branding form (Menu_Type)
# -------------------------
class MenuTypeBrandingForm(forms.ModelForm):
    class Meta:
        model = Menu_Type
        fields = [
            "name",
            "logo",
            "background_image",
            "primary_color",
            "secondary_color",
            "accent_color",
            "text_color",
            "background_color",
            "font_family",
        ]


# -------------------------
# App settings form (feature toggles)
# -------------------------
class AppSettingsForm(forms.ModelForm):
    class Meta:
        model = AppSettings
        fields = [
            "enable_nutrition",
            "enable_vegan_flags",
            "enable_product_fields",
            "enable_audit_log",
        ]
        widgets = {
            "enable_nutrition": forms.CheckboxInput(),
            "enable_vegan_flags": forms.CheckboxInput(),
            "enable_product_fields": forms.CheckboxInput(),
            "enable_audit_log": forms.CheckboxInput(),
        }
        labels = {
            "enable_nutrition": "Enable nutrition fields",
            "enable_vegan_flags": "Show vegan/vegetarian markers",
            "enable_product_fields": "Enable supplier/barcode fields",
            "enable_audit_log": "Require change reasons & keep an audit log",
        }
