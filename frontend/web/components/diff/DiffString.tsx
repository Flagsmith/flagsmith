import React, { FC } from 'react'
import Diff, { DiffMethod } from 'react-diff-viewer-continued'
import Prism from 'prismjs'
import 'prismjs/components/prism-json'
import { FlagsmithValue } from 'common/types/responses'
import { stringifyDiffValue } from 'common/utils/diffValue'
import DiffRow from './DiffRow'

type DiffType = {
  oldValue: FlagsmithValue | object
  newValue: FlagsmithValue | object
  compareMethod?: DiffMethod
}

const DiffString: FC<DiffType> = ({
  compareMethod = DiffMethod.WORDS_WITH_SPACE,
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

  if (stringifyDiffValue(oldValue) === stringifyDiffValue(newValue)) {
    if (oldValue === null || oldValue === '') {
      return <div className='text-muted'>No Value.</div>
    }
    return (
      <DiffRow state='unchanged' scrollable>
        <pre
          className='d-inline mb-0'
          dangerouslySetInnerHTML={{
            __html: Prism.highlight(
              stringifyDiffValue(newValue),
              Prism.languages.json,
              'json',
            ),
          }}
        />
      </DiffRow>
    )
  }
  return (
    <Diff
      oldValue={stringifyDiffValue(oldValue)}
      newValue={stringifyDiffValue(newValue)}
      compareMethod={compareMethod}
      hideLineNumbers={
        !(
          stringifyDiffValue(oldValue).includes('\n') ||
          stringifyDiffValue(newValue).includes('\n')
        )
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
