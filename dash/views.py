from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

import json
import csv
import ast
from io import TextIOWrapper, StringIO
import pandas as pd

from menus.models import Dish, Allergen, Menu_Type, Category, Subcategory, DishChangeLog
from .forms import (
    DishForm,
    CustomLoginForm,
    ImportForm,
    UserCreateForm,
    UserUpdateForm,
    MenuTypeBrandingForm,
    DishChangeReasonForm,
)

# Canonical gluten group for CSV conversion helper
GLUTEN_CANONICAL = "Cereals containing gluten"
GLUTEN_ALIAS_COLS = {
    "wheat",
    "barley",
    "rye",
    "oats",
    "spelt",
    "kamut",
    "gluten",  # in case someone literally names the column "Gluten"
}

# ---------------------------------------------
# 0. Superuser-only mixin
# ---------------------------------------------
class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You do not have permission to access that area.")
        return redirect("dashboard_home")


# ---------------------------------------------
# 1. Authentication and Dashboard Home
# ---------------------------------------------
def custom_login(request):
    if request.user.is_authenticated:
        return redirect("dashboard_home")

    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Welcome, %s!" % user.username)
            return redirect("dashboard_home")
        messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()

    return render(
        request,
        "dash/login.html",
        {"form": form, "page_title": "Secure Login"},
    )


def custom_logout(request):
    """Logs out the user and redirects to the home page."""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("index")


@login_required
def dashboard_home(request):
    context = {
        "active_dishes": Dish.objects.filter(status="active").count(),
        "inactive_dishes": Dish.objects.filter(status="inactive").count(),
        "archive_dishes": Dish.objects.filter(status="archive").count(),
        "page_title": "Admin Dashboard",
    }
    return render(request, "dash/dashboard_home.html", context)


# -----------------------------------------------------------------
# 2. Dish CRUD Views
# -----------------------------------------------------------------
class DishListView(LoginRequiredMixin, ListView):
    model = Dish
    template_name = "dash/dish_list.html"
    context_object_name = "dishes"
    ordering = ["name"]
    paginate_by = 10

    def get_queryset(self):
        queryset = self.model.objects.all()

        status_filter = self.request.GET.get("status")
        if status_filter in ["active", "inactive", "archive"]:
            queryset = queryset.filter(status=status_filter)

        query = self.request.GET.get("q")
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(category__name__icontains=query)
                | Q(menu_type__name__icontains=query)
            ).distinct()

        return queryset.order_by(*self.ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        current_status = self.request.GET.get("status", "all")
        context["current_status"] = current_status
        query = self.request.GET.get("q", "")
        context["query"] = query
        context["page_title"] = "Dish List: %s" % current_status.capitalize()
        return context


class DishCreateView(LoginRequiredMixin, CreateView):
    model = Dish
    form_class = DishForm
    template_name = "dash/dish_form.html"
    success_url = reverse_lazy("dish_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Create New Dish"
        return context


class DishUpdateView(LoginRequiredMixin, UpdateView):
    """
    Step 1 of editing a dish:
    - check lockout
    - compute differences
    - store pending data in session
    - show confirmation page (reason required)
    Actual save happens in confirm_dish_changes().
    """

    model = Dish
    form_class = DishForm
    template_name = "dash/dish_form.html"
    success_url = reverse_lazy("dish_list")

    def dispatch(self, request, *args, **kwargs):
        dish = self.get_object()
        if dish.edit_lock_until and timezone.now() < dish.edit_lock_until:
            remaining = dish.edit_lock_until - timezone.now()
            minutes = max(1, int(remaining.seconds / 60))
            messages.error(
                request,
                "This dish is locked for edits for another %d minute(s)." % minutes,
            )
            return redirect("dish_list")
        return super(DishUpdateView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "Edit Dish: %s" % self.object.name
        if "reason_form" not in context:
            context["reason_form"] = DishChangeReasonForm()
        return context

    def form_valid(self, form):
        dish = self.get_object()

        # Build "old" values for changed fields (as strings)
        old_values = {}
        for field in form.changed_data:
            if field in ["menu_type", "allergens"]:
                current_qs = getattr(dish, field).all()
                old_values[field] = ", ".join([str(obj) for obj in current_qs])
            else:
                old_values[field] = str(getattr(dish, field))

        # Build "new" values for display (not stored in session)
        new_values = {}
        for field in form.changed_data:
            value = form.cleaned_data.get(field)
            if field in ["menu_type", "allergens"]:
                if value is None:
                    new_values[field] = ""
                else:
                    new_values[field] = ", ".join([str(obj) for obj in value])
            else:
                new_values[field] = str(value)

        # Store POST data in session in a JSON-serialisable form
        post_data = {}
        for key in self.request.POST.keys():
            values = self.request.POST.getlist(key)
            if len(values) == 1:
                post_data[key] = values[0]
            else:
                post_data[key] = values

        self.request.session["pending_dish_changes"] = {
            "dish_id": dish.id,
            "post_data": post_data,
            "old_values": old_values,
        }
        self.request.session.modified = True

        context = {
            "dish": dish,
            "old_values": old_values,
            "new_values": new_values,
            "reason_form": DishChangeReasonForm(),
            "page_title": "Confirm changes: %s" % dish.name,
        }
        return render(self.request, "dash/dish_confirm_changes.html", context)


@login_required
def confirm_dish_changes(request, pk):
    """
    Step 2 of editing a dish:
    - rebuild form from stored POST data
    - validate reason
    - save dish
    - log changes
    - apply 5-minute edit lock
    """
    dish = get_object_or_404(Dish, pk=pk)
    pending = request.session.get("pending_dish_changes")

    if not pending or pending.get("dish_id") != dish.id:
        messages.error(request, "No pending changes found for this dish.")
        return redirect("dish_list")

    # Build form from stored POST data
    post_data = pending.get("post_data", {})
    form = DishForm(post_data, instance=dish)

    if not form.is_valid():
        # If this somehow fails, clear pending and force re-edit
        try:
            del request.session["pending_dish_changes"]
        except KeyError:
            pass
        messages.error(
            request,
            "The pending change data is no longer valid. Please edit the dish again.",
        )
        return redirect("dish_list")

    if request.method != "POST":
        # Should not happen in normal flow
        messages.error(request, "Please use the confirmation form to save changes.")
        return redirect("dish_list")

    reason_form = DishChangeReasonForm(request.POST)
    if not reason_form.is_valid():
        # Recalculate new_values for display
        old_values = pending.get("old_values", {})
        new_values = {}
        for field, old_val in old_values.items():
            if field in form.fields and field in form.changed_data:
                if field in ["menu_type", "allergens"]:
                    value = form.cleaned_data.get(field) or []
                    new_values[field] = ", ".join([str(obj) for obj in value])
                else:
                    new_values[field] = str(form.cleaned_data.get(field))
            else:
                new_values[field] = old_val

        context = {
            "dish": dish,
            "old_values": old_values,
            "new_values": new_values,
            "reason_form": reason_form,
            "page_title": "Confirm changes: %s" % dish.name,
        }
        return render(request, "dash/dish_confirm_changes.html", context)

    reason = reason_form.cleaned_data["reason"]
    old_values = pending.get("old_values", {})

    # Save dish with new data
    dish = form.save(commit=False)
    dish.last_modified_by = request.user
    dish.last_change_reason = reason
    dish.edit_lock_until = timezone.now() + timedelta(minutes=5)
    dish.save()
    form.save_m2m()

    # Build changes dict for log
    changes = {}
    for field, old_val in old_values.items():
        if field in ["menu_type", "allergens"]:
            current_qs = getattr(dish, field).all()
            new_val = ", ".join([str(obj) for obj in current_qs])
        else:
            new_val = str(getattr(dish, field))
        changes[field] = {"old": old_val, "new": new_val}

    DishChangeLog.objects.create(
        dish=dish,
        changed_by=request.user,
        reason=reason,
        changes=changes or None,
    )

    # Clear pending data
    try:
        del request.session["pending_dish_changes"]
    except KeyError:
        pass

    messages.success(
        request,
        "Changes to '%s' have been saved and logged." % dish.name,
    )
    return redirect("dish_list")


class DishDeleteView(LoginRequiredMixin, DeleteView):
    model = Dish
    template_name = "dash/dish_confirm_delete.html"
    success_url = reverse_lazy("dish_list")


@login_required
def bulk_archive_delete(request):
    if request.method == "POST":
        count = Dish.objects.filter(status="archive").delete()[0]
        messages.success(
            request,
            "%d archived dishes have been permanently deleted." % count,
        )

    return HttpResponseRedirect(reverse_lazy("dish_list"))


class DishChangeLogListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = DishChangeLog
    template_name = "dash/dish_change_log_list.html"
    context_object_name = "logs"
    paginate_by = 50

    def get_queryset(self):
        qs = super(DishChangeLogListView, self).get_queryset().select_related(
            "dish", "changed_by"
        )
        dish_id = self.request.GET.get("dish")
        if dish_id:
            qs = qs.filter(dish_id=dish_id)
        return qs

    def get_context_data(self, **kwargs):
        context = super(DishChangeLogListView, self).get_context_data(**kwargs)
        context["page_title"] = "Dish Change Audit Log"
        context["dishes"] = Dish.objects.all().order_by("name")
        context["selected_dish_id"] = self.request.GET.get("dish", "")
        return context


# -------------------------
# 3. Import View (M2M Logic Updated)
# -------------------------
@login_required
def convert_allergen_csv_view(request):
    """
    Helper endpoint used by the 'Convert allergen CSV' form on the import page.
    - POST: convert uploaded CSV and return a cleaned CSV as a download.
    - GET: bounce back to the import page with an info message.
    """
    if request.method != "POST":
        messages.info(
            request,
            "Please use the form on the import page to convert a CSV file.",
        )
        return redirect("import_data")

    upload = request.FILES.get("file")
    if not upload:
        messages.error(request, "Please choose a CSV file to convert.")
        return redirect("import_data")

    try:
        file_obj = TextIOWrapper(upload.file, encoding="utf-8")
        df = pd.read_csv(file_obj)
    except Exception as e:
        messages.error(request, "Could not read CSV file: %s" % e)
        return redirect("import_data")

    allergen_cols = df.columns[4:25]

    def get_allergens(row):
        allergens = []
        has_gluten = False

        for col in allergen_cols:
            cell = str(row[col])
            if "**" in cell:
                col_clean = col.strip()
                col_lower = col_clean.lower()

                if col_lower in GLUTEN_ALIAS_COLS:
                    has_gluten = True
                else:
                    allergens.append(col_clean)

        if has_gluten and GLUTEN_CANONICAL not in allergens:
            allergens.append(GLUTEN_CANONICAL)

        return ", ".join(allergens) if allergens else ""

    df["allergens"] = df.apply(
        lambda row: get_allergens(row)
        if pd.notna(row.get("name")) and row["name"] != ""
        else "",
        axis=1,
    )

    df_clean = df[df["name"].notna() & (df["name"] != "")]
    df_final = df_clean.drop(columns=allergen_cols, errors="ignore")

    csv_buffer = StringIO()
    df_final.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    response = HttpResponse(csv_data, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="converted_allergens.csv"'
    return response


@login_required
def import_data(request):
    """Handles CSV/JSON file uploads for bulk data import."""

    def process_dish_data(dish_data_list):
        imported_count = 0
        errors = []

        def parse_names(value):
            if isinstance(value, list):
                return [str(n).strip() for n in value if str(n).strip()]

            if not value or not isinstance(value, str):
                return []

            try:
                names = ast.literal_eval(value)
                if isinstance(names, list):
                    return [str(n).strip() for n in names if str(n).strip()]
            except (ValueError, SyntaxError):
                return [n.strip() for n in value.split(",") if n.strip()]
            return []

        def get_m2m_objects(model, field_key, error_msg, row_data, dish_name):
            names = parse_names(row_data.get(field_key))
            instances = []

            for name in names:
                try:
                    instance = model.objects.get(name__iexact=name)
                    instances.append(instance)
                except model.DoesNotExist:
                    errors.append(
                        "Dish '%s': %s '%s' not found. Skipping link."
                        % (dish_name, error_msg, name)
                    )
            return instances

        def get_fk_object(model, field_key, error_msg, row_data, dish_name):
            value = str(row_data.get(field_key)).strip()
            if not value:
                return None

            try:
                instance = model.objects.get(name__iexact=value)
                return instance
            except model.DoesNotExist:
                errors.append(
                    "Dish '%s': %s '%s' not found. Dish will be saved without this link."
                    % (dish_name, error_msg, value)
                )
                return None
            except Exception as e:
                errors.append(
                    "Dish '%s': Error looking up FK %s: %s"
                    % (dish_name, field_key, e)
                )
                return None

        for row in dish_data_list:
            dish_name = row.get("name", "UNKNOWN DISH").strip()
            if not dish_name:
                continue

            menu_type_instances = get_m2m_objects(
                Menu_Type, "menu_type", "Menu Type", row, dish_name
            )
            allergen_instances = get_m2m_objects(
                Allergen, "allergens", "Allergen", row, dish_name
            )
            category_instance = get_fk_object(
                Category, "category", "Category", row, dish_name
            )

            dish_slug = row.get("slug")
            slug_value = dish_slug.strip() if dish_slug and dish_slug.strip() else None

            try:
                dish, created = Dish.objects.update_or_create(
                    name=dish_name,
                    defaults={
                        "status": row.get("status", "inactive"),
                        "kcal": row.get("kcal") if row.get("kcal") else None,
                        "description": row.get("description", ""),
                        "image": row.get(
                            "image",
                            "https://i.ibb.co/7QpKsCX/white-background.jpg",
                        ),
                        "slug": slug_value,
                        "category": category_instance,
                    },
                )
            except Exception as e:
                errors.append(
                    "Dish '%s': Failed to create/update dish: %s" % (dish_name, e)
                )
                continue

            dish.menu_type.set(menu_type_instances)
            dish.allergens.set(allergen_instances)
            imported_count += 1

        return imported_count, errors

    if request.method == "POST":
        form = ImportForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            file_name = uploaded_file.name

            try:
                data_list = []
                if file_name.endswith(".csv"):
                    wrapper = TextIOWrapper(uploaded_file.file, encoding="utf-8")
                    reader = csv.DictReader(wrapper)
                    data_list = list(reader)

                elif file_name.endswith(".json"):
                    data_list = json.load(uploaded_file.file)
                    if not isinstance(data_list, list):
                        messages.error(
                            request, "JSON file must contain a list of objects."
                        )
                        return redirect("import_data")
                else:
                    messages.error(
                        request,
                        "Unsupported file format. Please upload a CSV or JSON file.",
                    )
                    return redirect("import_data")

                count, import_errors = process_dish_data(data_list)

                if count > 0:
                    messages.success(
                        request,
                        "Successfully imported/updated %d dishes from %s."
                        % (count, file_name.split(".")[-1].upper()),
                    )
                if import_errors:
                    messages.warning(
                        request,
                        "Completed with %d errors. First error: %s"
                        % (len(import_errors), import_errors[0]),
                    )
                elif count == 0 and not import_errors:
                    messages.info(
                        request,
                        "File processed, but no dishes were imported or updated.",
                    )

            except Exception as e:
                messages.error(
                    request,
                    "File import failed: An unexpected error occurred: %s" % e,
                )

            return redirect("import_data")

    else:
        form = ImportForm()

    return render(
        request,
        "dash/import_data.html",
        {"form": form, "page_title": "Import Dish Data"},
    )


# -------------------------
# 4. User Management (Superuser only)
# -------------------------
class UserListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = User
    template_name = "dash/user_list.html"
    context_object_name = "users"
    paginate_by = 10

    def get_queryset(self):
        return User.objects.filter(is_superuser=False).order_by("username")

    def get_context_data(self, **kwargs):
        context = super(UserListView, self).get_context_data(**kwargs)
        context["page_title"] = "Manage Users"
        return context


class UserCreateView(LoginRequiredMixin, SuperuserRequiredMixin, CreateView):
    model = User
    form_class = UserCreateForm
    template_name = "dash/user_form.html"
    success_url = reverse_lazy("user_list")

    def get_context_data(self, **kwargs):
        context = super(UserCreateView, self).get_context_data(**kwargs)
        context["page_title"] = "Create New User"
        return context

    def form_valid(self, form):
        messages.success(self.request, "User created successfully.")
        return super(UserCreateView, self).form_valid(form)


class UserUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "dash/user_form.html"
    success_url = reverse_lazy("user_list")

    def get_object(self, queryset=None):
        user = super(UserUpdateView, self).get_object(queryset)
        if user.is_superuser:
            messages.error(
                self.request,
                "You cannot edit the main admin account here.",
            )
            raise PermissionError("Attempted to edit superuser.")
        return user

    def get_context_data(self, **kwargs):
        context = super(UserUpdateView, self).get_context_data(**kwargs)
        context["page_title"] = "Edit User: %s" % self.object.username
        return context

    def form_valid(self, form):
        messages.success(self.request, "User updated successfully.")
        return super(UserUpdateView, self).form_valid(form)


class UserDeleteView(LoginRequiredMixin, SuperuserRequiredMixin, DeleteView):
    model = User
    template_name = "dash/user_confirm_delete.html"
    success_url = reverse_lazy("user_list")

    def get_object(self, queryset=None):
        user = super(UserDeleteView, self).get_object(queryset)
        if user.is_superuser:
            messages.error(
                self.request,
                "You cannot delete the main admin account.",
            )
            raise PermissionError("Attempted to delete superuser.")
        return user

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj == request.user:
            messages.error(request, "You cannot delete your own account.")
            return redirect("user_list")
        messages.success(request, "User '%s' deleted." % obj.username)
        return super(UserDeleteView, self).delete(request, *args, **kwargs)


# -------------------------
# 5. Branding Management (Superuser only)
# -------------------------
class BrandingListView(LoginRequiredMixin, SuperuserRequiredMixin, ListView):
    model = Menu_Type
    template_name = "dash/branding_list.html"
    context_object_name = "menu_types"
    paginate_by = 50

    def get_context_data(self, **kwargs):
        context = super(BrandingListView, self).get_context_data(**kwargs)
        context["page_title"] = "Branding & Themes"
        return context


class BrandingUpdateView(LoginRequiredMixin, SuperuserRequiredMixin, UpdateView):
    model = Menu_Type
    form_class = MenuTypeBrandingForm
    template_name = "dash/branding_form.html"
    success_url = reverse_lazy("branding_list")

    def get_context_data(self, **kwargs):
        context = super(BrandingUpdateView, self).get_context_data(**kwargs)
        context["page_title"] = "Edit Branding: %s" % self.object.name
        return context

    def form_valid(self, form):
        messages.success(self.request, "Branding updated successfully.")
        return super(BrandingUpdateView, self).form_valid(form)
