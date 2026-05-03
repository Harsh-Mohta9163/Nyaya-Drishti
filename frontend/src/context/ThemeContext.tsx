import { createContext, useContext, type ReactNode } from 'react';

interface ThemeContextType {
  theme: 'dark';
}

const ThemeContext = createContext<ThemeContextType>({ theme: 'dark' });

export function ThemeProvider({ children }: { children: ReactNode }) {
  return (
    <ThemeContext.Provider value={{ theme: 'dark' }}>
      <div className="dark">{children}</div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
