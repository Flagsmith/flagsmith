import React, { FC, useState } from 'react'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { colorIconAction, colorIconSecondary } from 'common/theme/tokens'
import './VariationKeyLabel.scss'

interface VariationKeyLabelProps {
  // The variant's `key`, surfaced in the UI as its "Label".
  value?: string | null
  index: number
  disabled?: boolean
  readOnly?: boolean
  // Keys of the other variations, used to enforce per-feature uniqueness.
  siblingKeys: (string | null | undefined)[]
  onChange: (key: string | null) => void
}

// Mirrors the backend `validate_slug` rule for the multivariate option key.
const VARIANT_KEY_REGEX = /^[a-zA-Z0-9_-]+$/

export const VariationKeyLabel: FC<VariationKeyLabelProps> = ({
  disabled,
  index,
  onChange,
  readOnly,
  siblingKeys,
  value,
}) => {
  const [isEditing, setIsEditing] = useState(false)
  const [draft, setDraft] = useState(value ?? '')
  const [error, setError] = useState<string | null>(null)

  const canEdit = !readOnly && !disabled
  // Fallback label when none is set — persisted on save by the provider.
  const displayName = value || Utils.getDefaultVariantKey(index)

  // Validates the raw input — trimming here would hide a trailing
  // space from the user until their next keystroke.
  const validate = (next: string): string | null => {
    if (!next) {
      // Empty clears the label (key persists as null).
      return null
    }
    if (next.length > Constants.forms.maxLength.VARIANT_KEY) {
      return `Label must be ${Constants.forms.maxLength.VARIANT_KEY} characters or fewer.`
    }
    if (!VARIANT_KEY_REGEX.test(next)) {
      return 'Label can only contain letters, numbers, hyphens and underscores.'
    }
    if (next === Constants.strings.RESERVED_VARIANT_KEY) {
      return `"${Constants.strings.RESERVED_VARIANT_KEY}" is a reserved label.`
    }
    if (siblingKeys.some((key) => key === next)) {
      return 'This label is already used by another variation.'
    }
    return null
  }

  const startEditing = () => {
    setDraft(value ?? '')
    setError(null)
    setIsEditing(true)
  }

  const cancel = () => {
    setDraft(value ?? '')
    setError(null)
    setIsEditing(false)
  }

  const commit = () => {
    if (error) {
      return
    }
    onChange(draft || null)
    setError(null)
    setIsEditing(false)
  }

  if (isEditing && canEdit) {
    return (
      <div>
        <Row className='align-items-center gap-3'>
          <Input
            autoFocus
            size='small'
            underline
            className='variation-key-label__input'
            data-test={`featureVariationKeyInput${index}`}
            value={draft}
            isValid={!error}
            maxLength={Constants.forms.maxLength.VARIANT_KEY}
            placeholder={Utils.getDefaultVariantKey(index)}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
              const next = Utils.safeParseEventValue(e).replace(/ /g, '_')
              setDraft(next)
              setError(validate(next))
            }}
            // An invalid draft must not be committed — keep the row in edit
            // mode with the error visible instead.
            onBlur={() => {
              if (!error) {
                commit()
              }
            }}
            // Escape is left to bubble up and close the modal.
            onKeyDown={(e: React.KeyboardEvent<HTMLInputElement>) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                commit()
              }
            }}
          />
          <div className='d-flex align-items-center gap-1'>
            <Button
              theme='text'
              disabled={!!error}
              onClick={commit}
              onMouseDown={(e) => e.preventDefault()}
              data-test={`featureVariationKeySave${index}`}
              aria-label='Save label'
            >
              <Icon
                name='checkmark-circle'
                width={20}
                fill={error ? colorIconSecondary : colorIconAction}
              />
            </Button>
            <Button
              theme='text'
              onClick={cancel}
              onMouseDown={(e) => e.preventDefault()}
              aria-label='Cancel'
            >
              <Icon name='close-circle' width={20} fill={colorIconSecondary} />
            </Button>
          </div>
        </Row>
        {!!error && <span className='text-danger text-small'>{error}</span>}
      </div>
    )
  }

  return (
    <Row className='align-items-center'>
      <span
        className='h6 mb-0 font-weight-semibold'
        data-test={`featureVariationKey${index}`}
      >
        {displayName}
      </span>
      {canEdit && (
        <Button
          theme='text'
          className='text-primary ml-2'
          onClick={startEditing}
          data-test={`featureVariationKeyEdit${index}`}
          aria-label='Edit label'
        >
          <Icon name='edit' width={16} />
        </Button>
      )}
    </Row>
  )
}
