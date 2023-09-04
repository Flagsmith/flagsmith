import React from 'react'

if (typeof hljs !== 'undefined') {
  hljs.initHighlightingOnLoad()
}
function escapeHtml(unsafe) {
  if (!unsafe || !unsafe.__html) return unsafe
  return {
    __html: `${unsafe.__html}`
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;'),
  }
}
const defaultValue = { __html: 'Enter a value...' }
const defaultDisabledValue = { __html: ' ' }
const collapsedHeight = 110
class Highlight extends React.Component {
  state = {
    value: { __html: this.props.children },
  }

  constructor(props) {
    super(props)
    this.setEl = this.setEl.bind(this)
  }

  componentDidMount() {
    this.highlightCode()
  }

  componentDidUpdate(prevProps) {
    this.highlightCode()
    if (this.props.className !== prevProps.className) {
      setTimeout(() => {
        this.highlightCode()
      }, 100)
    }
    if (this.state.prevValue !== this.props.children) {
      this.setState({
        key: Date.now(),
        value: {
          ...this.state.value,
          __html: this.props.children,
        },
      })
    }
  }

  highlightCode = () => {
    const nodes = this.el.querySelectorAll('pre code')
    if (typeof hljs !== 'undefined') {
      for (let i = 0; i < nodes.length; i++) {
        hljs.highlightBlock(nodes[i])
      }
    }
  }

  setEl(el) {
    this.el = el
    this.measure = (force) => {
      if (this.props.forceExpanded) return
      if (!this.el) return
      const height = this.el.clientHeight
      if (!this.state.expandable && height > collapsedHeight) {
        this.setState({ expandable: true, expanded: false })
      }
      if (typeof this.state.expandable !== 'boolean' || force) {
        if (height > collapsedHeight) {
          this.setState({ expandable: true, expanded: false })
        } else if (!height) {
          setTimeout(() => {
            this.measure()
          }, 50)
        } else {
          this.setState({ expandable: false })
        }
      }
    }
    this.measure()
  }
  shouldComponentUpdate(nextProps, nextState) {
    if (nextState.focus !== this.state.focus) return true
    if (nextProps.className !== this.props.className) return true
    if (nextState.expandable !== this.state.expandable) return true
    if (nextState.expanded !== this.state.expanded) return true
    if (nextProps['data-test'] !== this.props['data-test']) return true
    return this.state.value.__html !== `${nextProps.children}`
  }

  _handleInput = (event) => {
    const value = event.target.innerText
    this.state.value.__html = value
    this.props.onChange(value)
  }

  onFocus = () => {
    this.setState({ focus: true })
  }

  onBlur = () => {
    this.setState({ focus: false })
  }

  render() {
    const {
      children,
      className,
      disabled,
      element: Element,
      innerHTML,
    } = this.props
    const props = { className, ref: this.setEl }

    if (innerHTML) {
      props.dangerouslySetInnerHTML = { __html: children }
      if (Element) {
        return <Element {...props} />
      }
      return <div {...props} />
    }

    if (Element) {
      return <Element {...props}>{children}</Element>
    }

    const html = this.props.preventEscape
      ? this.state.focus
        ? this.state.value
        : this.props.children
        ? { ...this.state.value }
        : disabled
        ? defaultDisabledValue
        : defaultValue
      : escapeHtml(
          this.state.focus
            ? this.state.value
            : this.props.children
            ? { ...this.state.value }
            : disabled
            ? defaultDisabledValue
            : defaultValue,
        )
    return (
      <div className={this.state.expandable ? 'expandable' : ''}>
        <pre
          style={{
            ...(this.props.style || {}),
            height:
              this.state.expanded || !this.state.expandable
                ? 'auto'
                : collapsedHeight,
            opacity:
              typeof this.state.expandable === 'boolean' ||
              this.props.forceExpanded
                ? 1
                : 0,
          }}
          ref={this.setEl}
        >
          <code
            style={this.props.style}
            data-test={this.props['data-test']}
            contentEditable={!!this.props.onChange}
            onBlur={this.onBlur}
            onFocus={this.onFocus}
            onInput={this._handleInput}
            className={`${className} ${
              !this.state.value || !this.state.value.__html ? 'empty' : ''
            }`}
            dangerouslySetInnerHTML={html}
          />
        </pre>
        {this.state.expandable && (
          <div className='expand text-center mt-2'>
            <Button
              theme='text'
              onClick={() => this.setState({ expanded: !this.state.expanded })}
            >
              {this.state.expanded ? 'Hide' : 'Show More'}
              <span
                className={`icon ml-2 ion text-primary ${
                  this.state.expanded
                    ? 'ion-ios-arrow-up'
                    : 'ion-ios-arrow-down'
                }`}
              />
            </Button>
          </div>
        )}
      </div>
    )
  }
}

Highlight.defaultProps = {
  className: null,
  element: null,
  innerHTML: false,
}

export default Highlight
