import React from 'react';

if (typeof hljs !== 'undefined') {
    hljs.initHighlightingOnLoad();
}
function escapeHtml(unsafe) {
    if (!unsafe || !unsafe.__html) return unsafe;
    return {
        __html: unsafe.__html
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;'),
    };
}
const defaultValue = { __html: 'Enter a value...' };
class Highlight extends React.Component {
  state = {
      value: { __html: this.props.children },
  }

  constructor(props) {
      super(props);
      this.setEl = this.setEl.bind(this);
  }

  componentDidMount() {
      this.highlightCode();
  }

  componentDidUpdate() {
      this.highlightCode();
  }

  highlightCode = () => {
      const nodes = this.el.querySelectorAll('pre code');

      if (typeof hljs !== 'undefined') {
          for (let i = 0; i < nodes.length; i++) {
              hljs.highlightBlock(nodes[i]);
          }
      }
  };

  setEl(el) {
      this.el = el;
  }

  componentWillUpdate(nextProps, nextState, nextContext) {
      if (nextProps.className !== this.props.className) {
          setTimeout(() => {
              this.highlightCode();
          }, 100);
      }
      if (this.state.prevValue != nextProps.children) {
          this.state.value.__html = nextProps.children;
          this.state.key = Date.now();
      }
  }

  shouldComponentUpdate(nextProps, nextState, nextContext) {
      if (nextState.focus !== this.state.focus) return true;
      if (nextProps.className !== this.props.className) return true;
      if (nextProps['data-test'] !== this.props['data-test']) return true;
      if (this.state.value.__html === `${nextProps.children}`) return false;
      return true;
  }

  _handleInput = (event) => {
      const value = event.target.innerText;
      this.state.value.__html = value;
      this.props.onChange(value);
  };

    onFocus= () => {
        this.setState({ focus: true });
    }

    onBlur= () => {
        this.setState({ focus: false });
        this.highlightCode();
    }

    render() {
        const { children, className, element: Element, innerHTML } = this.props;
        const props = { ref: this.setEl, className };

        if (innerHTML) {
            props.dangerouslySetInnerHTML = { __html: children };
            if (Element) {
                return <Element {...props} />;
            }
            return <div {...props} />;
        }

        if (Element) {
            return <Element {...props}>{children}</Element>;
        }
        return (
            <pre style={this.props.style} ref={this.setEl}>
                <code
                  style={this.props.style}
                  data-test={this.props['data-test']}
                  contentEditable={!!this.props.onChange}
                  onBlur={this.onBlur}
                  onFocus={this.onFocus}
                  onInput={this._handleInput}
                  className={className}
                  dangerouslySetInnerHTML={escapeHtml(this.state.focus ? this.state.value : this.props.children ? { ...this.state.value } : defaultValue)}
                />
            </pre>
        );
    }
}

Highlight.defaultProps = {
    innerHTML: false,
    className: null,
    element: null,
};

export default Highlight;
