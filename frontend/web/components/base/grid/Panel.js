import { PureComponent } from 'react';

const Panel = class extends PureComponent {
    static displayName = 'Panel'

    render() {
        return (
            <div className={`panel panel-default ${this.props.className || ''} ${this.props.title ? '' : 'mt-2'}`}>
                {(this.props.title || this.props.action) && (
                <div className="panel-heading">
                    <Row space>
                        <Row className="flex-1">
                            {this.props.icon && (
                            <span className="panel-icon"><span className={`icon ${this.props.icon}`}/></span>
                            )}
                            <Flex className="m-b-0 title">{this.props.title}</Flex>
                        </Row>
                        {this.props.action}
                    </Row>
                </div>
                )}

                <div className="panel-content">
                    {this.props.children}
                    {this.props.renderFooter && this.props.renderFooter()}
                </div>
            </div>
        );
    }
};

Panel.displayName = 'Panel';

Panel.propTypes = {
    title: oneOfType([OptionalObject, OptionalString]),
    icon: OptionalString,
    children: OptionalNode,
};

module.exports = Panel;
