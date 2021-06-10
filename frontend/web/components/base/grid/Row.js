/**
 * Created by kylejohnson on 24/07/2016.
 */
import { PureComponent } from 'react';
import cn from 'classnames';

class Row extends PureComponent {
    static displayName = 'Row';

    static propTypes = {
        className: OptionalString,
        space: OptionalBool,
        children: OptionalNode,
        style: propTypes.any,
    };

    render() {
        const { space, noWrap, ...rest } = this.props;

        return (
            <div
              {...rest}
              className={cn({
                  'flex-row': true,
                  space,
                  noWrap,
              }, this.props.className)}
            >
                {this.props.children}
            </div>
        );
    }
}

module.exports = Row;
