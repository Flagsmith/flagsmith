import React from 'react';
import PropTypes from 'prop-types';

const PasswordRequirements = ({ password }) => {
  const requirements = [
    { label: 'At least 8 characters', test: password.length >= 8 },
    { label: 'Contains a number', test: /\d/.test(password) },
    { label: 'Contains a special character', test: /[!@#$%^&*]/.test(password) },
    { label: 'Contains an uppercase letter', test: /[A-Z]/.test(password) },
    { label: 'Contains a lowercase letter', test: /[a-z]/.test(password) },
  ];

  return (
    <div>
      <ul className="password-requirements" style={{ listStyleType: 'none', padding: 0 }}>
        {requirements.map((req, index) => (
          <p key={index} style={{ color: req.test ? 'green' : 'red', fontSize: '12px', margin: '4px 0' }}>
            {req.test ? '✔' : '✘'} {req.label}
          </p>
        ))}
      </ul>
    </div>
  );
};

PasswordRequirements.propTypes = {
    password: PropTypes.string.isRequired,
  };

export default PasswordRequirements;
