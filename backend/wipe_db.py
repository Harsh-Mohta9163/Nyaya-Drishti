"""Wipe ALL case-related data from the database. Leaves ChromaDB untouched."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
django.setup()

from django.db import connection
from apps.cases.models import Case, Judgment, Citation
from apps.action_plans.models import ActionPlan
from apps.reviews.models import ReviewLog

# Delete in correct FK order
print("Deleting ReviewLogs...")
ReviewLog.objects.all().delete()
print("Deleting ActionPlans...")
ActionPlan.objects.all().delete()
print("Deleting Citations...")
Citation.objects.all().delete()
print("Deleting Judgments...")
Judgment.objects.all().delete()
print("Deleting Cases...")
Case.objects.all().delete()

# Verify
print(f"\nCases remaining: {Case.objects.count()}")
print(f"Judgments remaining: {Judgment.objects.count()}")
print(f"ActionPlans remaining: {ActionPlan.objects.count()}")
print("✅ Database wiped clean. ChromaDB untouched.")
