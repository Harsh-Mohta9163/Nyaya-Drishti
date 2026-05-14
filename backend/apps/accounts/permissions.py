"""Department-scoping for DRF views.

Single source of truth for the rule: "if you're not a global role,
you only see cases tagged to your department."
"""
from django.db.models import Q


# Roles that bypass dept-scoped filtering entirely.
GLOBAL_ACCESS_ROLES = {"central_law", "state_monitoring"}

# Roles authorised to verify (approve/edit/reject) an Action Plan.
# The workflow doc names the Head of the Legal Cell as the mandatory
# human-in-the-loop. Central Law has override authority on anything.
# Legacy demo roles (reviewer/dept_head/legal_advisor) kept so older
# users from before the statutory taxonomy still function.
VERIFIER_ROLES = {
    "head_legal_cell",
    "central_law",
    "reviewer", "dept_head", "legal_advisor",  # legacy
}


def user_has_global_access(user) -> bool:
    return bool(user and user.is_authenticated and user.role in GLOBAL_ACCESS_ROLES)


def user_can_verify(user) -> bool:
    """Only HLC + Central Law (+ legacy reviewer roles) may approve/edit Action Plans."""
    return bool(user and user.is_authenticated and user.role in VERIFIER_ROLES)


class DepartmentScopedQuerysetMixin:
    """Mixin for ListAPIView / RetrieveAPIView that filters by request.user.department.

    Behavior:
      - Anonymous user → empty queryset.
      - Global role (CENTRAL_LAW / STATE_MONITORING):
          * If `?department=CODE` query param is set → filter to that dept.
          * Else → no filter (sees everything).
      - Dept-scoped user with department_id set →
          filter to primary_department == user.department
          OR secondary_departments contains user.department.
      - Dept-scoped user with no department → empty queryset (misconfigured user).

    Override `department_field` on the view if the model uses a different FK name
    (default `"primary_department"`).
    """

    department_field = "primary_department"
    secondary_department_field = "secondary_departments"

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if not user.is_authenticated:
            return qs.none()

        if user.role in GLOBAL_ACCESS_ROLES:
            code = (self.request.query_params.get("department") or "").strip().upper()
            if code:
                return qs.filter(**{f"{self.department_field}__code": code}).distinct()
            return qs

        if not user.department_id:
            return qs.none()

        return qs.filter(
            Q(**{self.department_field: user.department_id})
            | Q(**{self.secondary_department_field: user.department_id})
        ).distinct()
