import React, { FC } from 'react'
// @ts-ignore
import { diffLines, formatLines } from 'unidiff'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'

type DiffType = {
  oldValue: string
  newValue: string
  compareMethod?: DiffMethod
}

const DiffString: FC<DiffType> = ({
  compareMethod = DiffMethod.CHARS,
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
            __html: Prism.highlight(newValue, Prism.languages.json, 'json'),
          }}
        />
      </div>
    )
  }
  return (
    <Diff
      oldValue={oldValue}
      newValue={newValue}
      compareMethod={compareMethod}
      hideLineNumbers={!(oldValue?.includes('\n') || newValue?.includes('\n'))}
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
