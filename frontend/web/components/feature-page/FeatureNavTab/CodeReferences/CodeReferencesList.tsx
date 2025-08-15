import React from 'react'
import { CodeReference } from './FeatureCodeReferences'
import CodeReferenceItem from './CodeReferenceItem'

interface CodeReferencesListProps {
  codeReferences: CodeReference[]
}

const CodeReferencesList: React.FC<CodeReferencesListProps> = ({
  codeReferences,
}) => {
  return (
    <div className='flex flex-col gap-2'>
      {codeReferences.map((codeReference) => (
        <CodeReferenceItem
          codeReference={codeReference}
          key={codeReference.permalink}
        />
      ))}
    </div>
  )
}

export default CodeReferencesList
