import ModalHR from 'components/modals/ModalHR'
import { oneOf } from 'prop-types'
/**
 * Created by kylejohnson on 30/07/2016.
 */
const Tabs = class extends React.Component {
  static displayName = 'Tabs'

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor() {
    super()
    this.state = {
      value: 0,
    }
  }
  render() {
    const children = (
      this.props.children?.length ? this.props.children : [this.props.children]
    ).filter((c) => !!c)
    let value = this.props.uncontrolled ? this.state.value : this.props.value
    if (this.props.urlParam) {
      const tabParam = Utils.fromParam()[this.props.urlParam]
      if (tabParam) {
        const tab = children.findIndex((v) => {
          return (
            (v?.props?.tabLabelString || v?.props?.tabLabel)
              ?.toLowerCase()
              .replace(/ /g, '-') === tabParam
          )
        })
        if (tab !== -1) {
          value = tab
        }
      }
    }

    const hideNav = children.length === 1 && this.props.hideNavOnSingleTab
    return (
      <div className={`tabs ${this.props.className || ''}`}>
        <div
          className={`tabs-nav ${this.props.theme}`}
          style={isMobile ? { flexWrap: 'wrap' } : {}}
        >
          {!hideNav &&
            children.map((child, i) => {
              const isSelected = value == i
              if (!child) {
                return null
              }
              return (
                <Button
                  type='button'
                  theme={this.props.buttonTheme}
                  data-test={child.props['data-test']}
                  id={child.props.id}
                  key={`button${i}`}
                  onClick={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    if (this.props.urlParam) {
                      const currentParams = Utils.fromParam()
                      const history =
                        this.props.history || this.context.router.history
                      history.replace(
                        `${document.location.pathname}?${Utils.toParam({
                          ...currentParams,
                          [this.props.urlParam]: (
                            child.props.tabLabelString || child.props.tabLabel
                          )
                            .toLowerCase()
                            .replace(/ /g, '-'),
                        })}`,
                      )
                    } else if (this.props.uncontrolled) {
                      this.setState({ value: i })
                    }
                    this.props.onChange?.(i)
                  }}
                  className={`btn-tab ${isSelected ? ' tab-active' : ''}`}
                >
                  {child.props.tabLabel}
                </Button>
              )
            })}
        </div>
        {this.props.theme === 'tab' && !hideNav && (
          <ModalHR className='tab-nav-hr' />
        )}
        <div className='tabs-content'>
          {children.map((child, i) => {
            const isSelected = value === i
            return (
              <div
                key={`content${i}`}
                className={`tab-item ${isSelected ? ' tab-active' : ''} ${
                  this.props.isRoles && 'p-0'
                }`}
              >
                {child}
              </div>
            )
          })}
        </div>
      </div>
    )
  }
}

Tabs.defaultProps = {
  className: '',
  theme: 'tab',
  value: 0,
}

Tabs.propTypes = {
  children: RequiredElement,
  onChange: OptionalFunc,
  theme: oneOf(['tab', 'pill']),
  uncontrolled: OptionalBool,
  value: OptionalNumber,
}

export default Tabs

// Example Usage
//   <Tabs value={this.state.tab} onChange={this.selectTab}>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 1 content</h2>
//     </TabItem>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 2 content</h2>
//     </TabItem>
//   </Tabs>
