import React, { FC } from 'react'
// @ts-ignore
import { diffLines, formatLines } from 'unidiff'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import 'prismjs/components/prism-ini'
import 'prismjs/components/prism-yaml'
import 'prismjs/components/prism-xml-doc'
import ValueEditor from 'components/ValueEditor'

type DiffType = {
  oldValue: string
  newValue: string
}

const DiffString: FC<DiffType> = ({ newValue, oldValue }) => {
  if (oldValue === newValue) {
    return (
      <div>
        <ValueEditor value={oldValue} />
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
