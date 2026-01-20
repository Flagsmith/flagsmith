import React, { FC, ReactNode } from 'react'

export type FormGroupProps = {
  children?: ReactNode
  className?: string
}

const FormGroup: FC<FormGroupProps> = ({ children, className = '' }) => {
  return <div className={`form-group ${className}`}>{children}</div>
}

FormGroup.displayName = 'FormGroup'

export default FormGroup
