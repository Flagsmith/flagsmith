import { ChangeEvent, FC, useCallback, useMemo, useState } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import ColorSwatch from 'components/ColorSwatch'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { Experiment, ExpectedDirection } from 'common/types/responses'
import { useUpdateExperimentMutation } from 'common/services/useExperiment'
import { getPrimaryMetric } from 'components/experiments/constants'
import {
  VariationSplitEntry,
  getControlPercentage,
} from 'components/experiments/rollout'
import { getVariantIdentities } from './derive'
import './results.scss'

const EXPECTED_DIRECTION_CHIP: Record<ExpectedDirection, string> = {
  decrease: '↓ should decrease',
  increase: '↑ should increase',
  not_decrease: 'should not decrease',
  not_increase: 'should not increase',
}

type ExperimentConfigurationProps = {
  experiment: Experiment
  environmentId: string
}

const ExperimentConfiguration: FC<ExperimentConfigurationProps> = ({
  environmentId,
  experiment,
}) => {
  const metric = getPrimaryMetric(experiment)
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )

  const treatmentTotal = (experiment.feature.multivariate_options ?? []).reduce(
    (sum, mv) => sum + mv.default_percentage_allocation,
    0,
  )

  const getAllocation = (index: number): number =>
    index === 0
      ? 100 - treatmentTotal
      : experiment.feature.multivariate_options?.[index - 1]
          ?.default_percentage_allocation ?? 0

  const [updateExperiment, { isLoading: isSaving }] =
    useUpdateExperimentMutation()

  const [isEditing, setIsEditing] = useState(false)
  const [draftRollout, setDraftRollout] = useState(0)
  const [draftSplit, setDraftSplit] = useState<VariationSplitEntry[]>([])

  const startEditing = useCallback(() => {
    setDraftRollout(experiment.rollout_percentage ?? 100)
    setDraftSplit(
      (experiment.feature.multivariate_options ?? []).map((mv) => ({
        multivariate_feature_option: mv.id,
        percentage_allocation: mv.default_percentage_allocation,
      })),
    )
    setIsEditing(true)
  }, [experiment])

  const cancelEditing = () => setIsEditing(false)

  const handleSave = async () => {
    if (isSaving) return
    try {
      await updateExperiment({
        body: {
          experiment_rollout: {
            multivariate_feature_state_values: draftSplit,
            rollout_percentage: draftRollout,
          },
        },
        environmentId,
        experimentId: experiment.id,
      }).unwrap()
      setIsEditing(false)
    } catch {
      toast('Failed to update rollout', 'danger')
    }
  }

  const draftControlPct = isEditing ? getControlPercentage(draftSplit) : 0
  const draftInvalid =
    isEditing && (draftControlPct < 0 || draftControlPct > 100)

  return (
    <div className='row g-3 mb-4'>
      <div className='col-md-4'>
        <ContentCard compact title='Feature flag'>
          <div>
            <span className='selectable-card__tag'>
              {experiment.feature.name}
            </span>
          </div>
        </ContentCard>
      </div>
      <div className='col-md-4'>
        <ContentCard compact title='Primary Metric'>
          {metric ? (
            <div>
              <div>{metric.metric_name}</div>
              <div className='mt-3'>
                <span className='selectable-card__tag'>
                  {EXPECTED_DIRECTION_CHIP[metric.expected_direction]}
                </span>
              </div>
            </div>
          ) : (
            <span className='text-muted'>—</span>
          )}
        </ContentCard>
      </div>
      <div className='col-md-4'>
        <ContentCard
          compact
          title='Variation Split'
          action={
            !isEditing ? (
              <Button
                theme='text'
                onClick={startEditing}
                aria-label='Edit variation split'
              >
                <Icon name='edit' width={14} />
              </Button>
            ) : undefined
          }
        >
          <div className='d-flex flex-column gap-2'>
            <div className='d-flex align-items-center justify-content-between'>
              <span className='text-muted'>Rollout</span>
              {isEditing ? (
                <span className='d-flex align-items-center gap-1'>
                  <Input
                    type='number'
                    size='xSmall'
                    underline
                    centered
                    style={{ width: 56 }}
                    value={draftRollout}
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                      const val = Utils.safeParseEventValue(e)
                      setDraftRollout(val ? parseFloat(val) : 0)
                    }}
                  />
                  <span className='text-muted'>%</span>
                </span>
              ) : (
                <span className='text-muted'>
                  {experiment.rollout_percentage ?? 100}%
                </span>
              )}
            </div>

            {identities.map((v, i) => {
              const isControl = i === 0
              const optionId =
                experiment.feature.multivariate_options?.[i - 1]?.id
              let currentPct: number
              if (!isEditing) {
                currentPct = Math.round(getAllocation(i))
              } else if (isControl) {
                currentPct = Math.max(0, draftControlPct)
              } else {
                currentPct =
                  draftSplit.find(
                    (s) => s.multivariate_feature_option === optionId,
                  )?.percentage_allocation ?? 0
              }

              return (
                <div
                  key={v.key}
                  className='d-flex align-items-center justify-content-between'
                >
                  <span className='d-flex align-items-center gap-2'>
                    <ColorSwatch color={v.colour} size='sm' shape='circle' />
                    <span>{v.name}</span>
                  </span>
                  {isEditing && !isControl ? (
                    <span className='d-flex align-items-center gap-1'>
                      <Input
                        type='number'
                        size='xSmall'
                        underline
                        centered
                        style={{ width: 56 }}
                        value={currentPct}
                        onChange={(e: ChangeEvent<HTMLInputElement>) => {
                          const val = Utils.safeParseEventValue(e)
                          setDraftSplit((prev) =>
                            prev.map((entry) =>
                              entry.multivariate_feature_option === optionId
                                ? {
                                    ...entry,
                                    percentage_allocation: val
                                      ? parseFloat(val)
                                      : 0,
                                  }
                                : entry,
                            ),
                          )
                        }}
                      />
                      <span className='text-muted'>%</span>
                    </span>
                  ) : (
                    <span className='text-muted'>
                      {Math.round(currentPct)}%
                    </span>
                  )}
                </div>
              )
            })}

            {isEditing && (
              <div className='d-flex justify-content-end gap-2 mt-2'>
                <Button
                  theme='text'
                  size='xSmall'
                  onClick={cancelEditing}
                  disabled={isSaving}
                >
                  Cancel
                </Button>
                <Button
                  size='xSmall'
                  onClick={handleSave}
                  disabled={isSaving || draftInvalid}
                >
                  Save
                </Button>
              </div>
            )}
          </div>
        </ContentCard>
      </div>
    </div>
  )
}

export default ExperimentConfiguration
