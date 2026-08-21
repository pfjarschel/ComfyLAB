import { useState, useEffect } from 'react';

import en from './locales/en.json';
import ptBR from './locales/pt-BR.json';
import es from './locales/es.json';

export type Language = 'en' | 'pt-BR' | 'es';

export interface LanguageOption {
  code: Language;
  label: string;
  flag: string;
}

export const SUPPORTED_LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', flag: '🇺🇸' },
  { code: 'pt-BR', label: 'Português', flag: '🇧🇷' },
  { code: 'es', label: 'Español', flag: '🇪🇸' },
];

const resources: Record<Language, any> = {
  en,
  'pt-BR': ptBR,
  es,
};

const STORAGE_KEY = 'comfylab_language';

const getInitialLanguage = (): Language => {
  if (typeof window === 'undefined') return 'en';
  const saved = localStorage.getItem(STORAGE_KEY) as Language;
  if (saved && resources[saved]) return saved;

  const navLang = navigator.language;
  if (navLang.startsWith('pt')) return 'pt-BR';
  if (navLang.startsWith('es')) return 'es';
  return 'en';
};

let currentLanguage: Language = getInitialLanguage();
const listeners = new Set<(lang: Language) => void>();

export const i18n = {
  get language(): Language {
    return currentLanguage;
  },
  changeLanguage(lang: Language) {
    if (!resources[lang] || lang === currentLanguage) return;
    currentLanguage = lang;
    if (typeof window !== 'undefined') {
      localStorage.setItem(STORAGE_KEY, lang);
    }
    listeners.forEach((listener) => listener(lang));
  },
  t(key: string, defaultValOrParams?: string | Record<string, any>, maybeParams?: Record<string, any>): string {
    const defaultVal = typeof defaultValOrParams === 'string' ? defaultValOrParams : undefined;
    const params = typeof defaultValOrParams === 'object' && defaultValOrParams !== null 
      ? defaultValOrParams 
      : maybeParams;

    const keys = key.split('.');
    let val: any = resources[currentLanguage];
    for (const k of keys) {
      if (val && typeof val === 'object' && k in val) {
        val = val[k];
      } else {
        val = undefined;
        break;
      }
    }
    let res = typeof val === 'string' ? val : undefined;

    // Fallback to English if current language missing key
    if (res === undefined) {
      let fallbackVal: any = resources['en'];
      for (const k of keys) {
        if (fallbackVal && typeof fallbackVal === 'object' && k in fallbackVal) {
          fallbackVal = fallbackVal[k];
        } else {
          fallbackVal = undefined;
          break;
        }
      }
      if (typeof fallbackVal === 'string') {
        res = fallbackVal;
      }
    }

    if (res === undefined) {
      res = defaultVal !== undefined ? defaultVal : key;
    }

    if (params && typeof res === 'string') {
      res = res.replace(/\{\{\s*(\w+)\s*\}\}/g, (_, k) => {
        return k in params && params[k] !== undefined ? String(params[k]) : `{{${k}}}`;
      });
    }

    return res;
  },
  subscribe(listener: (lang: Language) => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
};

export function useTranslation() {
  const [lang, setLang] = useState<Language>(i18n.language);

  useEffect(() => {
    return i18n.subscribe((newLang) => {
      setLang(newLang);
    });
  }, []);

  return {
    t: (key: string, defaultValOrParams?: string | Record<string, any>, params?: Record<string, any>) =>
      i18n.t(key, defaultValOrParams, params),
    i18n,
    currentLanguage: lang,
  };
}

export default i18n;
