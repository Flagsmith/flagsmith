import React, { FC } from 'react'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import { DiffValue } from 'common/types/responses'
import Utils from 'common/utils/utils'
import DiffRow from './DiffRow'

type DiffType = {
  oldValue: DiffValue
  newValue: DiffValue
  compareMethod?: DiffMethod
}

const renderDiff = (
  oldValue: DiffValue,
  newValue: DiffValue,
  compareMethod: DiffMethod,
) => {
  const oldText = Utils.sanitiseDiffString(oldValue)
  const newText = Utils.sanitiseDiffString(newValue)
  if (oldText === newText) {
    if (oldValue === null || oldValue === '') {
      return <div className='text-muted'>No Value.</div>
    }
    return (
      <DiffRow state='unchanged' scrollable>
        <pre
          className='d-inline mb-0'
          dangerouslySetInnerHTML={{
            __html: Prism.highlight(newText, Prism.languages.json, 'json'),
          }}
        />
      </DiffRow>
    )
  }
  return (
    <Diff
      oldValue={oldText}
      newValue={newText}
      compareMethod={compareMethod}
      hideLineNumbers={!(oldText.includes('\n') || newText.includes('\n'))}
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

const DiffString: FC<DiffType> = ({
  compareMethod = DiffMethod.WORDS_WITH_SPACE,
  newValue,
  oldValue,
}) => (
  <div role='group' aria-label='Value diff'>
    {renderDiff(oldValue, newValue, compareMethod)}
  </div>
)

export default DiffString
