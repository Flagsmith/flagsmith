/**
 * Created by kylejohnson on 30/07/2016.
 */
const Tabs = class extends React.Component {
    static displayName = 'Tabs'

    render() {
        const children = this.props.children.filter((c)=>!!c);
        return (
            <div className={`tabs ${this.props.className || ''}`}>
                <div className="tabs-nav" style={isMobile ? { flexWrap: 'wrap' } : {}}>
                    {children.map((child, i) => {
                        const isSelected = this.props.value == i;
                        if (!child) {
                            return  null
                        }
                        return (
                            <Button
                              type="button"
                              data-test={child.props['data-test']}
                              id={child.props.id}
                              key={`button${i}`}
                              onClick={(e) => {
                                  e.stopPropagation();
                                  e.preventDefault();
                                  this.props.onChange(i);
                              }}
                              className={`btn-tab btn-primary${isSelected ? ' tab-active' : ''}`}
                            >
                                {child.props.tabLabel}
                            </Button>
                        );
                    })}
                </div>
                <div
                  className="tab-line" style={{
                      width: `${100 / children.length}%`,
                      left: `${100 / children.length * this.props.value}%`,
                  }}
                />
                <div className="tabs-content">
                    {children.map((child, i) => {
                        const isSelected = this.props.value == i;
                        return (
                            <div key={`content${i}`} className={`tab-item${isSelected ? ' tab-active' : ''}`}>
                                {child}
                            </div>
                        );
                    })}
                </div>
            </div>
        );
    }
};

Tabs.defaultProps = {
    className: '',
    value: 0,
};

Tabs.propTypes = {
    onChange: OptionalFunc,
    children: RequiredElement,
    value: OptionalNumber,
};

module.exports = Tabs;

// Example Usage
//   <Tabs value={this.state.tab} onChange={this.selectTab}>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 1 content</h2>
//     </TabItem>
//     <TabItem tabLabel={(<span className="fa fa-phone tab-icon"/>)}>
//       <h2>Tab 2 content</h2>
//     </TabItem>
//   </Tabs>
