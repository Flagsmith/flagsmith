import React, { FC } from 'react'
// @ts-ignore
import { diffLines, formatLines } from 'unidiff'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'

type DiffType = {
  oldValue: string
  newValue: string
}

const DiffString: FC<DiffType> = ({ newValue, oldValue }) => {
  if (oldValue === newValue) {
    if (oldValue === null || oldValue === '') {
      return null
    }
    return (
      <div className='react-diff react-diff-line d-flex align-items-center'>
        <div className='react-diff-marker' />
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
      compareMethod={DiffMethod.CHARS}
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
