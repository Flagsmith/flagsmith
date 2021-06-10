// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import withTags from '../../common/providers/withTags';
import { Tag } from './AddEditTags';

class TagSelect extends PureComponent {
    isSelected = tag => (this.props.value || []).includes(tag.id)

    onSelect = (tag) => {
        const value = this.props.value || [];
        if (value.includes(tag.id)) {
            this.props.onChange(_.filter(value, v => v !== tag.id));
        } else {
            this.props.onChange(value.concat([tag.id]));
        }
    }

    render() {
        const projectTags = (this.props.tags && this.props.tags[this.props.projectId]) || [];
        return (
            <Row className="tag-filter mx-2 mt-3">
                <div className="ml-1">
                    <Row>
                        {projectTags.map(tag => (
                          <div className="mr-1 mb-2">
                              <Tag
                                key={tag.id}
                                selected={this.isSelected(tag)}
                                onClick={this.onSelect}
                                className="px-2 py-2 mr-2"
                                tag={tag}
                              />
                          </div>

                        ))}
                    </Row>

                </div>

            </Row>
        );
    }
}

export default withTags(TagSelect);
