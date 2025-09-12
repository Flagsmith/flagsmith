import React, { useEffect } from 'react'
import PropTypes from 'prop-types'
import { close, checkmark } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

const PasswordRequirements = ({ onRequirementsMet, password }) => {
  const requirements = [
    { label: 'At least 8 characters', test: password.length >= 8 },
    { label: 'Contains a number', test: /\d/.test(password) },
    {
      label: 'Contains a special character',
      test: /[!@#$%^&*(),.?":{}|<>[\]\\\/_+=-]/.test(password),
    },
    { label: 'Contains an uppercase letter', test: /[A-Z]/.test(password) },
    { label: 'Contains a lowercase letter', test: /[a-z]/.test(password) },
  ]

  const allRequirementsMet = requirements.every((req) => req.test)

  useEffect(() => {
    onRequirementsMet(allRequirementsMet)
  }, [allRequirementsMet, onRequirementsMet])

  return (
    <div>
      <ul
        className='password-requirements'
        style={{ listStyleType: 'none', padding: 0 }}
      >
        {requirements.map((req, index) => (
          <p
            key={index}
            style={{
              color: req.test ? 'green' : 'red',
              fontSize: '12px',
              margin: '4px 0',
            }}
          >
            <IonIcon
              style={{ marginRight: '4px', verticalAlign: 'middle' }}
              icon={req.test ? checkmark : close}
            />
            {req.label}
          </p>
        ))}
      </ul>
    </div>
  )
}

PasswordRequirements.propTypes = {
  onRequirementsMet: PropTypes.func.isRequired,
  password: PropTypes.string.isRequired,
}

export default PasswordRequirements
