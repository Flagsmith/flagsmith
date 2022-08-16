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
const collapsedHeight = 110;
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
      if (nodes[0] && nodes[0].innerHTML && nodes[0].innerHTML.match(/[<>]/)) {
          if (!this.state.focus) {
              nodes[0].innerHTML = nodes[0].innerText
          }
              this.highlightCode()
          return
      }
      if (typeof hljs !== 'undefined') {
          for (let i = 0; i < nodes.length; i++) {
              hljs.highlightBlock(nodes[i]);
          }
      }
  };

  setEl(el) {
      this.el = el;
      this.measure = (force) => {
          if (this.props.forceExpanded) return;
          if (!this.el) return;
          const height = this.el.clientHeight;
          if (!this.state.expandable && height>collapsedHeight) {
              this.setState({ expandable: true, expanded: false });
          }
          if (typeof this.state.expandable !== 'boolean' || force) {
              if (height > collapsedHeight) {
                  this.setState({ expandable: true, expanded: false });
              } else if (!height) {
                  setTimeout(() => { this.measure(); }, 50);
              } else {
                  this.setState({ expandable: false });
              }
          }
      };
      this.measure();
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
      if (nextState.expandable !== this.state.expandable) return true;
      if (nextState.expanded !== this.state.expanded) return true;
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

        const html = this.props.preventEscape ? this.state.focus ? this.state.value : this.props.children ? { ...this.state.value } : defaultValue
            : escapeHtml(this.state.focus ? this.state.value : this.props.children ? { ...this.state.value } : defaultValue)
        return (
            <div className={this.state.expandable ? 'expandable' : ''}>
                <pre style={{ ...(this.props.style || {}), opacity: typeof this.state.expandable === 'boolean' ? 1 : 0, height: (this.state.expanded || !this.state.expandable) ? 'auto' : collapsedHeight }} ref={this.setEl}>
                    <code
                      style={this.props.style}
                      data-test={this.props['data-test']}
                      contentEditable={!!this.props.onChange}
                      onBlur={this.onBlur}
                      onFocus={this.onFocus}
                      onInput={this._handleInput}
                      className={`${className} ${!this.state.value || !this.state.value.__html ? 'empty' : ''}`}
                      dangerouslySetInnerHTML={html}
                    />

                </pre>
                {this.state.expandable && (
                    <div className="expand text-center mt-2">
                        <ButtonLink onClick={() => this.setState({ expanded: !this.state.expanded })} className="btn--link-primary">
                            {this.state.expanded ? 'Hide' : 'Show More'}
                            <span className={`icon ml-2 ion text-primary ${this.state.expanded ? 'ion-ios-arrow-up' : 'ion-ios-arrow-down'}`}/>
                        </ButtonLink>
                    </div>
                )}
            </div>

        );
    }
}

Highlight.defaultProps = {
    innerHTML: false,
    className: null,
    element: null,
};

export default Highlight;
