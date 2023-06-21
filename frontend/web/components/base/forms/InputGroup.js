/**
 * Created by kylejohnson on 25/07/2016.
 */
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
    const { inputProps } = this.props
    return (
      <div
        className={`${this.props.className} form-group ${
          this.props.isInvalid ? 'invalid' : ''
        }`}
      >
        {this.props.tooltip ? (
          <Tooltip
            title={
              <label htmlFor={id} className='cols-sm-2 control-label'>
                <div>
                  {props.title}{' '}
                  <span className='icon ion-ios-information-circle' />{' '}
                  {props.unsaved && <div className='unread'>Unsaved</div>}
                </div>
              </label>
            }
            place={this.props.tooltipPlace || 'right'}
          >
            {this.props.tooltip}
          </Tooltip>
        ) : (
          <Row>
            {!!props.title && (
              <Flex className='mr-4'>
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

        {inputProps && inputProps.error && (
          <span>
            <span> - </span>
            <span
              id={props.inputProps.name ? `${props.inputProps.name}-error` : ''}
              className='text-danger'
            >
              {inputProps.error}
            </span>
          </span>
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
                />
              )}
            </div>
          )}
        </div>
      </div>
    )
  }
}

InputGroup.propTypes = {
  disabled: OptionalBool,
  inputProps: OptionalObject,
  isValid: propTypes.any,
  onChange: OptionalFunc,
  placeholder: OptionalString,
  title: propTypes.any,
  type: OptionalString,
  value: OptionalString,
}

export default InputGroup
