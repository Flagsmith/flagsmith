import React, { useCallback, useMemo, useRef, useState } from 'react'
import Setting from 'components/Setting'
import RegexTester from 'components/RegexTester'
import Utils from 'common/utils/utils'
import { Project } from 'common/types/responses'
import { useUpdateProjectWithToast } from 'components/pages/project-settings/hooks'

type FeatureNameValidationProps = {
  project: Project
}

export const FeatureNameValidation = ({
  project,
}: FeatureNameValidationProps) => {
  const [updateProjectWithToast, { isLoading: isSaving }] =
    useUpdateProjectWithToast()
  const [featureNameRegex, setFeatureNameRegex] = useState<string | null>(
    project.feature_name_regex || null,
  )

  const inputRef = useRef<HTMLInputElement>(null)
  const featureRegexEnabled = typeof featureNameRegex === 'string'

  const handleToggle = useCallback(async () => {
    if (featureNameRegex) {
      setFeatureNameRegex(null)
      await updateProjectWithToast(
        {
          feature_name_regex: null,
          name: project.name,
        },
        project.id,
        {
          errorMessage:
            'Failed to update feature validation. Please try again.',
        },
      )
    } else {
      setFeatureNameRegex('^.+$')
    }
  }, [featureNameRegex, project.name, project.id, updateProjectWithToast])

  const handleSave = useCallback(async () => {
    await updateProjectWithToast(
      {
        feature_name_regex: featureNameRegex,
        name: project.name,
      },
      project.id,
      {
        errorMessage: 'Failed to save regex. Please try again.',
        successMessage: 'Feature name regex saved',
      },
    )
  }, [featureNameRegex, project.name, project.id, updateProjectWithToast])

  const regexValid = useMemo(() => {
    if (!featureNameRegex) return true
    try {
      new RegExp(featureNameRegex)
      return true
    } catch (e) {
      return false
    }
  }, [featureNameRegex])

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
      handleSave()
    }
  }

  const handleRegexChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let newRegex = Utils.safeParseEventValue(e).replace('$', '')
    if (!newRegex.startsWith('^')) {
      newRegex = `^${newRegex}`
    }
    if (!newRegex.endsWith('$')) {
      newRegex = `${newRegex}$`
    }
    setFeatureNameRegex(newRegex)
  }

  const openRegexTester = () => {
    openModal(
      <span>RegEx Tester</span>,
      <RegexTester
        regex={featureNameRegex || ''}
        onChange={(newRegex: string) => setFeatureNameRegex(newRegex)}
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
        onChange={handleToggle}
        checked={featureRegexEnabled}
      />
      <div
        style={{
          height: featureRegexEnabled ? 'auto' : 0,
          opacity: featureRegexEnabled ? 1 : 0,
          transition: 'opacity 0.4s ease-in-out, height 0.4s ease-in-out',
        }}
      >
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
                <Button
                  className='ml-2'
                  type='submit'
                  disabled={!regexValid || isSaving}
                >
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
      </div>
    </FormGroup>
  )
}
