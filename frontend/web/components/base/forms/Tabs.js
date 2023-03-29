const classNames = require('classnames')
/**
 * Created by kylejohnson on 30/07/2016.
 */
const Tabs = class extends React.Component {
  static displayName = 'Tabs'
  constructor() {
    super()
    this.state = {
      value: 0,
    }
  }
  render() {
    const children = this.props.children.filter((c) => !!c)
    const value = this.props.uncontrolled ? this.state.value : this.props.value
    return (
      <div
        className={`tabs ${this.props.className || ''} ${
          this.props.transparent ? 'tabs--transparent' : ''
        } ${this.props.inline ? 'tabs--inline' : ''}`}
      >
        <div className='tabs-nav' style={isMobile ? { flexWrap: 'wrap' } : {}}>
          {children.map((child, i) => {
            const isSelected = value == i
            if (!child) {
              return null
            }
            return (
              <Button
                type='button'
                data-test={child.props['data-test']}
                id={child.props.id}
                key={`button${i}`}
                onClick={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  if (this.props.uncontrolled) {
                    this.setState({ value: i })
                  } else {
                    this.props.onChange(i)
                  }
                }}
                className={`btn-tab btn-primary${
                  isSelected ? ' tab-active' : ''
                }`}
              >
                {child.props.tabIcon && (
                  <span
                    className={classNames('icon mr-2', child.props.tabIcon)}
                  />
                )}
                {child.props.tabLabel}
              </Button>
            )
          })}
          <div
            className='tab-line'
            style={{
              left: `${(100 / children.length) * value}%`,
              width: `${100 / children.length}%`,
            }}
          />
        </div>
        <div className='tabs-content'>
          {children.map((child, i) => {
            const isSelected = value === i
            return (
              <div
                key={`content${i}`}
                className={`tab-item${isSelected ? ' tab-active' : ''}`}
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
  value: 0,
}

Tabs.propTypes = {
  children: RequiredElement,
  inline: OptionalBool,
  onChange: OptionalFunc,
  transparent: OptionalBool,
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
