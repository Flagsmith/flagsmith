import { TDiffVariation } from './diff-utils'
import React, { FC } from 'react'
import DiffString from './DiffString'
import { DiffMethod } from 'react-diff-viewer-continued'

const widths = [120]

type DiffVariationsType = {
  diffs: TDiffVariation[] | undefined
}
const DiffVariations: FC<DiffVariationsType> = ({ diffs }) => {
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
      {diffs?.map((diff, i) => (
        <Row key={i} className='list-item list-item-sm'>
          <div className='table-column flex-fill'>
            <DiffString
              data-test={`version-variation-${i}-value`}
              oldValue={diff.oldValue}
              newValue={diff.newValue}
            />
          </div>
          <div
            className='table-column text-center'
            style={{ width: widths[0] }}
          >
            <DiffString
              data-test={`version-variation-${i}-weight`}
              compareMethod={DiffMethod.WORDS}
              oldValue={`${diff.oldWeight || 0}%`}
              newValue={`${diff.newWeight || 0}%`}
            />
          </div>
        </Row>
      ))}
    </>
  )
}

export default DiffVariations
