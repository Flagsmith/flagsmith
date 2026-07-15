import React from 'react'
import hljs from 'highlight.js'
import Button from './base/forms/Button'

type HtmlValue = { __html?: string }

export type HighlightProps = {
  // The code/value to render (via dangerouslySetInnerHTML, so a string), and
  // the initial value in editor mode.
  children?: string
  className?: string
  style?: React.CSSProperties
  'data-test'?: string
  // Display
  forceExpanded?: boolean // skip the collapse / "Show more" measurement
  preventEscape?: boolean // render children as-is (don't HTML-escape)
  innerHTML?: boolean // render children as raw HTML into `element`/div
  element?: React.ElementType // wrapper element for the innerHTML branch
  // Editor mode (contentEditable), active when onChange is provided
  onChange?: (value: string) => void
  onBlur?: () => void
  disabled?: boolean
}

type HighlightState = {
  value: HtmlValue
  focus?: boolean
  expandable?: boolean
  expanded?: boolean
  key?: number
  // Never assigned; the value-sync comparison below relies on it always being
  // undefined so the draft re-syncs to children on update. Kept as-is.
  prevValue?: string
}

function escapeHtml(unsafe: HtmlValue | undefined): HtmlValue | undefined {
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

const defaultValue: HtmlValue = { __html: 'Enter a value...' }
const defaultDisabledValue: HtmlValue = { __html: ' ' }
const collapsedHeight = 110

class Highlight extends React.Component<HighlightProps, HighlightState> {
  el: HTMLElement | null = null
  measure: (force?: boolean) => void = () => {}

  state: HighlightState = {
    value: { __html: this.props.children },
  }

  constructor(props: HighlightProps) {
    super(props)
    this.setEl = this.setEl.bind(this)
  }

  componentDidMount() {
    this.highlightCode()
  }

  componentDidUpdate(prevProps: HighlightProps) {
    this.highlightCode()
    if (this.props.className !== prevProps.className) {
      setTimeout(() => this.highlightCode(), 100)
    }
    if (this.state.prevValue !== this.props.children) {
      this.setState({
        key: Date.now(),
        value: { ...this.state.value, __html: this.props.children },
      })
    }
  }

  highlightCode = () => {
    const nodes = this.el?.querySelectorAll('pre code')
    nodes?.forEach((node) => hljs.highlightElement(node as HTMLElement))
  }

  setEl(el: HTMLElement | null) {
    this.el = el
    this.measure = (force?: boolean) => {
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
          setTimeout(() => this.measure(), 50)
        } else {
          this.setState({ expandable: false })
        }
      }
    }
    this.measure()
  }

  shouldComponentUpdate(nextProps: HighlightProps, nextState: HighlightState) {
    if (nextState.focus !== this.state.focus) return true
    if (nextProps.className !== this.props.className) return true
    if (nextState.expandable !== this.state.expandable) return true
    if (nextState.expanded !== this.state.expanded) return true
    if (nextProps['data-test'] !== this.props['data-test']) return true
    return this.state.value.__html !== `${nextProps.children}`
  }

  handleInput = (event: React.FormEvent<HTMLElement>) => {
    const value = event.currentTarget.innerText
    this.state.value.__html = value
    this.props.onChange?.(value)
  }

  onFocus = () => this.setState({ focus: true })

  onBlur = () => {
    this.setState({ focus: false })
    this.props.onBlur?.()
  }

  // The value to render before escaping: the live edit while focused, the
  // current value when there's content, otherwise a disabled/empty placeholder.
  getRawHtml(): HtmlValue | undefined {
    if (this.state.focus) return this.state.value
    if (this.props.children) return { ...this.state.value }
    return this.props.disabled ? defaultDisabledValue : defaultValue
  }

  render() {
    const { children, className, element: Element, innerHTML } = this.props

    if (innerHTML) {
      const htmlProps = {
        className,
        dangerouslySetInnerHTML: { __html: children ?? '' },
        ref: this.setEl,
      }
      if (Element) {
        return <Element {...htmlProps} />
      }
      return <div {...htmlProps} />
    }

    if (Element) {
      return (
        <Element className={className} ref={this.setEl}>
          {children}
        </Element>
      )
    }

    const raw = this.getRawHtml()
    const html = this.props.preventEscape ? raw : escapeHtml(raw)
    return (
      <div className={this.state.expandable ? 'expandable' : ''}>
        <pre
          className='mb-2'
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
            onInput={this.handleInput}
            className={`${className ?? ''} ${
              !this.state.value || !this.state.value.__html ? 'empty' : ''
            }`}
            dangerouslySetInnerHTML={{ __html: html?.__html ?? '' }}
          />
        </pre>
        {this.state.expandable && (
          <div className='expand text-center mb-2'>
            <Button
              className='h-auto'
              theme='text'
              onClick={() => this.setState({ expanded: !this.state.expanded })}
            >
              {this.state.expanded ? 'Hide' : 'Show More'}
              <span
                className={`icon ml-2 ion icon-action ${
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

export default Highlight
