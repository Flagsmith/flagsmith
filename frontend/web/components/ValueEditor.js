import React, { Component } from 'react'
import cx from 'classnames'
import Highlight from './Highlight'
import ConfigProvider from 'common/providers/ConfigProvider'
import { Clipboard } from 'polyfill-react-native'
import Icon from './Icon'

const toml = require('toml')
const yaml = require('yaml')

function xmlIsInvalid(xmlStr) {
  const parser = new DOMParser()
  const dom = parser.parseFromString(xmlStr, 'application/xml')
  for (const element of Array.from(dom.querySelectorAll('parsererror'))) {
    if (element instanceof HTMLElement) {
      // Found the error.
      return element.innerText
    }
  }
  // No errors found.
  return false
}

class Validation extends Component {
  constructor(props) {
    super(props)
    this.state = {}
    this.validateLanguage(this.props.language, this.props.value)
  }

  componentDidUpdate(prevProps) {
    if (
      prevProps.value !== this.props.value ||
      prevProps.language !== this.props.language
    ) {
      this.validateLanguage(this.props.language, this.props.value)
    }
  }

  validateLanguage = (language, value) => {
    const validate = new Promise((resolve) => {
      switch (language) {
        case 'json': {
          try {
            JSON.parse(value)
            resolve(false)
          } catch (e) {
            resolve(e.message)
          }
          break
        }
        case 'ini': {
          try {
            toml.parse(value)
            resolve(false)
          } catch (e) {
            resolve(e.message)
          }
          break
        }
        case 'yaml': {
          try {
            yaml.parse(value)
            resolve(false)
          } catch (e) {
            resolve(e.message)
          }
          break
        }
        case 'xml': {
          try {
            const error = xmlIsInvalid(value)
            resolve(error)
          } catch (e) {
            resolve('Failed to parse XML')
          }
          break
        }
        default: {
          resolve(false)
          break
        }
      }
    })

    validate.then((error) => {
      this.setState({ error })
    })
  }

  render() {
    const displayLanguage =
      this.props.language === 'ini' ? 'toml' : this.props.language
    return (
      <Tooltip
        position='top'
        title={
          !this.state.error ? (
            <span className='language-icon ion-ios-checkmark-circle' />
          ) : (
            <span
              id='language-validation-error'
              className='language-icon ion-ios-warning'
            />
          )
        }
      >
        {!this.state.error
          ? `${displayLanguage} validation passed`
          : `${displayLanguage} validation error, please check your value.<br/>Error: ${this.state.error}`}
      </Tooltip>
    )
  }
}
class ValueEditor extends Component {
  state = {
    language: 'txt',
  }

  componentDidMount() {
    if (!this.props.value) return
    try {
      const v = JSON.parse(this.props.value)
      if (typeof v !== 'object') return
      this.setState({ language: 'json' })
    } catch (e) {}
  }

  renderValidation = () => (
    <Validation language={this.state.language} value={this.props.value} />
  )

  render() {
    const { ...rest } = this.props
    return (
      <div
        className={cx(
          'value-editor',
          {
            disabled: this.props.disabled,
            light: this.state.language === 'txt',
          },
          this.props.className,
        )}
      >
        <Row className='select-language gap-1'>
          <span
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              this.setState({ language: 'txt' })
            }}
            className={cx('txt', { active: this.state.language === 'txt' })}
          >
            .txt
          </span>
          <span
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              this.setState({ language: 'json' })
            }}
            className={cx('json', { active: this.state.language === 'json' })}
          >
            .json {this.state.language === 'json' && this.renderValidation()}
          </span>
          <span
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              this.setState({ language: 'xml' })
            }}
            className={cx('xml', { active: this.state.language === 'xml' })}
          >
            .xml {this.state.language === 'xml' && this.renderValidation()}
          </span>
          <span
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()

              this.setState({ language: 'ini' })
            }}
            className={cx('ini', { active: this.state.language === 'ini' })}
          >
            .toml {this.state.language === 'ini' && this.renderValidation()}
          </span>
          <span
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
              this.setState({ language: 'yaml' })
            }}
            className={cx('yaml', { active: this.state.language === 'yaml' })}
          >
            .yaml {this.state.language === 'yaml' && this.renderValidation()}
          </span>
          <span
            onMouseDown={() => {
              const res = Clipboard.setString(this.props.value)
              toast(
                res ? 'Clipboard set' : 'Could not set clipboard :(',
                res ? '' : 'danger',
              )
            }}
            className={cx('txt primary')}
          >
            <Icon name='copy-outlined' fill={'#6837fc'} />
            copy
          </span>
        </Row>

        {E2E ? (
          <textarea {...rest} />
        ) : (
          <Highlight
            data-test={rest['data-test']}
            disabled={rest.disabled}
            onChange={rest.disabled ? null : rest.onChange}
            className={this.state.language}
          >
            {typeof rest.value !== 'undefined' && rest.value != null
              ? `${rest.value}`
              : ''}
          </Highlight>
        )}
      </div>
    )
  }
}

export default ConfigProvider(ValueEditor)
