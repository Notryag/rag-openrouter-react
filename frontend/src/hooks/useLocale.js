import { createContext, useContext, useEffect, useState } from "react";
import {
  DEFAULT_LOCALE,
  getLocale,
  getMessages,
  LOCALE_OPTIONS,
  setLocale as persistLocale,
} from "../state/localeMessages.js";

const LocaleContext = createContext(null);

export function LocaleProvider({ children }) {
  const [locale, setLocale] = useState(() => getLocale());

  useEffect(() => {
    persistLocale(locale);
  }, [locale]);

  return (
    <LocaleContext.Provider
      value={{
        copy: getMessages(locale),
        locale,
        locales: LOCALE_OPTIONS,
        setLocale,
      }}
    >
      {children}
    </LocaleContext.Provider>
  );
}

export function useLocale() {
  const context = useContext(LocaleContext);

  if (!context) {
    return {
      copy: getMessages(DEFAULT_LOCALE),
      locale: DEFAULT_LOCALE,
      locales: LOCALE_OPTIONS,
      setLocale: () => {},
    };
  }

  return context;
}
