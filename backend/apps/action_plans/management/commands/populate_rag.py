"""
Django management command to bulk-load Karnataka HC judgments into the RAG corpus.

USAGE:
  # Load from a directory of PDF files
  python manage.py populate_rag --source pdfs --path /path/to/pdfs/

  # Load from a directory of plain text files
  python manage.py populate_rag --source texts --path /path/to/texts/

  # Load from Indian Kanoon search results (auto-download)
  python manage.py populate_rag --source indiankanoon --query "Karnataka High Court 2024" --count 50

  # Load the built-in sample corpus
  python manage.py populate_rag --source samples
"""
import glob
import logging
import os
import time

from django.core.management.base import BaseCommand

from apps.action_plans.services.rag_engine import HybridRAGEngine

logger = logging.getLogger(__name__)


# Built-in sample corpus of Karnataka HC operative orders
BUILT_IN_SAMPLES = [
    {
        "text": "The writ petition is allowed. The impugned order dated 15.06.2023 passed by the Revenue Department is hereby quashed. The respondent-State is directed to pay compensation of Rs. 25,00,000/- to the petitioner within 60 days. The Secretary, Revenue Department shall ensure compliance, failing which contempt proceedings shall be initiated.",
        "metadata": {"case_number": "WP 9876/2023", "court": "Karnataka HC", "type": "Land Acquisition", "year": "2023"},
    },
    {
        "text": "The appeal is dismissed. The impugned order of the learned Single Judge does not warrant any interference. The appellants are directed to comply with the order within 30 days. No costs.",
        "metadata": {"case_number": "WA 543/2023", "court": "Karnataka HC", "type": "Writ Appeal", "year": "2023"},
    },
    {
        "text": "Having heard the learned counsel, this Court finds merit in the petition. The order of transfer is set aside. The Government is directed to reinstate the petitioner within 15 days with all consequential benefits including back wages. The respondent shall personally appear before this Court on the next date of hearing failing which coercive action will be taken.",
        "metadata": {"case_number": "WP 4567/2024", "court": "Karnataka HC", "type": "Service Matter", "year": "2024"},
    },
    {
        "text": "The petition under Article 226 is disposed of. The respondent-Corporation is directed to consider the representation of the petitioner and pass appropriate orders within 4 weeks. Liberty is reserved to the petitioner to approach this Court if the representation is not considered.",
        "metadata": {"case_number": "WP 2345/2024", "court": "Karnataka HC", "type": "Municipal", "year": "2024"},
    },
    {
        "text": "The SLP is allowed in part. The High Court order is modified. The State Government shall pay compensation of Rs. 1,50,00,000/- for land acquisition under the Right to Fair Compensation and Transparency in Land Acquisition Act, 2013. The amount shall be deposited within 90 days. In default of payment, the amount shall carry interest at 9% per annum.",
        "metadata": {"case_number": "SLP 1234/2024", "court": "Supreme Court", "type": "Land Acquisition", "year": "2024"},
    },
    {
        "text": "This Court is constrained to observe that the State Government has not complied with the earlier order dated 10.01.2024. The Chief Secretary is directed to file a personal affidavit explaining the reasons for non-compliance. In the event of continued non-compliance, this Court shall be constrained to initiate contempt proceedings under Section 12 of the Contempt of Courts Act, 1971.",
        "metadata": {"case_number": "WP 7890/2023", "court": "Karnataka HC", "type": "Contempt", "year": "2023"},
    },
    {
        "text": "The pension revision application is allowed. The respondent-State is directed to revise the pension of the petitioner in accordance with the recommendations of the 7th Pay Commission within 3 months from the date of this order. The arrears shall be paid with interest at 6% per annum.",
        "metadata": {"case_number": "WP 3456/2024", "court": "Karnataka HC", "type": "Pension", "year": "2024"},
    },
    {
        "text": "The environmental clearance granted by MoEFCC is quashed. The mining operations in the Western Ghats area shall cease forthwith. The District Collector shall ensure immediate compliance and file a compliance report within 30 days. The State Pollution Control Board shall monitor the restoration activities.",
        "metadata": {"case_number": "WP 5678/2023", "court": "Karnataka HC", "type": "Environmental", "year": "2023"},
    },
    {
        "text": "The petitioner is entitled to regularization in service as directed by this Court in its earlier order. The respondent-BDA is directed to regularize the service of the petitioner within 4 weeks and pay all consequential monetary benefits. The Director, BDA shall file compliance report within 6 weeks.",
        "metadata": {"case_number": "WP 1111/2024", "court": "Karnataka HC", "type": "Service Regularization", "year": "2024"},
    },
    {
        "text": "The impugned notification under Section 4 of the Land Acquisition Act is quashed for violation of principles of natural justice. No hearing was afforded to the petitioner before acquisition. The respondent shall return the land to the petitioner within 60 days, failing which market value compensation with solatium shall be paid.",
        "metadata": {"case_number": "WP 2222/2024", "court": "Karnataka HC", "type": "Land Acquisition", "year": "2024"},
    },
    {
        "text": "The bail application is rejected. The investigation is at a crucial stage and there is a possibility of the accused tampering with evidence. The accused shall remain in judicial custody. Application for anticipatory bail is also rejected.",
        "metadata": {"case_number": "Crl.P 333/2024", "court": "Karnataka HC", "type": "Criminal - Bail", "year": "2024"},
    },
    {
        "text": "The KSRTC is directed to pay the accident compensation of Rs. 8,50,000/- to the claimant within 45 days from the date of this order. The amount already deposited shall be adjusted. Interest at 7.5% per annum shall be payable from the date of accident till realization.",
        "metadata": {"case_number": "MFA 444/2024", "court": "Karnataka HC", "type": "Motor Accident", "year": "2024"},
    },
    {
        "text": "The respondent-BESCOM is directed to restore the electricity connection of the petitioner within 7 working days. The disconnection was illegal as no notice was served. The respondent shall also pay costs of Rs. 10,000/- to the petitioner for unnecessary harassment.",
        "metadata": {"case_number": "WP 5555/2024", "court": "Karnataka HC", "type": "Public Utility", "year": "2024"},
    },
    {
        "text": "The BBMP is directed to remove the encroachment on the storm water drain within 30 days after issuing proper notice to the encroacher. The Commissioner, BBMP shall personally monitor the demolition drive. The Health Officer shall ensure proper waste management in the area.",
        "metadata": {"case_number": "WP 6666/2024", "court": "Karnataka HC", "type": "Municipal - Encroachment", "year": "2024"},
    },
    {
        "text": "The respondent-University is directed to declare the result of the petitioner within 2 weeks. The petitioner's examination was withheld without valid reason. The Vice Chancellor shall ensure that no student faces similar harassment in future.",
        "metadata": {"case_number": "WP 7777/2024", "court": "Karnataka HC", "type": "Education", "year": "2024"},
    },
    {
        "text": "The Forest Department is directed to release the vehicles seized from the petitioner within 10 days as no forest offence is made out. The Range Forest Officer shall file compliance report. The department shall pay costs of Rs. 25,000/- for wrongful seizure.",
        "metadata": {"case_number": "WP 8888/2024", "court": "Karnataka HC", "type": "Forest", "year": "2024"},
    },
    {
        "text": "The respondent-Insurance Company shall settle the health insurance claim of Rs. 4,50,000/- within 30 days. The rejection of claim on technical grounds is unsustainable. Interest at 9% per annum shall be payable from the date of rejection.",
        "metadata": {"case_number": "WP 9999/2024", "court": "Karnataka HC", "type": "Insurance", "year": "2024"},
    },
    {
        "text": "The State Government is directed to constitute the Lokayukta within 3 months as mandated by the Karnataka Lokayukta Act. The Chief Secretary shall file status report every month. The inordinate delay in constituting the anti-corruption body is deprecated.",
        "metadata": {"case_number": "PIL 100/2024", "court": "Karnataka HC", "type": "PIL - Governance", "year": "2024"},
    },
    {
        "text": "The respondent-police are directed to register FIR within 24 hours on the complaint of the petitioner under Section 154 Cr.P.C. The SHO shall investigate the matter and file charge sheet within statutory period. The SP shall monitor the investigation.",
        "metadata": {"case_number": "Crl.P 200/2024", "court": "Karnataka HC", "type": "Criminal - FIR", "year": "2024"},
    },
    {
        "text": "The order of demolition passed by the BBMP is stayed for a period of 8 weeks subject to the petitioner filing regularization application within 2 weeks. The Corporation shall consider the application within 6 weeks thereafter.",
        "metadata": {"case_number": "WP 300/2025", "court": "Karnataka HC", "type": "Municipal - Demolition", "year": "2025"},
    },
]


class Command(BaseCommand):
    help = "Populate the RAG vector store with Karnataka HC judgment texts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=str,
            default="samples",
            choices=["samples", "pdfs", "texts", "indiankanoon"],
            help="Source of judgment texts",
        )
        parser.add_argument("--path", type=str, default="", help="Directory path for pdfs/texts source")
        parser.add_argument("--query", type=str, default="", help="Search query for indiankanoon source")
        parser.add_argument("--count", type=int, default=20, help="Number of documents to fetch")

    def handle(self, *args, **options):
        rag = HybridRAGEngine()
        source = options["source"]

        if source == "samples":
            self._load_samples(rag)
        elif source == "pdfs":
            self._load_pdfs(rag, options["path"])
        elif source == "texts":
            self._load_texts(rag, options["path"])
        elif source == "indiankanoon":
            self._load_indiankanoon(rag, options["query"], options["count"])

    def _load_samples(self, rag):
        self.stdout.write("Loading built-in sample corpus...")
        rag.add_documents(BUILT_IN_SAMPLES)
        self.stdout.write(self.style.SUCCESS(f"Added {len(BUILT_IN_SAMPLES)} sample documents to RAG"))

    def _load_pdfs(self, rag, path):
        if not path or not os.path.isdir(path):
            self.stderr.write(f"Invalid path: {path}")
            return

        from apps.cases.services.pdf_processor import extract_text_from_pdf
        from apps.cases.services.section_segmenter import segment_judgment

        pdf_files = glob.glob(os.path.join(path, "*.pdf"))
        self.stdout.write(f"Found {len(pdf_files)} PDF files in {path}")

        documents = []
        for i, pdf_path in enumerate(pdf_files):
            self.stdout.write(f"  [{i + 1}/{len(pdf_files)}] Processing {os.path.basename(pdf_path)}...")
            try:
                text = extract_text_from_pdf(pdf_path)
                sections = segment_judgment(text)
                operative = sections.get("operative_order", "")
                if len(operative) > 50:
                    documents.append({
                        "text": operative[:3000],
                        "metadata": {
                            "case_number": os.path.basename(pdf_path).replace(".pdf", ""),
                            "court": "Karnataka HC",
                            "type": "PDF Import",
                            "source_file": os.path.basename(pdf_path),
                        },
                    })
            except Exception as e:
                self.stderr.write(f"  Failed: {e}")

        if documents:
            rag.add_documents(documents)
            self.stdout.write(self.style.SUCCESS(f"Added {len(documents)} PDF documents to RAG"))

    def _load_texts(self, rag, path):
        if not path or not os.path.isdir(path):
            self.stderr.write(f"Invalid path: {path}")
            return

        text_files = glob.glob(os.path.join(path, "*.txt"))
        self.stdout.write(f"Found {len(text_files)} text files in {path}")

        documents = []
        for f in text_files:
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
                if len(text) > 50:
                    documents.append({
                        "text": text[:3000],
                        "metadata": {
                            "case_number": os.path.basename(f).replace(".txt", ""),
                            "court": "Karnataka HC",
                            "type": "Text Import",
                        },
                    })

        if documents:
            rag.add_documents(documents)
            self.stdout.write(self.style.SUCCESS(f"Added {len(documents)} text documents to RAG"))

    def _load_indiankanoon(self, rag, query, count):
        import requests

        if not query:
            query = "Karnataka High Court writ petition 2024"

        self.stdout.write(f"Fetching from Indian Kanoon: '{query}' (max {count})...")

        try:
            headers = {"User-Agent": "NyayaDrishti-Research/1.0"}
            resp = requests.get(
                "https://api.indiankanoon.org/search/",
                params={"formInput": query, "pagenum": 0},
                headers={**headers, "Authorization": "Token " + os.getenv("INDIANKANOON_API_KEY", "")},
                timeout=30,
            )

            if resp.status_code != 200:
                self.stderr.write(
                    f"Indian Kanoon API returned {resp.status_code}. "
                    f"Set INDIANKANOON_API_KEY in .env or use --source pdfs/texts instead."
                )
                # Fallback to samples
                self.stdout.write("Falling back to built-in samples...")
                self._load_samples(rag)
                return

            docs = resp.json().get("docs", [])[:count]
            documents = []
            for doc in docs:
                text = doc.get("docsource", "") or doc.get("headline", "")
                if len(text) > 50:
                    documents.append({
                        "text": text[:3000],
                        "metadata": {
                            "case_number": doc.get("title", "Unknown"),
                            "court": "Karnataka HC",
                            "type": "Indian Kanoon",
                            "tid": doc.get("tid", ""),
                        },
                    })

            if documents:
                rag.add_documents(documents)
                self.stdout.write(self.style.SUCCESS(f"Added {len(documents)} documents from Indian Kanoon"))
            else:
                self.stderr.write("No documents found. Falling back to samples.")
                self._load_samples(rag)

        except Exception as e:
            self.stderr.write(f"Indian Kanoon fetch failed: {e}. Using built-in samples.")
            self._load_samples(rag)
