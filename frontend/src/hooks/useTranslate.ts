import { useQuery } from '@tanstack/react-query';
import { useTranslation } from 'react-i18next';
import { api } from '../lib/api';
import type { TranslateResponse } from '../types';

export function useTranslate(text: string, enabled: boolean = true) {
  const { i18n } = useTranslation();
  return useQuery({
    queryKey: ['translate', text, i18n.language],
    queryFn: async () => {
      const res = await api.post<TranslateResponse>('/api/translate/', {
        text, source_lang: 'en', target_lang: i18n.language,
      });
      return res.data.translated_text;
    },
    enabled: enabled && i18n.language === 'kn',
    staleTime: Infinity,
  });
}
