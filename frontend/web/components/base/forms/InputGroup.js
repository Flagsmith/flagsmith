/**
 * Created by kylejohnson on 25/07/2016.
 */
import Icon from 'components/Icon'
import React, { Component } from 'react'

const InputGroup = class extends Component {
  static displayName = 'InputGroup'

  constructor(props, context) {
    super(props, context)
    this.state = {}
  }

  focus = () => {
    this.input.focus()
  }

  render() {
    const { props } = this
    const id = this.props.id || Utils.GUID()
    const { inputProps, size } = this.props
    return (
      <div
        className={`${
          this.props.className ? this.props.className : ''
        } form-group ${this.props.isInvalid ? 'invalid' : ''}`}
      >
        {this.props.tooltip ? (
          <Tooltip
            title={
              <label htmlFor={id} className='cols-sm-2 control-label'>
                <div>
                  {props.title}{' '}
                  {!props.hideTooltipIcon && <Icon name='info-outlined' />}{' '}
                  {props.unsaved && <div className='unread'>Unsaved</div>}
                </div>
              </label>
            }
            place={this.props.tooltipPlace || 'top'}
          >
            {this.props.tooltip}
          </Tooltip>
        ) : (
          <Row>
            {!!props.title && (
              <Flex>
                <label htmlFor={id} className='cols-sm-2 control-label'>
                  <div>
                    {props.title}{' '}
                    {props.unsaved && <div className='unread'>Unsaved</div>}
                  </div>
                </label>
              </Flex>
            )}
            {!!this.props.rightComponent && (
              <div
                style={{
                  marginBottom: '0.5rem',
                }}
              >
                {this.props.rightComponent}
              </div>
            )}
          </Row>
        )}

        <div>
          {this.props.component ? (
            this.props.component
          ) : (
            <div>
              {this.props.textarea ? (
                <textarea
                  ref={(c) => (this.input = c)}
                  {...props.inputProps}
                  isValid={props.isValid}
                  disabled={props.disabled}
                  value={props.value}
                  defaultValue={props.defaultValue}
                  data-test={props['data-test']}
                  onChange={props.onChange}
                  type={props.type || 'text'}
                  id={id}
                  placeholder={props.placeholder}
                />
              ) : (
                <Input
                  ref={(c) => (this.input = c)}
                  {...props.inputProps}
                  isValid={props.isValid}
                  disabled={props.disabled}
                  defaultValue={props.defaultValue}
                  value={props.value}
                  data-test={props['data-test']}
                  onChange={props.onChange}
                  type={props.type || 'text'}
                  id={id}
                  placeholder={props.placeholder}
                  size={size}
                />
              )}
            </div>
          )}
        </div>
        {inputProps && inputProps.error && (
          <span>
            <span
              id={props.inputProps.name ? `${props.inputProps.name}-error` : ''}
              className='text-danger'
            >
              {typeof inputProps.error === 'string'
                ? inputProps.error
                : !!inputProps.error?.length &&
                  inputProps.error.map((err, i) => <div key={i}>{err}</div>)}
            </span>
          </span>
        )}
      </div>
    )
  }
}

InputGroup.propTypes = {
  disabled: OptionalBool,
  hideTooltipIcon: OptionalBool,
  inputProps: OptionalObject,
  isValid: propTypes.any,
  onChange: OptionalFunc,
  placeholder: OptionalString,
  size: OptionalString,
  title: propTypes.any,
  type: OptionalString,
  value: OptionalString,
}

export default InputGroup
