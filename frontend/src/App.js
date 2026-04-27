import React from 'react';
import { BrowserRouter, Routes, Route, Link, useNavigate, Navigate } from 'react-router-dom';
import './App.css';
import ProjectsList from './projects/ProjectsList';
import ProjectDetail from './projects/ProjectDetail';
import Login from './auth/Login';
import Signup from './auth/Signup';
import { useState } from 'react';

// Vérifie si l'utilisateur est connecté (présence du token)
function isAuthenticated() {
  return !!localStorage.getItem('accessToken');
}

// Route protégée : redirige vers /login si non connecté
function PrivateRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/login" />;
}

export default function App() {
  const [logged, setLogged] = useState(isAuthenticated());

  return (
    <BrowserRouter>
      <div>
        <h1>Gestion des projets étudiants - Polytechnique</h1>
        <nav>
          <Link to="/">Projets</Link> | <Link to="/login">Connexion</Link> | <Link to="/signup">Inscription</Link>
        </nav>
        <Routes>
          <Route path="/login" element={<Login onLogin={()=>setLogged(true)} />} />
          <Route path="/signup" element={<Signup onSignup={()=>window.location='/login'} />} />
          <Route path="/" element={<PrivateRoute><ProjectsList /></PrivateRoute>} />
          <Route path="/projects/:id" element={<PrivateRoute><ProjectDetail /></PrivateRoute>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
