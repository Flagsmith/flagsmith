import React, { FC, useState } from 'react'
import flagsmith from '@flagsmith/flagsmith'
import Highlight from './Highlight'
import Constants from 'common/constants'
import Utils from 'common/utils/utils'
import Icon from './Icon'
import { logoGithub, document } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

type Snippets = Record<string, string>

type CodeHelpProps = {
  hideHeader?: boolean
  showInitially?: boolean
  snippets: Snippets
  subtitle?: React.ReactNode
  title?: string
}

type SnippetItemProps = {
  code: string
  isVisible: boolean
  keys: string[]
  language: string
  languageKey: string
  onCopy: (s: string) => void
  onLanguageChange: (lang: string) => void
}

const getGithubLink = (key: string): string => {
  switch (key) {
    case '.NET':
      return 'https://github.com/flagsmith/flagsmith-dotnet-client/'
    case 'Flutter':
      return 'https://github.com/flagsmith/flagsmith-flutter-client/'
    case 'Go':
      return 'https://github.com/flagsmith/flagsmith-go-client/'
    case 'Java':
      return 'https://github.com/flagsmith/flagsmith-java-client/'
    case 'JavaScript':
      return 'https://github.com/flagsmith/flagsmith-js-client/'
    case 'Node JS':
      return 'https://github.com/flagsmith/flagsmith-nodejs-client/'
    case 'PHP':
      return 'https://github.com/flagsmith/flagsmith-php-client/'
    case 'Python':
      return 'https://github.com/flagsmith/flagsmith-python-client/'
    case 'REST':
      return 'https://docs.flagsmith.com/clients/rest/'
    case 'React Native':
      return 'https://github.com/flagsmith/flagsmith-js-client/'
    case 'React':
      return 'https://github.com/flagsmith/flagsmith-js-client/'
    case 'Next.js':
      return 'https://github.com/flagsmith/flagsmith-js-client/'
    case 'Ruby':
      return 'https://github.com/flagsmith/flagsmith-ruby-client/'
    case 'Rust':
      return 'https://github.com/flagsmith/flagsmith-rust-client/'
    case 'iOS':
      return 'https://github.com/flagsmith/flagsmith-ios-client/'
    default:
      return 'https://docs.flagsmith.com'
  }
}

const getDocsLink = (key: string): string | null => {
  switch (key) {
    case '.NET':
      return 'https://docs.flagsmith.com/clients/server-side?language=dotnet'
    case 'curl':
      return 'https://docs.flagsmith.com/clients/rest'
    case 'Flutter':
      return 'https://docs.flagsmith.com/clients/flutter/'
    case 'Go':
      return 'https://docs.flagsmith.com/clients/server-side?language=go'
    case 'Java':
      return 'https://docs.flagsmith.com/clients/server-side?language=java'
    case 'JavaScript':
      return 'https://docs.flagsmith.com/clients/javascript/'
    case 'Node JS':
      return 'https://docs.flagsmith.com/clients/server-side?language=nodejs'
    case 'PHP':
      return 'https://docs.flagsmith.com/clients/server-side?language=php'
    case 'Python':
      return 'https://docs.flagsmith.com/clients/server-side?language=python'
    case 'REST':
      return null
    case 'React':
      return 'https://docs.flagsmith.com/clients/react'
    case 'React Native':
      return 'https://docs.flagsmith.com/clients/react'
    case 'Ruby':
      return 'https://docs.flagsmith.com/clients/server-side?language=ruby'
    case 'Rust':
      return 'https://docs.flagsmith.com/clients/server-side?language=rust'
    case 'iOS':
      return 'https://docs.flagsmith.com/clients/ios/'
    case 'Next.js':
      return 'https://docs.flagsmith.com/clients/next-ssr'
    default:
      return 'https://docs.flagsmith.com'
  }
}

const SnippetItem: FC<SnippetItemProps> = ({
  code,
  isVisible,
  keys,
  language,
  languageKey,
  onCopy,
  onLanguageChange,
}) => {
  const docs = getDocsLink(languageKey)
  const github = getGithubLink(languageKey)

  return (
    <div className={!isVisible ? 'd-none' : 'hljs-container mt-2 mb-2'}>
      <Select
        data-test='select-segment'
        placeholder='Select a language'
        value={{
          label: language,
        }}
        onChange={(v: { label: string }) => {
          onLanguageChange(v.label)
        }}
        options={[...keys]
          .sort((a, b) => a[0].toLowerCase().localeCompare(b[0].toLowerCase()))
          .map((v: string, i: number) => ({
            label: v,
            value: i,
          }))}
        styles={{
          control: (base: Record<string, unknown>) => ({
            ...base,
            alignSelf: 'flex-end',
            width: 200,
          }),
        }}
      />
      <Highlight
        forceExpanded
        preventEscape
        className={
          Constants.codeHelp.keys[
            languageKey as keyof typeof Constants.codeHelp.keys
          ]
        }
      >
        {code}
      </Highlight>

      <div className='flex-column hljs-docs'>
        <Button
          onClick={() => onCopy(code)}
          size='xSmall'
          iconLeft='copy'
          iconLeftColour='white'
        >
          Copy Code
        </Button>
        {docs && (
          <Button
            target='_blank'
            href={docs}
            className='btn btn-primary'
            size='xSmall'
          >
            <span className='icon ion' style={{ marginRight: '2px' }}>
              <IonIcon icon={document} />
            </span>
            {languageKey}
            Docs
          </Button>
        )}
        {github && (
          <Button
            target='_blank'
            href={github}
            className='btn btn-primary'
            size='xSmall'
          >
            <span className='icon ion' style={{ marginRight: '2px' }}>
              <IonIcon icon={logoGithub} />
            </span>
            {languageKey} GitHub
          </Button>
        )}
      </div>
    </div>
  )
}

const CodeHelp: FC<CodeHelpProps> = ({
  hideHeader,
  showInitially,
  snippets,
  subtitle,
  title,
}) => {
  const [visible, setVisible] = useState(!!showInitially || !!hideHeader)
  const [selectedLanguage, setSelectedLanguage] = useState<string | null>(null)

  const keys = Object.keys(snippets)
  let language =
    selectedLanguage ||
    (flagsmith.getTrait('preferred_language') as string) ||
    keys[0]
  const tab = language ? Math.max(keys.indexOf(language), 0) : 0
  language = keys[tab]

  const copy = (s: string) => {
    Utils.copyToClipboard(s)
  }

  const handleLanguageChange = (lang: string) => {
    setSelectedLanguage(lang)
    flagsmith.setTrait('preferred_language', lang)
  }

  return (
    <div>
      {!hideHeader && (
        <div style={{ cursor: 'pointer' }} onClick={() => setVisible(!visible)}>
          <div className='flex-row'>
            <div
              className='flex flex-1'
              style={isMobile ? { overflowX: 'scroll' } : {}}
            >
              <div>
                <pre className='hljs-header'>
                  <span />
                  {'<>'} Code example:{' '}
                  <span className='hljs-description'>{title}</span>
                  <span className='hljs-icon'>
                    <Icon
                      name={visible ? 'chevron-down' : 'chevron-right'}
                      width={16}
                    />
                  </span>
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}

      {visible && (
        <>
          {subtitle && <div className='mb-2'>{subtitle}</div>}

          <div className='code-help'>
            {Object.entries(snippets).map(([key, code]) => (
              <SnippetItem
                key={key}
                code={code}
                isVisible={key === language}
                keys={keys}
                language={language}
                languageKey={key}
                onCopy={copy}
                onLanguageChange={handleLanguageChange}
              />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default CodeHelp
