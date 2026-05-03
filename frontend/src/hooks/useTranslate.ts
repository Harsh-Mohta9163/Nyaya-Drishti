import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api, USE_MOCK, mockDelay } from '../lib/api';
import type { TranslateResponse } from '../types';

export function useTranslate(text: string, enabled: boolean = true) {
  const { i18n } = useTranslation();
  return useQuery({
    queryKey: ['translate', text, i18n.language],
    queryFn: async () => {
      if (USE_MOCK) {
        await mockDelay();
        return text; // In mock mode, return original text
      }
      const res = await api.post<TranslateResponse>('/api/translate/', {
        text, source_lang: 'en', target_lang: i18n.language,
      });
      return res.data.translated_text;
    },
    enabled: enabled && i18n.language === 'kn',
    staleTime: Infinity, // Translated text never goes stale
  });
}
