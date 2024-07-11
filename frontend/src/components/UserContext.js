import React, { createContext, useContext, useState, useEffect } from 'react';

const UserContext = createContext();

function useUser() {
  return useContext(UserContext);
}

function UserProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loading, setLoading] = useState(true); // New state for loading

    // Initialize darkMode state based on localStorage or default to false
    const [darkMode, setDarkMode] = useState(() => {
      const storedDarkModePref = localStorage.getItem('darkMode');
      return storedDarkModePref === 'true' ? true : false;
    });
    const [isSoundOn, setIsSoundOn] = useState(() => {
      const storedSoundPref = localStorage.getItem('soundPreference');
      return storedSoundPref === 'true';
    });

  useEffect(() => {
    const token = localStorage.getItem('token');
    setIsLoggedIn(!!token);
    setLoading(false); // Set loading to false after checking the token
  }, []);

  useEffect(() => {
    // Store the dark mode preference in localStorage
    localStorage.setItem('darkMode', darkMode);
  }, [darkMode]); // This effect runs when darkMode state changes

  useEffect(() => {
    localStorage.setItem('soundPreference', isSoundOn);
  }, [isSoundOn]);

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    setIsLoggedIn(false);
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const toggleSound = () => setIsSoundOn(!isSoundOn);

  const value = {
    isLoggedIn,
    setIsLoggedIn,
    loading,
    logout,
    darkMode,
    toggleDarkMode,
    isSoundOn,
    toggleSound,
  };

  return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

export { UserContext, useUser, UserProvider };

