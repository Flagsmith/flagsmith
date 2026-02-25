import { TDiffVariation } from './diff-utils'
import React, { FC, useMemo } from 'react'
import DiffString from './DiffString'
import { DiffMethod } from 'react-diff-viewer-continued'
import { ProjectFlag } from 'common/types/responses'
import Utils from 'common/utils/utils'

const widths = [120]

type DiffVariationsType = {
  diffs: TDiffVariation[] | undefined
  projectFlag: ProjectFlag | undefined
}
const DiffVariations: FC<DiffVariationsType> = ({ diffs, projectFlag }) => {
  const sortedDiffs = useMemo(() => {
    if (!diffs || !projectFlag?.multivariate_options) return diffs
    return [...diffs].sort((a, b) => {
      const indexA = projectFlag.multivariate_options.findIndex(
        (mv) => mv.id === a.variationOption,
      )
      const indexB = projectFlag.multivariate_options.findIndex(
        (mv) => mv.id === b.variationOption,
      )
      return indexA - indexB
    })
  }, [diffs, projectFlag])
  const tableHeader = (
    <Row className='table-header mt-4'>
      <div className='table-column flex-fill'>Value</div>
      <div style={{ width: widths[0] }} className='table-column'>
        Weight
      </div>
    </Row>
  )

  return (
    <>
      {tableHeader}
      {sortedDiffs?.map((diff, i) => {
        const variation = projectFlag?.multivariate_options?.find(
          (v) => v.id === diff.variationOption,
        )
        const stringValue = variation
          ? Utils.featureStateToValue(variation)
          : ''
        return (
          <Row key={i} className='list-item list-item-sm'>
            <div className='table-column flex-fill'>
              <DiffString
                oldValue={stringValue}
                newValue={stringValue}
                data-test={`version-variation-${i}-value`}
              />
            </div>
            <div
              className='table-column text-center'
              style={{ width: widths[0] }}
            >
              <DiffString
                data-test={`version-variation-${i}-weight`}
                compareMethod={DiffMethod.WORDS_WITH_SPACE}
                oldValue={`${diff.oldWeight || 0}%`}
                newValue={`${diff.newWeight || 0}%`}
              />
            </div>
          </Row>
        )
      })}
    </>
  )
}

export default DiffVariations
