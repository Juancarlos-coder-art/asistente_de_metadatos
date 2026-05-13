// src/context/LanguageContext.jsx
import { createContext, useContext, useState } from "react";

const LanguageContext = createContext({ lang: "es", toggle: () => {} });

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState("es");
  const toggle = () => setLang(l => l === "es" ? "en" : "es");
  return (
    <LanguageContext.Provider value={{ lang, toggle }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLang() {
  return useContext(LanguageContext);
}
