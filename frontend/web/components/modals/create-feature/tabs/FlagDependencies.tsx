import { FC, useMemo, useState } from 'react'
import Button from 'components/base/forms/Button'
import InlinePillToggle from 'components/base/forms/InlinePillToggle'
import Panel from 'components/base/grid/Panel'
import EmptyState from 'components/EmptyState'
import ErrorMessage from 'components/ErrorMessage'
import Icon from 'components/icons/Icon'
import InfoMessage from 'components/InfoMessage'
import ModalHR from 'components/modals/ModalHR'
import Switch from 'components/Switch'
import WarningMessage from 'components/WarningMessage'

// TODO: this tab is a mock up — nothing here is persisted and no API is called.
// The catalogue below stands in for the project's features and their current
// state in this environment.

const DOCS_URL = 'https://docs.flagsmith.com/managing-flags/flag-dependencies'
const MAX_PREREQUISITES = 5
const COLOUR_MET = '#27ab95'
const COLOUR_UNMET = '#9da4af'
const COLOUR_ICON = '#656d7b'

// Dependencies are only one layer deep, so a feature is in exactly one of these
// two states. The mock up switches between them so both can be screenshotted.
type MockScenario = 'has-prerequisites' | 'is-prerequisite'

type MockFlag = {
  id: number
  name: string
  /** Whether the flag is currently enabled in this environment. */
  enabled: boolean
  /** Flags with prerequisites of their own would form a second layer. */
  hasPrerequisites?: boolean
}

type MockDependentFlag = {
  id: number
  name: string
  requires: string
}

type Prerequisite = {
  key: number
  featureId: number | null
  requiredEnabled: boolean
}

type SelectOption = {
  label: string
  value: number
  isDisabled?: boolean
  description?: string
}

const MOCK_FLAGS: MockFlag[] = [
  { enabled: true, id: 101, name: 'billing_engine_v2' },
  { enabled: false, id: 102, name: 'checkout_redesign' },
  { enabled: true, id: 103, name: 'payment_provider' },
  { enabled: true, id: 104, name: 'dark_mode' },
  { enabled: true, hasPrerequisites: true, id: 105, name: 'search_ranking' },
  { enabled: false, id: 106, name: 'beta_programme' },
  {
    enabled: true,
    hasPrerequisites: true,
    id: 107,
    name: 'checkout_express_lane',
  },
  { enabled: false, hasPrerequisites: true, id: 108, name: 'one_click_pay' },
]

const MOCK_DEPENDENT_FLAGS: MockDependentFlag[] = [
  { id: 107, name: 'checkout_express_lane', requires: 'Enabled' },
  { id: 108, name: 'one_click_pay', requires: 'Enabled' },
]

const MOCK_PREREQUISITES: Prerequisite[] = [
  { featureId: 101, key: 1, requiredEnabled: true },
  { featureId: 103, key: 2, requiredEnabled: true },
]

const SCENARIO_OPTIONS: { label: string; value: MockScenario }[] = [
  { label: 'Has prerequisites', value: 'has-prerequisites' },
  { label: 'Is a prerequisite', value: 'is-prerequisite' },
]

const getFlag = (featureId: number | null) =>
  MOCK_FLAGS.find((flag) => flag.id === featureId)

// A prerequisite is met when the prerequisite flag is in the required state.
const isMet = (prerequisite: Prerequisite) => {
  const flag = getFlag(prerequisite.featureId)
  return !!flag && flag.enabled === prerequisite.requiredEnabled
}

const listNames = (names: string[]) =>
  names.length > 1
    ? `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`
    : names[0]

type FlagDependenciesProps = {
  featureName?: string
  environmentName?: string
}

const FlagDependencies: FC<FlagDependenciesProps> = ({
  environmentName = 'Production',
  featureName = 'This feature',
}) => {
  const [scenario, setScenario] = useState<MockScenario>('has-prerequisites')
  const [prerequisites, setPrerequisites] =
    useState<Prerequisite[]>(MOCK_PREREQUISITES)
  const [nextKey, setNextKey] = useState(MOCK_PREREQUISITES.length + 1)
  const [isDirty, setIsDirty] = useState(false)

  const isPrerequisite = scenario === 'is-prerequisite'
  const dependentFlags = isPrerequisite ? MOCK_DEPENDENT_FLAGS : []

  const changeScenario = (value: MockScenario) => {
    setScenario(value)
    setPrerequisites(value === 'has-prerequisites' ? MOCK_PREREQUISITES : [])
    setNextKey(MOCK_PREREQUISITES.length + 1)
    setIsDirty(false)
  }

  const updatePrerequisites = (value: Prerequisite[]) => {
    setPrerequisites(value)
    setIsDirty(true)
  }

  const addPrerequisite = () => {
    updatePrerequisites(
      prerequisites.concat({
        featureId: null,
        key: nextKey,
        requiredEnabled: true,
      }),
    )
    setNextKey(nextKey + 1)
  }

  const removePrerequisite = (key: number) => {
    updatePrerequisites(prerequisites.filter((p) => p.key !== key))
  }

  const changePrerequisite = (key: number, changes: Partial<Prerequisite>) => {
    updatePrerequisites(
      prerequisites.map((p) => (p.key === key ? { ...p, ...changes } : p)),
    )
  }

  const selectedIds = prerequisites
    .map((p) => p.featureId)
    .filter((id): id is number => id !== null)

  const dependentNames = dependentFlags.map((flag) => flag.name)

  // A feature that other features already depend on cannot take prerequisites
  // of its own, and a flag that has its own prerequisites cannot become one.
  const lockedReason = dependentFlags.length
    ? `Other features already depend on this feature. Dependencies are only one layer deep, so it cannot have prerequisites of its own.`
    : ''

  const flagOptions: SelectOption[] = useMemo(
    () =>
      MOCK_FLAGS.map((flag) => ({
        description: flag.hasPrerequisites
          ? 'Already depends on other features'
          : undefined,
        isDisabled: !!flag.hasPrerequisites,
        label: flag.name,
        value: flag.id,
      })),
    [],
  )

  const unmetCount = prerequisites.filter(
    (p) => p.featureId !== null && !isMet(p),
  ).length
  const incompleteCount = prerequisites.filter((p) => !p.featureId).length
  const atLimit = prerequisites.length >= MAX_PREREQUISITES
  const canAdd = !lockedReason && !atLimit

  const addDisabledReason = () => {
    if (lockedReason) {
      return lockedReason
    }
    if (atLimit) {
      return `You can add up to ${MAX_PREREQUISITES} prerequisites to a feature.`
    }
    return ''
  }

  const renderPrerequisite = (prerequisite: Prerequisite) => {
    const met = prerequisite.featureId !== null && isMet(prerequisite)

    return (
      <Row className='list-item overflow-visible' key={prerequisite.key}>
        <div className='table-column text-center' style={{ width: '50px' }}>
          {prerequisite.featureId !== null && (
            <Tooltip
              title={
                <Icon
                  name={met ? 'checkmark-circle' : 'minus-circle'}
                  width={20}
                  fill={met ? COLOUR_MET : COLOUR_UNMET}
                />
              }
              place='top'
            >
              {met
                ? 'This prerequisite is currently met.'
                : `This prerequisite is not met, so ${featureName} is serving its disabled value.`}
            </Tooltip>
          )}
        </div>
        <Flex className='table-column overflow-visible'>
          <Select
            value={
              flagOptions.find((o) => o.value === prerequisite.featureId) ||
              null
            }
            placeholder='Select a flag'
            options={flagOptions.filter(
              (o) =>
                o.value === prerequisite.featureId ||
                !selectedIds.includes(o.value),
            )}
            onChange={(option: SelectOption) =>
              changePrerequisite(prerequisite.key, {
                featureId: option.value,
              })
            }
          />
        </Flex>
        <div className='table-column' style={{ width: '150px' }}>
          <Row className='gap-2'>
            <Switch
              checked={prerequisite.requiredEnabled}
              onChange={(requiredEnabled: boolean) =>
                changePrerequisite(prerequisite.key, { requiredEnabled })
              }
            />
            <span className='text-muted'>
              {prerequisite.requiredEnabled ? 'Enabled' : 'Disabled'}
            </span>
          </Row>
        </div>
        <div className='table-column text-center' style={{ width: '80px' }}>
          <Button
            theme='text'
            className='btn btn-with-icon'
            onClick={() => removePrerequisite(prerequisite.key)}
          >
            <Icon name='trash-2' width={20} fill={COLOUR_ICON} />
          </Button>
        </div>
      </Row>
    )
  }

  return (
    <FormGroup className='mb-4'>
      <Row className='align-items-center mb-2 gap-4'>
        <div className='flex-fill'>
          <Tooltip
            title={
              <h5 className='mb-0'>
                Flag Dependencies <Icon name='info-outlined' />
              </h5>
            }
            place='top'
          >
            Gate this feature behind other features. Dependencies are evaluated
            before targeting rules, segment overrides and identity overrides.
          </Tooltip>
        </div>
        <div className='text-right'>
          <Tooltip
            title={
              <Button
                size='small'
                theme='outline'
                disabled={!canAdd}
                onClick={addPrerequisite}
                data-test='add-prerequisite-btn'
              >
                Add Prerequisite
              </Button>
            }
            place='left'
          >
            {addDisabledReason()}
          </Tooltip>
        </div>
      </Row>
      <div className='text-muted mb-2'>
        <p>
          A prerequisite is met when the prerequisite flag is in the state you
          specify for this environment.
          <a href={DOCS_URL} target='_blank' rel='noreferrer'>
          Learn more
          </a>
        </p>
      </div>

      {!!incompleteCount && (
        <ErrorMessage
          error={`Select a flag for ${incompleteCount} incomplete ${
            incompleteCount === 1 ? 'prerequisite' : 'prerequisites'
          } before saving.`}
        />
      )}

      {!!unmetCount && (
        <WarningMessage
          warningMessage={
            <>
              {unmetCount === 1
                ? '1 prerequisite is '
                : `${unmetCount} prerequisites are `}
              not currently met, so <strong>{featureName}</strong> is serving
              its disabled value in <strong>{environmentName}</strong>.
            </>
          }
        />
      )}

      <Panel className='no-pad overflow-visible mt-2'>
        {prerequisites.length ? (
          <>
            <Row className='table-header'>
              <div
                className='table-column text-center'
                style={{ width: '50px' }}
              >
                {''}
              </div>
              <Flex className='table-column'>Prerequisite flag</Flex>
              <div className='table-column' style={{ width: '150px' }}>
                Must be
              </div>
              <div
                className='table-column text-center'
                style={{ width: '80px' }}
              >
                {''}
              </div>
            </Row>
            {prerequisites.map(renderPrerequisite)}
          </>
        ) : (
          <EmptyState
            className='p-4'
            icon='layers'
            title={
              lockedReason ? 'Prerequisites unavailable' : 'No prerequisites'
            }
            description={
              lockedReason ||
              `${featureName} is evaluated independently of every other feature. Add a prerequisite to gate it behind another flag.`
            }
            docsUrl={DOCS_URL}
            action={
              canAdd ? (
                <Button
                  className='mt-2'
                  size='small'
                  theme='outline'
                  onClick={addPrerequisite}
                >
                  Add Prerequisite
                </Button>
              ) : undefined
            }
          />
        )}
      </Panel>

      <ModalHR className='mt-4' />

      <h5 className='mt-4 mb-2'>Dependent features</h5>
      <div className='text-muted mb-2'>
        These features list <strong>{featureName}</strong> as a prerequisite.
        They will serve their disabled value whenever this feature does not meet
        their requirement.
      </div>
      <Panel className='no-pad overflow-visible'>
        {dependentFlags.length ? (
          <>
            <Row className='table-header'>
              <Flex className='table-column'>Feature</Flex>
              <div className='table-column' style={{ width: '200px' }}>
                Requires this feature to be
              </div>
            </Row>
            {dependentFlags.map((flag) => (
              <Row className='list-item' key={flag.id}>
                <Flex className='table-column font-weight-medium'>
                  {flag.name}
                </Flex>
                <div className='table-column' style={{ width: '200px' }}>
                  <span className='chip chip--xs'>{flag.requires}</span>
                </div>
              </Row>
            ))}
          </>
        ) : (
          <EmptyState
            className='p-4'
            icon='layers'
            title='No dependent features'
            description={
              prerequisites.length
                ? `${featureName} has prerequisites of its own. Dependencies are only one layer deep, so other features cannot depend on it.`
                : 'No other features depend on this one.'
            }
          />
        )}
      </Panel>

      <ModalHR className='mt-4' />

      <p className='text-right mt-4 fs-small lh-sm modal-caption'>
        This will update the flag dependencies for the environment{' '}
        <strong>{environmentName}</strong>
      </p>
      <div className='text-right'>
        <Button
          data-test='update-flag-dependencies-btn'
          disabled={!isDirty || !!incompleteCount}
          onClick={() => {
            setIsDirty(false)
            toast('Flag dependencies updated')
          }}
        >
          Update Dependencies
        </Button>
      </div>

      {/* Mock up only — lets both states of the tab be screenshotted. */}
      <ModalHR className='mt-4' />
      <Row className='mt-4 gap-2 align-items-center'>
        <span className='text-muted fs-small'>Mock up preview</span>
        <InlinePillToggle
          size='small'
          options={SCENARIO_OPTIONS}
          value={scenario}
          onChange={changeScenario}
          data-test='flag-dependencies-scenario'
        />
      </Row>
    </FormGroup>
  )
}

export default FlagDependencies
