/**
 * Created by kylejohnson on 30/07/2016.
 */
import MaskedInput from 'react-maskedinput'
import cn from 'classnames'
import Icon from 'components/Icon'
import Radio from './Radio'
import Checkbox from './Checkbox'

const maskedCharacters = {
  'a': {
    validate(char) {
      return /[ap]/.test(char)
    },
  },
  'm': {
    transform() {
      return 'm'
    },
    validate(char) {
      return /\w/.test(char)
    },
  },
}

const sizeClassNames = {
  default: '',
  large: 'input-lg',
  small: 'input-sm',
  xSmall: 'input-xsm',
}

const Input = class extends React.Component {
  static displayName = 'Input'

  constructor(props, context) {
    super(props, context)
    this.state = {
      shouldValidate: !!this.props.value || this.props.autoValidate,
      type: this.props.type,
    }
  }
  onFocus = (e) => {
    this.setState({
      isFocused: true,
    })
    this.props.onFocus && this.props.onFocus(e)
  }

  focus = () => {
    if (E2E) return
    this.input.focus()
  }

  onKeyDown = (e) => {
    if (Utils.keys.isEscape(e)) {
      this.input.blur()
    }
    this.props.onKeyDown && this.props.onKeyDown(e)
  }

  validate = () => {
    this.setState({
      shouldValidate: true,
    })
  }

  onBlur = (e) => {
    this.setState({
      isFocused: false,
      shouldValidate: true,
    })
    this.props.onBlur && this.props.onBlur(e)
  }

  render() {
    const {
      disabled,
      inputClassName,
      isValid,
      mask,
      placeholderChar,
      showSuccess,
      size,
      ...rest
    } = this.props

    const invalid = this.state.shouldValidate && !isValid
    const success = isValid && showSuccess
    const className = cn(
      {
        'focused': this.state.isFocused,
        'input-container': true,
        invalid,
        'password': this.props.type === 'password',
        'search': this.props.search,
        success,
      },
      this.props.className,
    )

    const innerClassName = cn(
      {
        input: true,
      },
      inputClassName,
      sizeClassNames[size],
    )

    if (this.props.type === 'checkbox') {
      return (
        <Checkbox
          label={this.props.label}
          value={this.props.value}
          onChange={this.props.onChange}
          checked={!!this.props.value}
        />
      )
    } else if (this.props.type === 'radio') {
      return (
        <Radio
          label={this.props.label}
          value={this.props.value}
          onChange={this.props.onChange}
          checked={!!this.props.value}
        />
      )
    }

    return (
      <div className={className}>
        {mask ? (
          <MaskedInput
            ref={(c) => (this.input = c)}
            {...rest}
            mask={this.props.mask}
            type={this.state.type}
            formatCharacters={maskedCharacters}
            onKeyDown={this.onKeyDown}
            onFocus={this.onFocus}
            onBlur={this.onBlur}
            className={innerClassName}
            placeholderChar={placeholderChar}
          />
        ) : (
          <input
            ref={(c) => (this.input = c)}
            {...rest}
            onFocus={this.onFocus}
            onKeyDown={this.onKeyDown}
            type={this.state.type}
            onBlur={this.onBlur}
            value={this.props.value}
            className={innerClassName}
            disabled={disabled}
          />
        )}
        {this.props.type === 'password' && (
          <span
            className={cn(
              {
                'clickable': true,
                'input-icon-right': true,
              },
              sizeClassNames[size],
            )}
            onClick={() => {
              if (!disabled) {
                this.setState({
                  type: this.state.type === 'password' ? 'text' : 'password',
                })
              }
            }}
          >
            <Icon
              name={this.state.type === 'text' ? 'eye' : 'eye-off'}
              fill={invalid && '#ef4d56'}
              width={
                size &&
                ((size === 'small' && 20) ||
                  (size === 'xSmall' && 18) ||
                  (size === 'large' && 24))
              }
            />
          </span>
        )}
        {this.props.search && (
          <span
            className={cn(
              {
                'input-icon-right': true,
              },
              sizeClassNames[size],
            )}
          >
            <Icon
              name='search'
              width={this.props.size === 'xSmall' ? 16 : 20}
            />
          </span>
        )}
      </div>
    )
  }
}

Input.defaultProps = {
  className: '',
  isValid: true,
  placeholderChar: ' ',
}

Input.propTypes = {
  className: propTypes.any,
  inputClassName: OptionalString,
  isValid: propTypes.any,
  mask: OptionalString,
  onBlur: OptionalFunc,
  onFocus: OptionalFunc,
  onKeyDown: OptionalFunc,
  onSearchChange: OptionalFunc,
  placeholderChar: OptionalString,
  search: propTypes.Boolean,
  size: OptionalString,
}

export default Input
