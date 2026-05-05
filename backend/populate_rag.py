import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.action_plans.services.rag_engine import HybridRAGEngine

documents = [
    {
        "text": "The impugned order is set aside, and the appeals are allowed. The State shall reinstate the petitioner within 60 days.",
        "metadata": {"case_number": "WA No. 101 of 2024", "outcome": "Compliance ordered", "summary": "Similar appeal allowed. Department ordered to comply within 60 days."}
    },
    {
        "text": "Appeals are allowed in the aforesaid terms. Cost of Rs 25000 to be paid.",
        "metadata": {"case_number": "WA No. 202 of 2023", "outcome": "Compliance with penalty", "summary": "Appeal allowed but with costs imposed on the State for delay."}
    },
    {
        "text": "The impugned order is quashed. Respondent directed to issue NOC.",
        "metadata": {"case_number": "WA No. 303 of 2023", "outcome": "Contempt proceedings", "summary": "State failed to comply with the allowed appeal. Contempt was filed after 90 days."}
    }
]

engine = HybridRAGEngine()
engine.add_documents(documents)
print("Successfully populated RAG ChromaDB vector store with 3 historical cases.")
