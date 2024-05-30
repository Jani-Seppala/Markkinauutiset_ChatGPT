import React from 'react';
import { Link } from 'react-router-dom';
// import './Forms.css'; // Assuming you have generic styles you want to reuse

function NotFoundPage() {
  return (
    <div className="page not-found-page">
      <h1 className="text-center">404 - Page Not Found</h1>
      <p className="text-center">We can't find the page you're looking for.</p>
      <div className="text-center">
        <Link to="/" className="btn btn-primary">Go Home</Link>
        {/* <Link to="/info" className="btn btn-secondary">Contact Support</Link> */}
      </div>
    </div>
  );
}

export default NotFoundPage;
