import React, { Component } from 'react'
import Highlight from './Highlight'
import ConfigProvider from 'common/providers/ConfigProvider'
import Constants from 'common/constants'
import { Clipboard } from 'polyfill-react-native'
import Icon from './Icon'
import { logoGithub, document } from 'ionicons/icons'
import { IonIcon } from '@ionic/react'

const getGithubLink = (key) => {
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
const getDocsLink = (key) => {
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

const CodeHelp = class extends Component {
  static displayName = 'CodeHelp'

  constructor(props, context) {
    super(props, context)
    this.state = {
      visible: this.props.showInitially || this.props.hideHeader,
    }
  }

  copy = (s) => {
    const res = Clipboard.setString(s)
    toast(
      res ? 'Clipboard set' : 'Could not set clipboard :(',
      res ? '' : 'danger',
    )
  }

  render() {
    const { hideHeader } = this.props
    let language =
      this.state.language ||
      flagsmith.getTrait('preferred_language') ||
      Object.keys(this.props.snippets)[0]
    // A snippet might not be available for the code help, in which case match the index or set to the first one
    const tab = language
      ? Math.max(Object.keys(this.props.snippets).indexOf(language), 0)
      : 0
    language = Object.keys(this.props.snippets)[tab]
    return (
      <div>
        {!hideHeader && (
          <div
            style={{ cursor: 'pointer' }}
            onClick={() => {
              this.setState({ visible: !this.state.visible })
            }}
          >
            <Row>
              <Flex style={isMobile ? { overflowX: 'scroll' } : {}}>
                <div>
                  <pre className='hljs-header'>
                    <span />
                    {'<>'} Code example:{' '}
                    <span className='hljs-description'>{this.props.title}</span>
                    <span className='hljs-icon'>
                      <Icon
                        name={
                          this.state.visible ? 'chevron-down' : 'chevron-right'
                        }
                        width={16}
                      />
                    </span>
                  </pre>
                </div>
              </Flex>
            </Row>
          </div>
        )}

        {this.state.visible && (
          <>
            {this.props.subtitle && (
              <div className='mb-2'>{this.props.subtitle}</div>
            )}

            <div className='code-help'>
              {_.map(this.props.snippets, (s, key) => {
                const docs = getDocsLink(key)
                const github = getGithubLink(key)
                return (
                  <div
                    className={
                      key !== language ? 'd-none' : 'hljs-container mt-2 mb-2'
                    }
                  >
                    <Select
                      data-test='select-segment'
                      placeholder='Select a language'
                      value={{
                        label: language,
                      }}
                      onChange={(v) => {
                        const lang = v.label
                        this.setState({ language: lang })
                        flagsmith.setTrait('preferred_language', lang)
                        this.setState({ tab })
                      }}
                      options={_.sortBy(
                        Object.keys(this.props.snippets),
                        (key) => key[0].toLowerCase(),
                      ).map((v, i) => ({
                        label: v,
                        value: i,
                      }))}
                      styles={{
                        control: (base) => ({
                          ...base,
                          alignSelf: 'flex-end',
                          width: 200,
                        }),
                      }}
                    />
                    <Highlight
                      forceExpanded
                      preventEscape
                      className={Constants.codeHelp.keys[key]}
                    >
                      {s}
                    </Highlight>

                    <Column className='hljs-docs'>
                      <Button
                        onClick={() => this.copy(s)}
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
                          <span
                            className='icon ion'
                            style={{ marginRight: '2px' }}
                          >
                            <IonIcon icon={document} />
                          </span>
                          {key}
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
                          <span
                            className='icon ion'
                            style={{ marginRight: '2px' }}
                          >
                            <IonIcon icon={logoGithub} />
                          </span>
                          {key} GitHub
                        </Button>
                      )}
                    </Column>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>
    )
  }
}

CodeHelp.propTypes = {}

module.exports = ConfigProvider(CodeHelp)
