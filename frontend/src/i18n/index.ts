import en from './en.json';
import es from './es.json';
import nl from './nl.json';

export const languages = ['en', 'es', 'nl'] as const;
export type Language = (typeof languages)[number];

export const defaultLanguage: Language = 'en';

export const languageNames: Record<Language, string> = {
  en: 'English',
  es: 'Espanol',
  nl: 'Nederlands',
};

const translations: Record<Language, typeof en> = {
  en,
  es,
  nl,
};

export function getTranslations(lang: Language) {
  return translations[lang] || translations[defaultLanguage];
}

export function isValidLanguage(lang: string): lang is Language {
  return languages.includes(lang as Language);
}
