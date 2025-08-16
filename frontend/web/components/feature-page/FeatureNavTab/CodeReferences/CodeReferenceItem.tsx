import Icon from 'components/Icon'
import { CodeReference } from 'common/types/responses'

interface CodeReferenceItemProps {
  codeReference: CodeReference
}

const CodeReferenceItem: React.FC<CodeReferenceItemProps> = ({
  codeReference,
}) => {
  return (
    <Row className='flex items-center gap-1'>
      <Icon
        name={'chevron-down'}
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
  )
}

export default CodeReferenceItem
