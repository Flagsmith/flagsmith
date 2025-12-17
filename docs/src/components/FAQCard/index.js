import React, { useState } from 'react';
import clsx from 'clsx';
import styles from './styles.module.css';

export default function FAQCard({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className={styles.faqCard}>
      <button
        className={clsx(styles.faqCardHeader, isOpen && styles.faqCardHeaderOpen)}
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
      >
        <h3 className={styles.faqCardTitle}>{title}</h3>
        <span className={styles.faqCardIcon}>
          {isOpen ? '−' : '+'}
        </span>
      </button>
      {isOpen && (
        <div className={styles.faqCardContent}>
          {children}
        </div>
      )}
    </div>
  );
}

