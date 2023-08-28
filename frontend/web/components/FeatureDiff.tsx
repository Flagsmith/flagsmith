import React, { FC, useState } from 'react'
import { FeatureState, ProjectFlag } from 'common/types/responses'
import Utils from 'common/utils/utils'
import { Change } from 'diff'
import classNames from 'classnames'
import Format from 'common/utils/format'
import Switch from './Switch'
import Tabs from './base/forms/Tabs'
import TabItem from './base/forms/TabItem'

const Diff = require('diff')

type FeatureDiffType = {
  oldState: FeatureState[]
  newState: FeatureState[]
  projectflag: ProjectFlag
  oldTitle?: string
  newTitle?: string
}

type DiffType = {
  changes: Change[]
  isEnabledState?: boolean
}

const getChangedChanges = (changes: Change[]) =>
  changes.filter((v) => !!v.added || !!v.removed)
const DiffEl: FC<DiffType> = ({ changes, isEnabledState }) => {
  return (
    <>
      {changes.map((v, i) => (
        <div
          key={i}
          className={classNames('git-diff', {
            'git-diff--added': v.added,
            'git-diff--removed': v.removed,
          })}
        >
          {(!!v.added || !!v.removed) && (
            <span style={{ width: 30 }} className='text-center d-inline-block'>
              {v.added ? '+' : '-'}
            </span>
          )}
          {isEnabledState ? (
            <Switch checked={v.value === 'true'} />
          ) : (
            <span
              dangerouslySetInnerHTML={{
                __html: v.value
                  .replace(/ /g, '&nbsp;')
                  .replace(
                    /\n/g,
                    '<br/><span class="d-inline-block" style="width: 30px;"></span>',
                  ),
              }}
            />
          )}
        </div>
      ))}
    </>
  )
}

const getDiff = (
  oldFeatureState: FeatureState | undefined,
  newFeatureState: FeatureState | undefined,
) => {
  const oldEnabled = `${!!oldFeatureState?.enabled}`
  const newEnabled = `${!!newFeatureState?.enabled}`
  return {
    enabled: Diff.diffLines(oldEnabled, newEnabled),
    value: Diff.diffLines(
      `${Utils.getTypedValue(
        Utils.featureStateToValue(oldFeatureState?.feature_state_value),
      )}`,
      `${Utils.getTypedValue(
        Utils.featureStateToValue(newFeatureState?.feature_state_value),
      )}`,
    ),
  }
}
const FeatureDiff: FC<FeatureDiffType> = ({
  newState,
  newTitle,
  oldState,
  oldTitle,
}) => {
  const oldEnv = oldState?.find((v) => !v.feature_segment)
  const newEnv = newState?.find((v) => !v.feature_segment)
  const diff = getDiff(oldEnv, newEnv)
  const valueChanges = getChangedChanges(diff.value).length ? 1 : 0
  const enabledChanges = getChangedChanges(diff.enabled).length ? 1 : 0
  const environmentChanges = valueChanges + enabledChanges
  const [value, setValue] = useState(environmentChanges?.length ? 0 : 1)

  return (
    <div className='p-2'>
      <Tabs onChange={setValue} value={value}>
        <TabItem
          tabLabel={
            <div>
              Value
              {!!environmentChanges && (
                <span className='unread'>{environmentChanges}</span>
              )}
            </div>
          }
        >
          <div>
            {environmentChanges === 0 && (
              <div className='p-4 text-center text-muted'>No Changes</div>
            )}
            <div className='flex-row table-header'>
              <div className='table-column text-center' style={{ width: 100 }}>
                Enabled
              </div>
              <div className='table-column flex flex-1'>Value</div>
            </div>
            <div className='flex-row list-item'>
              <div className='table-column text-center' style={{ width: 100 }}>
                <DiffEl isEnabledState changes={diff.enabled} />
              </div>
              <div className='table-column flex flex-1'>
                <div>
                  <DiffEl changes={diff?.value} />
                </div>
              </div>
            </div>
          </div>
        </TabItem>
        <TabItem tabLabel={'Variations'}></TabItem>
        <TabItem tabLabel={'Segment Overrides'}></TabItem>
      </Tabs>
    </div>
  )
}

export default FeatureDiff
