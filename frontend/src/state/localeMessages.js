import { enMessages } from "./localeCatalog.en.js";
import { zhMessages } from "./localeCatalog.zh.js";

export const DEFAULT_LOCALE = "zh-CN";
export const LOCALE_STORAGE_KEY = "rag_locale";
export const LOCALE_OPTIONS = [
  { value: "zh-CN", label: "中文" },
  { value: "en", label: "English" },
];

const MESSAGES = {
  "zh-CN": zhMessages,
  en: enMessages,
};

export function getLocale() {
  return localStorage.getItem(LOCALE_STORAGE_KEY) || DEFAULT_LOCALE;
}

export function setLocale(value) {
  localStorage.setItem(LOCALE_STORAGE_KEY, value);
}

export function getMessages(locale = DEFAULT_LOCALE) {
  return MESSAGES[locale] || MESSAGES[DEFAULT_LOCALE];
}
