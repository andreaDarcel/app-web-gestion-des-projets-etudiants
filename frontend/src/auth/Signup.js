import React, { useState } from 'react';
import api from '../api';

// Formulaire d'inscription avec gestion d'erreur et feedback utilisateur
export default function Signup({ onSignup }) {
  const [form, setForm] = useState({ email: '', username: '', password: '', first_name: '', last_name: '' });
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  // Gestion du changement de champ
  const handleChange = e => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  // Soumission du formulaire
  const handleSubmit = e => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    api.post('/accounts/signup/', form)
      .then(() => {
        setSuccess(true);
        onSignup && onSignup();
      })
      .catch(err => {
        if (err.response && err.response.data) {
          setError(err.response.data.error || Object.values(err.response.data).join(' '));
        } else {
          setError("Erreur réseau ou serveur.");
        }
      });
  };

  return (
    <form onSubmit={handleSubmit} className="signup-form">
      <h2>Inscription</h2>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">Inscription réussie ! Connectez-vous.</div>}
      <input name="email" type="email" placeholder="Email" value={form.email} onChange={handleChange} required />
      <input name="username" placeholder="Nom d'utilisateur" value={form.username} onChange={handleChange} required />
      <input name="first_name" placeholder="Prénom" value={form.first_name} onChange={handleChange} required />
      <input name="last_name" placeholder="Nom" value={form.last_name} onChange={handleChange} required />
      <input name="password" type="password" placeholder="Mot de passe" value={form.password} onChange={handleChange} required />
      <button type="submit">S'inscrire</button>
    </form>
  );
}
