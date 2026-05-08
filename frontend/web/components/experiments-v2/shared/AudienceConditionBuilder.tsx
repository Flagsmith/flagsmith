import React, { FC, useCallback, useMemo } from 'react'
import Button from 'components/base/forms/Button'
import Input from 'components/base/forms/Input'
import SearchableSelect, {
  OptionType,
} from 'components/base/select/SearchableSelect'
import Icon from 'components/icons/Icon'
import {
  AUDIENCE_OPERATOR_LABELS,
  AudienceCondition,
  AudienceOperator,
  MOCK_AUDIENCE_ATTRIBUTES,
  VALUELESS_OPERATORS,
} from 'components/experiments-v2/types'
import './AudienceConditionBuilder.scss'

type AudienceConditionBuilderProps = {
  conditions: AudienceCondition[]
  onChange: (conditions: AudienceCondition[]) => void
}

const newConditionId = () =>
  `cond-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`

const makeBlankCondition = (): AudienceCondition => ({
  id: newConditionId(),
  operator: 'EQUAL',
  property: MOCK_AUDIENCE_ATTRIBUTES[0]?.value ?? 'identity_id',
  value: '',
})

const operatorOptions: OptionType[] = (
  Object.keys(AUDIENCE_OPERATOR_LABELS) as AudienceOperator[]
).map((op) => ({ label: AUDIENCE_OPERATOR_LABELS[op], value: op }))

const AudienceConditionBuilder: FC<AudienceConditionBuilderProps> = ({
  conditions,
  onChange,
}) => {
  const attributeOptions = useMemo<OptionType[]>(
    () =>
      MOCK_AUDIENCE_ATTRIBUTES.map((attr) => ({
        label: attr.label,
        value: attr.value,
      })),
    [],
  )

  const handleAdd = useCallback(() => {
    onChange([...conditions, makeBlankCondition()])
  }, [conditions, onChange])

  const handleRemove = useCallback(
    (id: string) => {
      onChange(conditions.filter((c) => c.id !== id))
    },
    [conditions, onChange],
  )

  const handleUpdate = useCallback(
    (id: string, patch: Partial<AudienceCondition>) => {
      onChange(
        conditions.map((c) => {
          if (c.id !== id) return c
          const next = { ...c, ...patch }
          // If the operator becomes valueless, clear any stored value to
          // keep the data model honest.
          if (
            patch.operator !== undefined &&
            VALUELESS_OPERATORS.includes(patch.operator)
          ) {
            next.value = ''
          }
          return next
        }),
      )
    },
    [conditions, onChange],
  )

  if (conditions.length === 0) {
    return (
      <div className='audience-condition-builder audience-condition-builder--empty'>
        <div className='audience-condition-builder__empty-content'>
          <Icon name='people' width={20} />
          <div>
            <strong>All identities in this environment</strong>
            <p className='text-muted fs-small'>
              No targeting conditions — every identity is eligible for the
              experiment. Add a condition to filter the audience.
            </p>
          </div>
        </div>
        <Button
          theme='outline'
          size='small'
          onClick={handleAdd}
          iconLeft='plus'
          iconSize={14}
        >
          Add condition
        </Button>
      </div>
    )
  }

  return (
    <div className='audience-condition-builder'>
      <div className='audience-condition-builder__rows'>
        {conditions.map((condition, index) => {
          const isValueless = VALUELESS_OPERATORS.includes(condition.operator)
          return (
            <div key={condition.id} className='audience-condition-builder__row'>
              <span className='audience-condition-builder__joiner'>
                {index === 0 ? 'IF' : 'AND'}
              </span>

              <div className='audience-condition-builder__select'>
                <SearchableSelect
                  value={condition.property}
                  displayedLabel={
                    attributeOptions.find((a) => a.value === condition.property)
                      ?.label
                  }
                  options={attributeOptions}
                  onChange={(opt: OptionType) =>
                    handleUpdate(condition.id, { property: opt.value })
                  }
                  isSearchable={false}
                  placeholder='Attribute'
                />
              </div>

              <div className='audience-condition-builder__select'>
                <SearchableSelect
                  value={condition.operator}
                  displayedLabel={AUDIENCE_OPERATOR_LABELS[condition.operator]}
                  options={operatorOptions}
                  onChange={(opt: OptionType) =>
                    handleUpdate(condition.id, {
                      operator: opt.value as AudienceOperator,
                    })
                  }
                  isSearchable={false}
                  placeholder='Operator'
                />
              </div>

              {isValueless ? (
                <span className='audience-condition-builder__valueless'>—</span>
              ) : (
                <Input
                  className='audience-condition-builder__value'
                  value={condition.value}
                  placeholder='Value'
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    handleUpdate(condition.id, { value: e.target.value })
                  }
                />
              )}

              <Button
                theme='icon'
                size='xSmall'
                onClick={() => handleRemove(condition.id)}
                aria-label='Remove condition'
              >
                <Icon name='close-circle' width={16} />
              </Button>
            </div>
          )
        })}
      </div>

      <Button
        theme='outline'
        size='small'
        onClick={handleAdd}
        iconLeft='plus'
        iconSize={14}
      >
        Add condition
      </Button>
    </div>
  )
}

AudienceConditionBuilder.displayName = 'AudienceConditionBuilder'
export default AudienceConditionBuilder
