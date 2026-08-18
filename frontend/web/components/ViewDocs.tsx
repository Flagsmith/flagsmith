import { FC } from 'react'
import Button, { ButtonType } from './base/forms/Button'
import Icon from './icons/Icon'

type ViewDocsType = ButtonType & {}

const ViewDocs: FC<ViewDocsType> = (props) => {
  return (
    <Button {...props} target='_blank' className='fw-bold' theme='text'>
      <Icon name='file-text' />
      View docs
    </Button>
  )
}

export default ViewDocs
