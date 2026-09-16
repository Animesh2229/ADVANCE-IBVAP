import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { translations, languageNames, t as translate } from '../i18n/translations';

const LanguageContext = createContext();
const STORAGE_KEY = 'ibvap_field_lang';

export function LanguageProvider({ children }) {
  const [lang, setLangState] = useState('en');

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY).then((v) => {
      if (v && translations[v]) setLangState(v);
    }).catch(() => {});
  }, []);

  const setLang = (code) => {
    if (translations[code]) {
      setLangState(code);
      AsyncStorage.setItem(STORAGE_KEY, code).catch(() => {});
    }
  };

  const t = (key) => translate(lang, key);

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, languageNames, available: Object.keys(translations) }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider');
  return ctx;
}
