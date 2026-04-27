import React, { useEffect, useState } from 'react';
import api from '../api';
import { Link } from 'react-router-dom';

export default function ProjectsList() {
  const [projects, setProjects] = useState([]);
  const [q, setQ] = useState('');
  const [email, setEmail] = useState('');
  const [page, setPage] = useState(1);
  const [count, setCount] = useState(0);

  useEffect(() => {
    api.get('/projects/', { params: { q, email, page } })
      .then(res => { setProjects(res.data.results); setCount(res.data.count); })
      .catch(err => console.error(err));
  }, [q, email, page]);

  return (
    <div>
      <h2>Liste des projets</h2>
      <div>
        <input placeholder="Recherche texte" value={q} onChange={e=>setQ(e.target.value)} />
        <input placeholder="Recherche par email" value={email} onChange={e=>setEmail(e.target.value)} />
      </div>
      {projects.length === 0 && <p>Aucun projet</p>}
      <ul>
        {projects.map(p => (
          <li key={p.id}><Link to={`/projects/${p.id}`}>{p.title}</Link> - {p.supervisors && p.supervisors.length>0 ? p.supervisors[0].first_name : 'Sans encadrant'}</li>
        ))}
      </ul>
      <div>
        <button onClick={()=>setPage(p=>Math.max(1,p-1))} disabled={page===1}>Préc</button>
        <span> Page {page} </span>
        <button onClick={()=>setPage(p=>p+1)} disabled={page*10>=count}>Suiv</button>
      </div>
    </div>
  );
}
