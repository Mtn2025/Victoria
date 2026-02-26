import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import es from './translations/es.json';
import en from './translations/en.json';

type Language = 'es' | 'en';
type TranslationsRecord = Record<string, any>;

const translations: Record<Language, TranslationsRecord> = {
    es,
    en
};

interface I18nContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export const I18nProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [language, setLanguageState] = useState<Language>('es');

    useEffect(() => {
        const savedLang = localStorage.getItem('appLanguage') as Language;
        if (savedLang && (savedLang === 'es' || savedLang === 'en')) {
            setLanguageState(savedLang);
        }
    }, []);

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
        localStorage.setItem('appLanguage', lang);
    };

    // Helper function to get nested object property via dot notation string (e.g. "model.provider")
    const getNestedTranslation = (obj: any, path: string): string => {
        const value = path.split('.').reduce((prev, curr) => (prev && prev[curr] !== undefined) ? prev[curr] : undefined, obj);
        return typeof value === 'string' ? value : path;
    };

    const t = (key: string): string => {
        return getNestedTranslation(translations[language], key);
    };

    return (
        <I18nContext.Provider value={{ language, setLanguage, t }}>
            {children}
        </I18nContext.Provider>
    );
};

export const useTranslation = (): I18nContextType => {
    const context = useContext(I18nContext);
    if (!context) {
        throw new Error('useTranslation must be used within an I18nProvider');
    }
    return context;
};
