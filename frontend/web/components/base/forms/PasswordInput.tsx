import React, { FC } from 'react'
import Input, { InputProps } from './Input'

// `type` and `search` are fixed by this component.
type PasswordInputProps = Omit<InputProps, 'type' | 'search'>

// Password field with a reveal (eye) toggle.
//
// Phase 1: composes Input, which still owns the toggle. This establishes the
// component consumers migrate to; the toggle logic moves here when Input is
// slimmed to a plain input (the wrapper-less redesign).
const PasswordInput: FC<PasswordInputProps> = (props) => (
  <Input {...props} type='password' />
)

export default PasswordInput
