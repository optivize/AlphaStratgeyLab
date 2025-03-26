import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'dark' | 'light';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

export const ThemeProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  // Check for saved theme preference or use preferred color scheme
  const getSavedTheme = (): Theme => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    
    if (savedTheme) {
      return savedTheme;
    }
    
    // Check for system preference
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  };

  const [theme, setTheme] = useState<Theme>(getSavedTheme);

  // Effect to apply theme to document when it changes
  useEffect(() => {
    document.documentElement.setAttribute('data-bs-theme', theme);
    document.body.classList.remove('theme-dark', 'theme-light');
    document.body.classList.add(`theme-${theme}`);
    localStorage.setItem('theme', theme);
  }, [theme]);

  // Add transition class on initial load
  useEffect(() => {
    document.body.classList.add('theme-transition');
    
    // Remove transition class after components have mounted
    const timeoutId = setTimeout(() => {
      document.body.classList.add('theme-transition-active');
    }, 100);
    
    return () => clearTimeout(timeoutId);
  }, []);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

export default ThemeContext;