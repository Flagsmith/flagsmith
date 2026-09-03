import { ChangeEvent, FC, useCallback, useMemo, useState } from 'react'
import ContentCard from 'components/base/grid/ContentCard'
import ColorSwatch from 'components/ColorSwatch'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { Experiment } from 'common/types/responses'
import { useUpdateExperimentRolloutMutation } from 'common/services/useExperiment'
import AudienceSegmentList from 'components/experiments/AudienceSegmentList'
import { experimentErrorMessage } from 'components/experiments/errors'
import {
  VariationSplitEntry,
  buildRolloutBody,
  getControlPercentage,
  joinSegmentNames,
} from 'components/experiments/rollout'
import isValidPercentage from 'common/utils/isValidPercentage'
import { getVariantIdentities } from './derive'

type ExperimentRolloutCardProps = {
  experiment: Experiment
  environmentId: string
}

const ExperimentRolloutCard: FC<ExperimentRolloutCardProps> = ({
  environmentId,
  experiment,
}) => {
  const identities = useMemo(
    () => getVariantIdentities(experiment.feature),
    [experiment.feature],
  )

  const rollout = experiment.experiment_rollout
  // The audience is frozen once the experiment starts, so it is display-only.
  const audience = rollout?.audience
  const mvOptions = experiment.feature.multivariate_options ?? []

  const getTreatmentAllocation = (optionId: number): number =>
    rollout
      ? rollout.multivariate_feature_state_values.find(
          (mv) => mv.multivariate_feature_option === optionId,
        )?.percentage_allocation ?? 0
      : mvOptions.find((mv) => mv.id === optionId)
          ?.default_percentage_allocation ?? 0

  const treatmentTotal = mvOptions.reduce(
    (sum, mv) => sum + getTreatmentAllocation(mv.id),
    0,
  )

  const [updateRollout, { isLoading: isSaving }] =
    useUpdateExperimentRolloutMutation()

  const [isEditing, setIsEditing] = useState(false)
  const [draftRollout, setDraftRollout] = useState(0)
  const [draftSplit, setDraftSplit] = useState<VariationSplitEntry[]>([])

  const startEditing = useCallback(() => {
    setDraftRollout(rollout?.rollout_percentage ?? 100)
    setDraftSplit(
      rollout?.multivariate_feature_state_values ??
        (experiment.feature.multivariate_options ?? []).map((mv) => ({
          multivariate_feature_option: mv.id,
          percentage_allocation: mv.default_percentage_allocation,
        })),
    )
    setIsEditing(true)
  }, [rollout, experiment.feature.multivariate_options])

  const cancelEditing = () => setIsEditing(false)

  const handleSave = () => {
    if (isSaving) return
    openConfirm({
      body: (
        <>
          Changing the rollout configuration will immediately affect how traffic
          is distributed across experiment variations.
          <br />
          <br />
          This may impact the statistical validity of your results.
        </>
      ),
      noText: 'Cancel',
      onYes: async () => {
        try {
          await updateRollout({
            // No audience: it is frozen once running, and omitting the key
            // leaves the stored one untouched.
            body: buildRolloutBody({
              enabled: rollout?.enabled ?? true,
              featureStateValue: rollout?.feature_state_value ?? {
                type: 'string',
                value: experiment.feature.initial_value ?? '',
              },
              rolloutPercentage: draftRollout,
              variationSplit: draftSplit,
            }),
            environmentId,
            experimentId: experiment.id,
          }).unwrap()
          setIsEditing(false)
        } catch (error) {
          toast(
            experimentErrorMessage(error, 'Failed to update rollout'),
            'danger',
          )
        }
      },
      title: 'Update rollout configuration',
      yesText: 'Update',
    })
  }

  const draftControlPct = isEditing ? getControlPercentage(draftSplit) : 0

  const draftInvalid =
    isEditing &&
    (!isValidPercentage(draftControlPct) ||
      !isValidPercentage(draftRollout) ||
      draftSplit.some((s) => !isValidPercentage(s.percentage_allocation)))

  return (
    <ContentCard
      compact
      className='experiment-config-rollout'
      title='Rollout configuration'
      action={
        !isEditing ? (
          <Button
            theme='text'
            size='xSmall'
            onClick={startEditing}
            aria-label='Edit rollout configuration'
          >
            Edit <Icon name='edit' width={14} />
          </Button>
        ) : undefined
      }
    >
      <div className='d-flex flex-column gap-3 mx-0'>
        {!!audience && (
          <>
            <div className='d-flex flex-column gap-2'>
              <span>
                Audience
                {audience.segments.length > 1 && (
                  <span className='text-muted ml-1'>
                    (matches {audience.match === 'all' ? 'all' : 'any'})
                  </span>
                )}
              </span>
              {audience.segments.length ? (
                <AudienceSegmentList
                  segments={audience.segments.map((segment) => ({
                    cohortSourceType: segment.is_cohort
                      ? segment.cohort_source_type
                      : null,
                    deleted: segment.deleted,
                    id: segment.id,
                    name: segment.name,
                  }))}
                />
              ) : (
                <span className='text-muted'>
                  All identities in this environment
                </span>
              )}
            </div>

            <hr className='my-0 mx-0' />
          </>
        )}

        <div className='d-flex align-items-center justify-content-between'>
          <span>
            {audience?.segments.length
              ? joinSegmentNames(
                  audience.segments.map((segment) => segment.name),
                  audience.match === 'all' ? 'and' : 'or',
                )
              : 'Current rollout'}
          </span>
          {isEditing ? (
            <span className='d-flex align-items-center gap-1 justify-content-end'>
              <Input
                type='number'
                size='xSmall'
                underline
                centered
                className='w-25'
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
              {rollout?.rollout_percentage ?? 100}%
            </span>
          )}
        </div>

        <hr className='my-0 mx-0' />

        {identities.map((v, i) => {
          const isControl = i === 0
          const optionId = experiment.feature.multivariate_options?.[i - 1]?.id
          let currentPct: number
          if (!isEditing) {
            currentPct = Math.round(
              isControl
                ? 100 - treatmentTotal
                : getTreatmentAllocation(optionId!),
            )
          } else if (isControl) {
            currentPct = Math.max(0, draftControlPct)
          } else {
            currentPct =
              draftSplit.find((s) => s.multivariate_feature_option === optionId)
                ?.percentage_allocation ?? 0
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
                <span className='d-flex align-items-center gap-1 justify-content-end'>
                  <Input
                    type='number'
                    size='xSmall'
                    underline
                    centered
                    className='w-25'
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
                <span className='text-muted'>{Math.round(currentPct)}%</span>
              )}
            </div>
          )
        })}

        {isEditing && (
          <div className='d-flex justify-content-end gap-3 mt-2'>
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
  )
}

export default ExperimentRolloutCard
