import React, { FC } from 'react'
// @ts-ignore
import { diffLines, formatLines } from 'unidiff'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import { FlagsmithValue } from 'common/types/responses'

type DiffType = {
  oldValue: FlagsmithValue
  newValue: FlagsmithValue
  compareMethod?: DiffMethod
}

const sanitiseDiffString = (value: FlagsmithValue) => {
  if (value === undefined || value == null) {
    return ''
  }
  return `${value}`
}
const DiffString: FC<DiffType> = ({
  compareMethod = DiffMethod.WORDS,
  newValue,
  oldValue,
}) => {
  if (E2E) {
    return (
      <>
        <div data-test={'old-value'}>{oldValue}</div>
        <div data-test={'new-value'}>{newValue}</div>
      </>
    )
  }

  if (oldValue === newValue) {
    if (oldValue === null || oldValue === '') {
      return null
    }
    return (
      <div className='react-diff react-diff-line d-flex align-items-center'>
        <pre
          className='d-inline'
          dangerouslySetInnerHTML={{
            __html: Prism.highlight(
              sanitiseDiffString(newValue),
              Prism.languages.json,
              'json',
            ),
          }}
        />
      </div>
    )
  }
  return (
    <Diff
      oldValue={sanitiseDiffString(oldValue)}
      newValue={sanitiseDiffString(newValue)}
      compareMethod={compareMethod}
      hideLineNumbers={
        !(`${oldValue}`.includes?.('\n') || `${newValue}`.includes?.('\n'))
      }
      renderContent={(str) => (
        <pre
          className='d-inline'
          dangerouslySetInnerHTML={{
            __html: Prism.highlight(str, Prism.languages.json, 'json'),
          }}
        />
      )}
      splitView={false}
    />
  )
}

export default DiffString
