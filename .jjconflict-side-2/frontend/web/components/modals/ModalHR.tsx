import React, { FC } from 'react'

type ModalHRType = {
  className?: string
}

const ModalHR: FC<ModalHRType> = ({ className }) => {
  return <hr className={`my-0 py-0 ${className ? className : ''}`} />
}

export default ModalHR
