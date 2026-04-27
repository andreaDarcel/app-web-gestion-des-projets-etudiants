import React, { useEffect, useState } from 'react';
import api from '../api';
import { useParams } from 'react-router-dom';

export default function ProjectDetail(){
  const { id } = useParams();
  const [project, setProject] = useState(null);
  const [motivation, setMotivation] = useState('');

  useEffect(() => {
    api.get(`/projects/${id}/`).then(r => setProject(r.data)).catch(console.error);
  }, [id]);

  const apply = () => {
    api.post('/applications/', { project: id, motivation })
      .then(() => alert('Candidature envoyée'))
      .catch(e => alert('Erreur'));
  };

  if(!project) return <div>Chargement...</div>
  return (
    <div>
      <h2>{project.title}</h2>
      <p>{project.description}</p>
      <h3>Postuler</h3>
      <textarea value={motivation} onChange={e => setMotivation(e.target.value)} />
      <button onClick={apply}>Postuler</button>
    </div>
  )
}
