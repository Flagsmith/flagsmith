import React, { FC } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import InputGroup from 'components/base/forms/InputGroup'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'

type ScimTokenModalProps = {
  token: string
}

const ScimTokenModal: FC<ScimTokenModalProps> = ({ token }) => {
  const onCopy = () => Utils.copyToClipboard(token)

  return (
    <div className='create-feature-tab px-3 mt-3'>
      <div className='alert alert-warning d-flex gap-2 align-items-start mb-3'>
        <Icon name='warning' width={20} />
        <div>
          <strong>Copy this token now.</strong> It will not be retrievable later
          — store it somewhere secure before closing this dialogue.
        </div>
      </div>
      <InputGroup
        title='SCIM bearer token'
        className='mt-2'
        component={
          <Row>
            <Flex>
              <Input
                value={token}
                inputProps={{ readOnly: true }}
                data-test='scim-token-value'
              />
            </Flex>
            <Button
              theme='secondary'
              className='ms-2'
              onClick={onCopy}
              data-test='scim-token-copy'
            >
              Copy
            </Button>
          </Row>
        }
      />
      <div className='text-right mt-4'>
        <Button onClick={() => closeModal()} data-test='scim-token-done'>
          Done
        </Button>
      </div>
    </div>
  )
}

ScimTokenModal.displayName = 'ScimTokenModal'

export default ScimTokenModal
