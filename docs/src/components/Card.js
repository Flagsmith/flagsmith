import React from 'react';
import './Card.css';

export default function Card({ title, children, href }) {
  return (
    <a className="card" href={href}>
      <div className="card-title">{title}</div>
      <div className="card-body">{children}</div>
    </a>
  );
}
