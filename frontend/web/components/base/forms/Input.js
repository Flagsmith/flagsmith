/**
 * Created by kylejohnson on 30/07/2016.
 */
import MaskedInput from 'react-maskedinput'
import cn from 'classnames'

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
      inputClassName,
      isValid,
      mask,
      onSearchChange,
      placeholderChar,
      showSuccess,
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
        success,
      },
      this.props.className,
    )

    const innerClassName = cn(
      {
        input: true,
      },
      inputClassName,
    )

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
          />
        )}
        {invalid && (
          <span
            className={`input-icon-right text-danger icon ion ion-ios-close-circle-outline`}
          />
        )}
        {success && (
          <span
            className={`input-icon-right text-success icon ion ion-ios-checkmark-circle-outline`}
          />
        )}
        {this.props.type === 'password' && (
          <span
            onClick={() =>
              this.setState({
                type: this.state.type === 'password' ? 'text' : 'password',
              })
            }
            className={`input-icon-right icon ion ${
              this.state.type === 'text' ? 'ion-ios-eye-off' : 'ion-ios-eye'
            }`}
          />
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
}

export default Input
