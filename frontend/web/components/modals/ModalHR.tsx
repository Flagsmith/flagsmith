import React, { FC } from 'react' // we need this to make JSX compile

type ModalHRType = {
  className?: string
}

const ModalHR: FC<ModalHRType> = ({ className }) => {
  return <hr className={`my-0 py-0 ${className}`} />
}

export default ModalHR
