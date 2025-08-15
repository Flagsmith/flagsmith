import React, { useState } from 'react'
import { CodeReference } from './FeatureCodeReferences'
import Icon from 'components/Icon'
import Highlight from 'components/Highlight'
import { GithubIcon } from 'components/base/icons/GithubIcon'
import GithubReferencesTag from 'components/tags/GithubReferencesTag'

interface CodeReferenceItemProps {
  codeReference: CodeReference
}

const CodeReferenceItem: React.FC<CodeReferenceItemProps> = ({
  codeReference,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  return (
    <>
      <div
        className='flex flex-col gap-2 bg-primary bg-opacity-10 border-radius-sm'
        style={{
          borderRadius: '6px',
          cursor: 'pointer',
          padding: '8px 6px',
          paddingRight: '12px',
        }}
      >
        <Row
          className='flex justify-content-between items-center'
          onClick={() => setIsOpen(!isOpen)}
        >
          <Row className='flex items-center gap-1'>
            <Icon
              name={isOpen ? 'chevron-up' : 'chevron-down'}
              className='w-4 h-4'
            />
            <p
              className='text-sm text-gray-500 mb-0 fw-bold'
              style={{ userSelect: 'none' }}
            >
              {codeReference.repository_url}
            </p>
          </Row>
          <GithubReferencesTag
            count={2}
            vcsProvider={codeReference.vcs_provider}
          />
        </Row>
        {isOpen && (
          <div className='flex flex-col gap-2 mt-2'>
            <Row className='flex items-center gap-1'>
              <Icon
                name={isOpen ? 'chevron-up' : 'chevron-down'}
                className='w-4 h-4 transparent'
                style={{ visibility: 'hidden' }}
              />
              <a
                className='text-sm text-gray-500 mb-0'
                style={{
                  fontStyle: 'italic',
                  fontWeight: 400,
                  textDecoration: 'underline',
                }}
                href={codeReference.permalink}
                target='_blank'
                rel='noreferrer'
              >
                {codeReference.file_path}:{codeReference.line_number}
              </a>
            </Row>
          </div>
        )}
      </div>
    </>
  )
}

export default CodeReferenceItem
