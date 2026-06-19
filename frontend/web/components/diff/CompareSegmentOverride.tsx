import React, { FC, useState } from 'react'
import InfoMessage from 'components/InfoMessage'
import DiffFeatureStateValues from './DiffFeatureStateValues'
import useCompareTargets, {
  CompareSource,
  CompareTarget,
} from './useCompareTargets'

type CompareSegmentOverrideType = {
  projectId: number | string
  environmentId: string
  featureId: number
  source: CompareTarget
  sourceDescriptor: CompareSource
}

const hasDifference = (source: CompareTarget, target: CompareTarget) =>
  source.enabled !== target.enabled || `${source.value}` !== `${target.value}`

const CompareSegmentOverride: FC<CompareSegmentOverrideType> = ({
  environmentId,
  featureId,
  projectId,
  source,
  sourceDescriptor,
}) => {
  const { isLoading, targets } = useCompareTargets({
    environmentId,
    featureId,
    projectId,
    source: sourceDescriptor,
  })
  const [targetIndex, setTargetIndex] = useState(0)
  const target = targets[targetIndex] ?? targets[0]

  const flatOptions = targets.map((t, index) => ({
    label: t.label,
    value: index,
  }))
  const groupedOptions = targets.reduce<
    { label: string; options: { label: string; value: number }[] }[]
  >((groups, t, index) => {
    const group = groups.find((g) => g.label === t.group)
    const option = { label: t.label, value: index }
    if (group) {
      group.options.push(option)
    } else {
      groups.push({ label: t.group, options: [option] })
    }
    return groups
  }, [])
  // Segment overrides first, then environment defaults.
  const groupOrder = ['Segment Overrides', 'Environment Defaults']
  groupedOptions.sort(
    (a, b) => groupOrder.indexOf(a.label) - groupOrder.indexOf(b.label),
  )
  const selectedOption = flatOptions[targetIndex] ?? flatOptions[0]

  const changed = !!target && hasDifference(source, target)

  const renderBody = () => {
    if (isLoading && !targets.length) {
      return (
        <div className='text-center'>
          <Loader />
        </div>
      )
    }
    if (!target) {
      return (
        <InfoMessage>There is nothing to compare this override to.</InfoMessage>
      )
    }
    if (!changed) {
      return (
        <InfoMessage>
          <strong>{source.label}</strong> and <strong>{target.label}</strong>{' '}
          are identical — no differences in enabled state or value.
        </InfoMessage>
      )
    }
    return (
      <DiffFeatureStateValues
        enabled={{ newValue: source.enabled, oldValue: target.enabled }}
        value={{ newValue: source.value, oldValue: target.value }}
      />
    )
  }

  return (
    <div>
      <div className='d-flex align-items-center gap-2 mb-3'>
        <label className='mb-0'>
          Comparing <strong>{source.label}</strong> against
        </label>
        <div className='flex-fill'>
          <Select
            value={selectedOption}
            options={groupedOptions}
            onChange={(option: { value: number }) =>
              setTargetIndex(option.value)
            }
          />
        </div>
      </div>
      {renderBody()}
    </div>
  )
}

export default CompareSegmentOverride
