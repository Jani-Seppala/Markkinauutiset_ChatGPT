import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate} from 'react-router-dom';
import LoginPage from './components/LoginPage';
import RegisterPage from './components/RegisterPage';
import FavoritesPage from './components/FavoritesPage';
import StockPage from './components/StockPage';
import InfoPage from './components/InfoPage';
import SearchBar from './components/SearchBar';
import Logout from './components/Logout';
import NewsAndAnalysis from './components/NewsAndAnalysis';
import NotFoundPage from './components/NotFoundPage';
import { useUser, UserProvider } from './components/UserContext';
import './App.css';

function App() {
  const { isLoggedIn, toggleDarkMode, darkMode, logout, isSoundOn, toggleSound, loading } = useUser();
  const [logoutCount, setLogoutCount] = useState(0);

  const handleLogout = () => {
    logout();
    setLogoutCount(logoutCount + 1);
  };

  // Apply or remove the dark-mode class on the body element based on the darkMode state
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark-mode');
    } else {
      document.body.classList.remove('dark-mode');
    }
  }, [darkMode]); // This effect runs whenever darkMode changes


  useEffect(() => {
    const handleTokenExpiration = () => logout();
    window.addEventListener('token-expiration', handleTokenExpiration);
    return () => {
        window.removeEventListener('token-expiration', handleTokenExpiration);
    };
  }, [logout]);

    // Determine navbar and button classes based on darkMode
    const navbarClass = darkMode ? "navbar navbar-expand-lg navbar-dark bg-dark" : "navbar navbar-expand-lg navbar-light bg-light";
    const toggleButtonClass = darkMode ? "btn btn-light" : "btn btn-dark";
    const soundToggleButtonClass = isSoundOn ? "btn btn-danger" : "btn btn-success";

    if (loading) {
      return <div>Loading...</div>; // Show a loading indicator while authentication state is being initialized
    }

  return (
    <Router>
      {/* <CheckTokenExpiration /> */}
      <nav className={`${navbarClass} fixed-navbar mb-4`}>
        <div className="container">
          <Link className="navbar-brand fs-2" to="/">News App</Link>
          <div className="navbar-collapse collapse">
            <ul className="navbar-nav me-auto mb-2 mb-lg-0 fs-4">            
              {!isLoggedIn && (
                <>
                  <li className="nav-item"><Link className="nav-link" to="/login">Login</Link></li>
                  <li className="nav-item"><Link className="nav-link" to="/register">Register</Link></li>
                </>
              )}
              {isLoggedIn && (
                <>
                  <li className="nav-item"><Link className="nav-link" to="/favorites">Favorites</Link></li>
                  <li className="nav-item"><Logout onLogout={handleLogout} /></li>
                </>
              )}
              <li className="nav-item"><Link className="nav-link" to="/info">Info</Link></li>
            </ul>
            <button onClick={toggleSound} className={`${soundToggleButtonClass} me-3`}>
              {isSoundOn ? 'Sound Off' : 'Sound On'}
            </button>
            <button onClick={toggleDarkMode} className={`${toggleButtonClass} me-3`}>
              {darkMode ? 'Light Mode' : 'Dark Mode'}
            </button>
            <SearchBar />
          </div>
        </div>
      </nav>
      <div className="nav-spacer"></div>
      <div className="container">
        <Routes>
          <Route path="/" element={<NewsAndAnalysis isSoundOn={isSoundOn} />} />
          <Route path="/login" element={!isLoggedIn ? <LoginPage /> : <Navigate replace to="/" />} />
          <Route path="/register" element={!isLoggedIn ? <RegisterPage /> : <Navigate replace to="/" />} />
          <Route path="/favorites" element={isLoggedIn ? <FavoritesPage /> : <Navigate replace to="/login" />} />
          <Route path="/stocks/:stockId" element={<StockPage />} />
          <Route path="/info" element={<InfoPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default function WrappedApp() {
  return (
    <UserProvider>
      <App />
    </UserProvider>
  );
}