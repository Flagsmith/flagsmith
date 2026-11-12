import React, { FC, useEffect } from 'react'
import classNames from 'classnames'
import Icon from './icons/Icon'

type PasswordRequirementsProps = {
  onRequirementsMet: (met: boolean) => void
  password: string
}

const PasswordRequirements: FC<PasswordRequirementsProps> = ({
  onRequirementsMet,
  password,
}) => {
  const requirements = [
    { label: 'At least 8 characters', test: password.length >= 8 },
    { label: 'Contains a number', test: /\d/.test(password) },
    {
      label: 'Contains a special character',
      test: /[!@#$%^&*(),.?":{}|<>[\]\\/_+=-]/.test(password),
    },
    { label: 'Contains an uppercase letter', test: /[A-Z]/.test(password) },
    { label: 'Contains a lowercase letter', test: /[a-z]/.test(password) },
  ]

  const allRequirementsMet = requirements.every((req) => req.test)

  useEffect(() => {
    onRequirementsMet(allRequirementsMet)
  }, [allRequirementsMet, onRequirementsMet])

  return (
    <ul className='password-requirements list-unstyled mb-0 mt-2'>
      {requirements.map((req, index) => (
        <li
          key={index}
          className={classNames(
            'd-flex align-items-center gap-1 fs-small lh-sm mb-1',
            req.test ? 'text-success' : 'text-danger',
          )}
        >
          <Icon
            name={req.test ? 'checkmark' : 'close-circle'}
            width={12}
            height={12}
            fill='currentColor'
          />
          {req.label}
        </li>
      ))}
    </ul>
  )
}

export default PasswordRequirements
