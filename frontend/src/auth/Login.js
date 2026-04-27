import React, { useState } from 'react';
import api from '../api';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  // Soumission du formulaire de connexion
  const submit = (e) => {
    e.preventDefault();
    api.post('/token/', { username: email, password })
      .then(res => {
        localStorage.setItem('accessToken', res.data.access);
        localStorage.setItem('refreshToken', res.data.refresh);
        onLogin && onLogin();
      })
      .catch(err => setError('Échec de la connexion'));
  };

  return (
    <form onSubmit={submit} className="login-form">
      <h2>Connexion</h2>
      {error && <div className="error">{error}</div>}
      <input placeholder="Email ou nom d'utilisateur" value={email} onChange={e => setEmail(e.target.value)} required />
      <input type="password" placeholder="Mot de passe" value={password} onChange={e => setPassword(e.target.value)} required />
      <button type="submit">Se connecter</button>
    </form>
  );
}
