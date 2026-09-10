import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, useContext, useEffect, useMemo, useState } from 'react';
import { Appearance } from 'react-native';

type StarterContextValue = {
  savedIds: string[];
  darkMode: boolean;
  ready: boolean;
  toggleSaved: (id: string) => void;
  setDarkMode: (value: boolean) => void;
  resetPreferences: () => void;
};

const StarterContext = createContext<StarterContextValue | null>(null);

export function StarterProvider({ children }: { children: React.ReactNode }) {
  const [savedIds, setSavedIds] = useState<string[]>([]);
  const [darkMode, setDarkModeState] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    Promise.all([AsyncStorage.getItem('starter.saved'), AsyncStorage.getItem('starter.dark')])
      .then(([saved, dark]) => {
        if (saved) setSavedIds(JSON.parse(saved) as string[]);
        if (dark) {
          const isDark = dark === 'true';
          setDarkModeState(isDark);
          Appearance.setColorScheme(isDark ? 'dark' : 'light');
        }
      })
      .finally(() => setReady(true));
  }, []);

  const toggleSaved = (id: string) => {
    setSavedIds((current) => {
      const next = current.includes(id) ? current.filter((item) => item !== id) : [...current, id];
      void AsyncStorage.setItem('starter.saved', JSON.stringify(next));
      return next;
    });
  };

  const setDarkMode = (value: boolean) => {
    setDarkModeState(value);
    Appearance.setColorScheme(value ? 'dark' : 'light');
    void AsyncStorage.setItem('starter.dark', String(value));
  };

  const resetPreferences = () => {
    setSavedIds([]);
    setDarkModeState(false);
    Appearance.setColorScheme('light');
    void AsyncStorage.multiRemove(['starter.saved', 'starter.dark']);
  };

  const value = useMemo(() => ({ savedIds, darkMode, ready, toggleSaved, setDarkMode, resetPreferences }), [savedIds, darkMode, ready]);
  return <StarterContext.Provider value={value}>{children}</StarterContext.Provider>;
}

export function useStarter() {
  const context = useContext(StarterContext);
  if (!context) throw new Error('useStarter must be used inside StarterProvider');
  return context;
}