// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import withTags from '../../common/providers/withTags';
import { Tag } from './AddEditTags';

class TagValues extends PureComponent {
    render() {
        const projectTags = (this.props.tags && this.props.tags[this.props.projectId]) || [];

        const tags = _.filter(projectTags, (tag)=> {
            return (this.props.value||[]).includes(tag.id)
        });
        return (
            <Row className="tag-values">
                <Row>
                    {tags.map(tag => (
                      <Tag
                        hideNames
                        key={tag.id}
                        className={"mr-1"}
                        tag={tag}
                      />
                    ))}
                </Row>

            </Row>
        );
    }
}

export default withTags(TagValues);
