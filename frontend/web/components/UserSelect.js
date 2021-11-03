import React, { Component } from 'react';
import InlineModal from './InlineModal';


class TheComponent extends Component {
    state = {
        filter: '',
    };

    render() {
        const users = this.props.users && this.props.users.filter((v) => {
            const search = this.state.filter.toLowerCase();
            if (!search) return true;
            return `${v.first_name} ${v.last_name}`.toLowerCase().includes(search);
        });
        const value = this.props.value || [];
        return (
            <InlineModal
              title="Users"
              isOpen={this.props.isOpen}
              onClose={this.props.onToggle}
              className="inline-modal--tags"
            >
                <Input
                  disabled={this.props.disabled}
                  value={this.state.filter} onChange={e => this.setState({ filter: Utils.safeParseEventValue(e) })} className="full-width mb-2"
                  placeholder="Type or choose a user"
                />
                <div style={{ maxHeight: 200, overflowY: 'auto' }}>
                    {users && users.map(v => (
                        <div className="list-item clickable" key={v.id}>
                            <Row
                              onClick={() => {
                                  const isRemove = value.includes(v.id);
                                  if (isRemove && this.props.onRemove) {
                                      this.props.onRemove(v.id);
                                  } else if (!isRemove && this.props.onAdd) {
                                      this.props.onAdd(v.id);
                                  }
                                  this.props.onChange && this.props.onChange(
                                      isRemove ? value.filter(f => f !== v.id)
                                          : value.concat([v.id]),
                                  );
                              }} space
                            >
                                <Flex className={value.includes(v.id) ? 'font-weight-bold' : ''}>
                                    {v.first_name} {v.last_name}
                                </Flex>
                                {value.includes(v.id) && (
                                    <span style={{ fontSize: 24 }} className="ion `text-primary` ion-ios-checkmark"/>
                                )}
                            </Row>
                        </div>
                    ))}
                </div>
            </InlineModal>
        );
    }
}

module.exports = hot(module)(TheComponent);
