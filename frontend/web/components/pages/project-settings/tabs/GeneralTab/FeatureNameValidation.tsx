import React, { FC, useRef } from 'react'
import Setting from 'components/Setting'
import RegexTester from 'components/RegexTester'
import Utils from 'common/utils/utils'

type FeatureNameValidationProps = {
  featureNameRegex: string | null
  onToggle: () => void
  onChange: (regex: string) => void
  onSave: () => void
  isSaving: boolean
}

export const FeatureNameValidation: FC<FeatureNameValidationProps> = ({
  featureNameRegex,
  isSaving,
  onChange,
  onSave,
  onToggle,
}) => {
  const inputRef = useRef<HTMLInputElement>(null)
  const featureRegexEnabled = typeof featureNameRegex === 'string'

  let regexValid = true
  if (featureNameRegex) {
    try {
      new RegExp(featureNameRegex)
    } catch (e) {
      regexValid = false
    }
  }

  const forceSelectionRange = (e: React.MouseEvent | React.KeyboardEvent) => {
    const input = e.currentTarget as HTMLInputElement
    setTimeout(() => {
      const range = input.selectionStart || 0
      if (range === input.value.length) {
        input.setSelectionRange(input.value.length - 1, input.value.length - 1)
      }
    }, 0)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (regexValid) {
      onSave()
    }
  }

  const handleRegexChange = (e: InputEvent) => {
    let newRegex = Utils.safeParseEventValue(e).replace('$', '')
    if (!newRegex.startsWith('^')) {
      newRegex = `^${newRegex}`
    }
    if (!newRegex.endsWith('$')) {
      newRegex = `${newRegex}$`
    }
    onChange(newRegex)
  }

  const openRegexTester = () => {
    openModal(
      <span>RegEx Tester</span>,
      <RegexTester
        regex={featureNameRegex || ''}
        onChange={(newRegex: string) => onChange(newRegex)}
      />,
    )
  }

  return (
    <FormGroup className='d-flex flex-column gap-2 ml-0'>
      <Setting
        title='Feature name RegEx'
        data-test='js-flag-case-sensitivity'
        disabled={isSaving}
        description={`This allows you to define a regular expression that
                          all feature names must adhere to.`}
        onChange={onToggle}
        checked={featureRegexEnabled}
      />
      {featureRegexEnabled && (
        <InputGroup
          title='Feature Name RegEx'
          component={
            <form onSubmit={handleSubmit}>
              <Row>
                <Flex>
                  <Input
                    ref={inputRef}
                    value={featureNameRegex || ''}
                    inputClassName='input input--wide'
                    name='feature-name-regex'
                    onClick={forceSelectionRange}
                    onKeyUp={forceSelectionRange}
                    showSuccess
                    onChange={handleRegexChange}
                    isValid={regexValid}
                    type='text'
                    placeholder='Regular Expression'
                  />
                </Flex>
                <Button className='ml-2' type='submit' disabled={!regexValid}>
                  Save
                </Button>
                <Button
                  theme='text'
                  type='button'
                  onClick={openRegexTester}
                  className='ml-2'
                  disabled={!regexValid}
                >
                  Test RegEx
                </Button>
              </Row>
            </form>
          }
        />
      )}
    </FormGroup>
  )
}
