from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from .services.translator import BilingualTranslator


class TranslateView(APIView):
    translator = BilingualTranslator()

    def post(self, request):
        text = request.data.get("text", "")
        source_lang = request.data.get("source_lang", "eng_Latn")
        target_lang = request.data.get("target_lang", "kan_Knda")
        translated_text = self.translator.translate(text, source_lang=source_lang, target_lang=target_lang)
        return Response({"translated_text": translated_text})
