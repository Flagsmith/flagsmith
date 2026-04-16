import React, { FC, useMemo, useState } from 'react'
import Button from 'components/base/forms/Button'
import EmptyState from 'components/EmptyState'
import Input from 'components/base/forms/Input'
import SearchableSelect from 'components/base/select/SearchableSelect'
import VariationTable from 'components/experiments-v2/shared/VariationTable'
import { OptionType } from 'components/base/select/SearchableSelect'
import { MOCK_FLAGS, Variation } from 'components/experiments-v2/types'
import './FlagVariationsStep.scss'

type FlagVariationsStepProps = {
  featureFlagId: string | null
  variations: Variation[]
  onFlagChange: (flagId: string) => void
  onVariationsChange: (variations: Variation[]) => void
}

const FlagVariationsStep: FC<FlagVariationsStepProps> = ({
  featureFlagId,
  onFlagChange,
  onVariationsChange,
  variations,
}) => {
  const [showAddForm, setShowAddForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [newValue, setNewValue] = useState('')

  const handleAddVariation = () => {
    if (!newName) return

    const newVariation: Variation = {
      colour: 'var(--orange-500)',
      description: newDescription,
      id: `var-${Date.now()}`,
      name: newName,
      value: newValue || 'false',
    }
    onVariationsChange([...variations, newVariation])
    setNewName('')
    setNewDescription('')
    setNewValue('')
    setShowAddForm(false)
  }

  const handleRemove = (id: string) => {
    onVariationsChange(variations.filter((v) => v.id !== id))
  }

  const eligibleFlags = useMemo(
    () => MOCK_FLAGS.filter((f) => f.isMultiVariant),
    [],
  )

  if (eligibleFlags.length === 0) {
    return (
      <div className='flag-variations-step'>
        <EmptyState
          title='No multi-variant flags'
          description='Experiments require a multi-variant feature flag. Create one first, then come back to set up your experiment.'
          icon='features'
        />
      </div>
    )
  }

  return (
    <div className='flag-variations-step'>
      <div className='flag-variations-step__field'>
        <label className='flag-variations-step__label'>Feature Flag</label>
        <SearchableSelect
          value={featureFlagId}
          onChange={(opt: OptionType) => {
            onFlagChange(opt.value)
          }}
          options={eligibleFlags}
          placeholder='Select a feature flag...'
        />
        <span className='flag-variations-step__hint text-muted fs-small'>
          Only multi-variant flags can be experimented on.
        </span>
      </div>

      <div className='flag-variations-step__field'>
        <label className='flag-variations-step__label'>Variations</label>
        <VariationTable
          variations={variations}
          editable
          onRemove={handleRemove}
        />
      </div>

      {showAddForm ? (
        <div className='flag-variations-step__add-form'>
          <Input
            value={newName}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setNewName(e.target.value)
            }
            placeholder='Variation name'
          />
          <Input
            value={newDescription}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setNewDescription(e.target.value)
            }
            placeholder='Description'
          />
          <Input
            value={newValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setNewValue(e.target.value)
            }
            placeholder='Value'
          />
          <div className='flag-variations-step__add-actions'>
            <Button
              theme='outline'
              size='small'
              onClick={() => setShowAddForm(false)}
            >
              Cancel
            </Button>
            <Button theme='primary' size='small' onClick={handleAddVariation}>
              Add
            </Button>
          </div>
        </div>
      ) : (
        <Button
          theme='outline'
          size='small'
          iconLeft='plus'
          onClick={() => setShowAddForm(true)}
        >
          Add Variation
        </Button>
      )}
    </div>
  )
}

FlagVariationsStep.displayName = 'FlagVariationsStep'
export default FlagVariationsStep
