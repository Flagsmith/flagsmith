import { FC } from 'react'
import Button, { ButtonType } from './base/forms/Button'
import Icon from './Icon' // we need this to make JSX compile

type ViewDocsType = ButtonType & {}

const ViewDocs: FC<ViewDocsType> = (props) => {
  return (
    <Button {...props} target='_blank' className='fw-bold' theme='text'>
      <Icon style={{ marginTop: -5 }} fill={'#6837fc'} name={'file-text'} />
      <span style={{ lineHeight: '24px' }}> View docs</span>
    </Button>
  )
}

export default ViewDocs
