import React, { FC } from 'react'
import InputGroup from 'components/base/forms/InputGroup'
import Tooltip from 'components/Tooltip'
import Icon from 'components/Icon'
import InfoMessage from 'components/InfoMessage'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import FormGroup from 'components/base/grid/FormGroup'
import Row from 'components/base/grid/Row'

type FeatureNameInputProps = {
  value: string
  onChange: (name: string) => void
  caseSensitive: boolean
  regex?: string
  regexValid: boolean
  autoFocus?: boolean
}

const FeatureNameInput: FC<FeatureNameInputProps> = ({
  autoFocus,
  caseSensitive,
  onChange,
  regex,
  regexValid,
  value,
}) => {
  const FEATURE_ID_MAXLENGTH = Constants.forms.maxLength.FEATURE_ID

  return (
    <FormGroup className='mb-4 mt-2'>
      <InputGroup
        autoFocus={autoFocus}
        data-test='featureID'
        inputProps={{
          className: 'full-width',
          maxLength: FEATURE_ID_MAXLENGTH,
          name: 'featureID',
          readOnly: false,
        }}
        value={value}
        onChange={(e: InputEvent) => {
          const newName = Utils.safeParseEventValue(e).replace(/ /g, '_')
          onChange(caseSensitive ? newName.toLowerCase() : newName)
        }}
        isValid={!!value && regexValid}
        type='text'
        title={
          <>
            <Tooltip
              title={
                <Row>
                  <span className={'mr-1'}>ID / Name*</span>
                  <Icon name='info-outlined' />
                </Row>
              }
            >
              The ID that will be used by SDKs to retrieve the feature value and
              enabled state. This cannot be edited once the feature has been
              created.
            </Tooltip>
            {!!regex && (
              <div className='mt-2'>
                {' '}
                <InfoMessage collapseId={'flag-regex'}>
                  {' '}
                  This must conform to the regular expression <pre>{regex}</pre>
                </InfoMessage>
              </div>
            )}
          </>
        }
        placeholder='E.g. header_size'
      />
    </FormGroup>
  )
}

export default FeatureNameInput
