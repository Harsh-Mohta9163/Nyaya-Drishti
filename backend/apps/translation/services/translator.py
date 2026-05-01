"""
Bilingual translation service.

Primary: IndicTrans2 (local model, CPU-friendly) — for Linux/Render deployment.
Fallback: NVIDIA NIM LLM translation — for Windows dev / when IndicTrans unavailable.
"""
import logging

logger = logging.getLogger(__name__)


class BilingualTranslator:
    def __init__(self):
        self._indictrans_available = False
        self._nvidia_available = False

        # Try IndicTrans2 first (only works on Linux with C++ build tools)
        try:
            from IndicTransToolkit import IndicProcessor
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            self.processor = IndicProcessor(inference=True)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(
                "ai4bharat/indictrans2-en-indic-dist-200M",
                trust_remote_code=True,
            )
            self.tokenizer = AutoTokenizer.from_pretrained(
                "ai4bharat/indictrans2-en-indic-dist-200M",
                trust_remote_code=True,
            )
            self._indictrans_available = True
            logger.info("IndicTrans2 loaded successfully")
        except Exception as e:
            logger.info("IndicTrans2 not available (%s), will use NVIDIA NIM fallback", e)
            self.processor = None
            self.model = None
            self.tokenizer = None

        # Check NVIDIA NIM availability as fallback
        try:
            from django.conf import settings
            if getattr(settings, "NVIDIA_API_KEY", ""):
                self._nvidia_available = True
                logger.info("NVIDIA NIM translation fallback available")
        except Exception:
            pass

    def translate(self, text: str, source_lang: str = "eng_Latn", target_lang: str = "kan_Knda") -> str:
        """
        Translate text between English and Kannada.

        Tries IndicTrans2 first, falls back to NVIDIA NIM LLM translation.
        """
        if not text or not text.strip():
            return text

        # Try IndicTrans2 (fast, local, production)
        if self._indictrans_available:
            return self._translate_indictrans(text, source_lang, target_lang)

        # Fallback to NVIDIA NIM (cloud, slower, but works everywhere)
        if self._nvidia_available:
            return self._translate_nvidia(text, source_lang, target_lang)

        # No translation available
        logger.warning("No translation backend available, returning original text")
        return text

    def _translate_indictrans(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using IndicTrans2 local model."""
        try:
            import torch

            batch = self.processor.preprocess_batch(
                [text], src_lang=source_lang, tgt_lang=target_lang
            )
            inputs = self.tokenizer(batch, return_tensors="pt", padding=True)
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_length=256)
            result = self.tokenizer.batch_decode(outputs, skip_special_tokens=True)
            return self.processor.postprocess_batch(result, lang=target_lang)[0]
        except Exception as e:
            logger.error("IndicTrans2 translation failed: %s", e)
            return text

    def _translate_nvidia(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate using NVIDIA NIM Llama for Kannada translation."""
        try:
            from openai import OpenAI
            from django.conf import settings

            client = OpenAI(
                base_url=settings.NVIDIA_BASE_URL,
                api_key=settings.NVIDIA_API_KEY,
            )

            # Map language codes to human-readable names
            lang_map = {
                "eng_Latn": "English",
                "kan_Knda": "Kannada",
                "hin_Deva": "Hindi",
            }
            src_name = lang_map.get(source_lang, source_lang)
            tgt_name = lang_map.get(target_lang, target_lang)

            response = client.chat.completions.create(
                model="meta/llama-3.3-70b-instruct",
                temperature=0.1,
                max_tokens=1000,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a professional legal translator. "
                            f"Translate the following text from {src_name} to {tgt_name}. "
                            f"Preserve all legal terminology, case numbers, dates, and proper nouns. "
                            f"Output ONLY the translated text, no explanations."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
            )

            translated = response.choices[0].message.content
            return translated.strip() if translated else text

        except Exception as e:
            logger.error("NVIDIA NIM translation failed: %s", e)
            return text
