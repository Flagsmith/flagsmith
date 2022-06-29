// import propTypes from 'prop-types';
import React, { PureComponent } from 'react';
import color from 'color';
import cx from 'classnames';
import withTags from '../../common/providers/withTags';
import InlineModal from './InlineModal';

export class TagValues extends PureComponent {
  static displayName = 'TheComponent';

  static propTypes = {
  };

  render() {
      const { props: { tags } } = this;
      return (
          <>
              {tags && tags.map(tag => this.props.isSelected(tag) && (
              <Tag
                onClick={this.props.onAdd}
                className="px-2 py-2 mr-2"
                tag={tag}
              />
              ))}
              {!!this.props.onAdd && (
              <Button onClick={this.props.onAdd} type="button" className="btn--outline">
                Add Tag
              </Button>
              ) }

          </>
      );
  }
}
export class Tag extends PureComponent {
  static displayName = 'TheComponent';

  state = {
      hover: false,
  }

  static propTypes = {
      selected: propTypes.bool,
      className: propTypes.string,
      onClick: propTypes.func,
      tag: propTypes.shape({
          color: propTypes.string,
      }),
  };

  toggleHover =() => this.setState({ hover: !this.state.hover })

  getColor = () => {
      const { props: { deselectedColor, tag, selected } } = this;
      if (selected) {
          return tag.color;
      }
      return deselectedColor || tag.color;
  }

  render() {
      const { props: { onClick, tag, selected, className } } = this;
      if (!this.props.hideNames) {
          return (
              <ToggleChip color={this.getColor()} active={selected} onClick={onClick ? () => onClick(tag) : null}>
                  {tag.label}
              </ToggleChip>
          );
      }

      return (
          <div
            onClick={onClick ? () => onClick(tag) : null}
            onMouseEnter={onClick ? this.toggleHover : null}
            onMouseLeave={onClick ? this.toggleHover : null}
            style={{ backgroundColor: this.state.hover ? color(this.getColor()).darken(0.1) : this.getColor() }}
            className={cx('tag', { selected, hideNames: this.props.hideNames }, className)}
          >
              <div>
                  {tag.label ? (
                      <Row space>
                          {this.props.hideNames ? '' : tag.label}
                          {selected && (
                          <span className="icon ion-md-checkmark"/>
                          )}
                      </Row>
                  ) : (
                      <div className="text-center">
                          {selected && (
                          <span className="icon ion-md-checkmark"/>
                          )}
                      </div>
                  )}
              </div>
          </div>
      );
  }
}

class _CreateEditTag extends PureComponent {
  static displayName = 'TheComponent';

  state = {
      tag: this.props.tag ? { ...this.props.tag } : {},
  }

  componentDidMount() {
      this.input && this.input.focus();
  }

  update = (index, e) => {
      this.setState({
          tag: {
              ...this.state.tag,
              [index]: Utils.safeParseEventValue(e),
          },
      });
  }

  save = () => {
      const disabled = this.props.tagsSaving || !this.state.tag.color || !this.state.tag.label;
      if (disabled) return;
      const isEdit = !!this.state.tag.id;
      const func = isEdit ? AppActions.updateTag : AppActions.createTag;
      func(this.props.projectId, this.state.tag, (tag) => {
          this.setState({ tag });
          this.props.onComplete && this.props.onComplete(tag);
      });
  }

  onKeyDown = (e) => {
      if (e.key === 'Enter') {
          this.save();
      }
  }

  render() {
      const isEdit = !!this.state.tag.id;
      return (
          <div>
              <InputGroup
                value={this.state.tag.label}
                ref={input => this.input = input}
                inputProps={{ name: 'create-tag-name', className: 'full-width mb-2', onKeyDown: this.onKeyDown }}
                title="Name"
                onChange={e => this.update('label', e)}
              />
              <InputGroup
                title="Select a color"
                component={(
                    <Row className="mb-2">
                        {Constants.tagColors.map(color => (
                            <div                               className="tag--select mr-2 mb-2">
                                <Tag
                                    onClick={e => this.update('color', e.color)}
                                    key={color}
                                    selected={this.state.tag.color === color}
                                    tag={{
                                        color,
                                        id: color,
                                    }}
                                />
                            </div>

                        ))}
                    </Row>
)}
              />
              <div className="text-center">
                  <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                      {({ permission, isLoading }) => Utils.renderWithPermission(permission, Constants.projectPermissions('Admin'),
                          <Button onClick={this.save} type="button" disabled={this.props.tagsSaving || !this.state.tag.color || !this.state.tag.label || !permission}>
                              {isEdit ? 'Save Tag' : 'Create Tag' }
                          </Button>
                      )}
                  </Permission>
              </div>
          </div>
      );
  }
}

const CreateEditTag = withTags(_CreateEditTag);

class TheComponent extends PureComponent {
  static displayName = 'TheComponent';

  static propTypes = {
      onChange: propTypes.func,
      value: propTypes.arrayOf(propTypes.number),
  };

  state = {
      isOpen: false,
      tab: 'SELECT',
  }


  componentDidMount() {
      AppActions.getTags(this.props.projectId);
  }

  toggle = () => this.setState({ isOpen: !this.state.isOpen })

  setFilter = e => this.setState({ filter: Utils.safeParseEventValue(e) })


  filter = (tags) => {
      const filter = this.state.filter && this.state.filter.toLowerCase();
      if (filter) {
          return _.filter(tags, tag => tag.label.toLowerCase().includes(filter));
      }
      return tags;
  }

  selectTag = (tag) => {
      const value = this.props.value || [];
      const isSelected = this.props.isSelected(tag);
      if (isSelected) {
          this.props.onChange(_.filter(value, id => id !== tag.id));
      } else {
          this.props.onChange(value.concat([tag.id]));
      }
  }

  editTag = (tag) => {
      this.setState({
          tag,
          tab: 'EDIT',
      });
  }

  deleteTag = (tag) => {
      openConfirm('Please confirm', 'Are you sure you wish to delete this tag?', () => {
          const value = this.props.value || [];
          this.props.onChange(_.filter(value, id => id !== tag.id));
          AppActions.deleteTag(this.props.projectId, tag);
          this.setState({ isOpen: true });
      });
  }

  render() {
      const { props: {
          tags,
          tagsLoading,
          tagsSaving,
          readOnly,
      } } = this;
      const projectTags = tags && tags[this.props.projectId];
      const filteredTags = projectTags && this.filter(projectTags);
      const noTags = projectTags && !projectTags.length;
      return (
          <div>
              <Row className="inline-tags mt-2">
                  <TagValues
                    onAdd={readOnly ? null : this.toggle} tags={projectTags} isSelected={this.props.isSelected}
                    value={this.props.value}
                  />
              </Row>

              <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                  {({permission:projectAdminPermission})=>(
              <InlineModal
                title="Tags"
                isOpen={this.state.isOpen}
                onBack={() => this.setState({ tab: 'SELECT' })}
                showBack={this.state.tab !== 'SELECT'}
                onClose={this.toggle}
                className="inline-modal--tags"
              >

                  {this.state.tab === 'SELECT' && !noTags && (
                  <div>
                      <Input
                        value={this.state.filter} onChange={this.setFilter} className="full-width mb-2"
                        placeholder="Search tags..."
                      />
                      {tagsLoading && !projectTags && (
                      <div className="text-center">
                          <Loader/>
                      </div>
                      )}
                      <div className="tag-list">
                          {filteredTags && filteredTags.map((tag, index) => (
                              <div key={tag.id}>
                                  <Row className={"py-2"}>
                                      <Flex>
                                          <Tag
                                            className="px-2 py-2" onClick={this.selectTag} selected={this.props.isSelected(tag)}
                                            tag={tag}
                                          />
                                      </Flex>
                                      <Permission level="project" permission="ADMIN" id={this.props.projectId}>
                                          {({ permission, isLoading }) => Utils.renderWithPermission(permission, Constants.projectPermissions('Admin'), (
                                              <>
                                                  {!readOnly && !!permission && (
                                                      <>
                                                          <div onClick={() => this.editTag(tag)} className="ml-2 px-2 clickable">
                                                              <span className="icon ion-md-settings"/>
                                                          </div>
                                                          <div onClick={() => this.deleteTag(tag)} className="ml-2 px-2 clickable">
                                                              <img width={16} src="/static/images/icons/bin.svg" />
                                                          </div>
                                                      </>
                                                  )}
                                              </>
                                      ))}
                                      </Permission>
                                  </Row>
                              </div>
                          ))}
                          {!readOnly && (
                          <div className="text-center mb-2 mt-3">
                              {Utils.renderWithPermission(projectAdminPermission, Constants.projectPermissions("Admin"), (
                                      <ButtonLink
                                          disabled={!projectAdminPermission}
                                          buttonText=" Create a New Tag" onClick={() => this.setState({ tab: 'CREATE', filter: '' })}
                                          type="button"
                                      >
                                          <span className="ml-3 icon ion-md-add"/>
                                      </ButtonLink>
                                  ))}
                          </div>
                          )}
                          {projectTags && projectTags.length && !filteredTags.length ? (
                              <div className="text-center">
                          No results for "<strong>{this.state.filter}</strong>"
                              </div>
                          ) : null}
                          {
                        noTags && (
                        <div className="text-center">
                            You have no tags yet
                        </div>
                        )
                      }

                      </div>
                  </div>
                  )}
                  {(this.state.tab === 'CREATE' || noTags) && (
                  <CreateEditTag
                    projectId={this.props.projectId} onComplete={(tag) => {
                        this.selectTag(tag);
                        this.setState({ tab: 'SELECT' });
                    }}
                  />
                  )}
                  {
                  this.state.tab === 'EDIT' && (
                  <CreateEditTag
                    tagsSaving={tagsSaving}
                    projectId={this.props.projectId} tag={this.state.tag} onComplete={(tag) => {
                        this.selectTag(tag);
                        this.setState({ tab: 'SELECT' });
                    }}
                  />
                  )
                  }
              </InlineModal>
                      )}
              </Permission>
          </div>

      );
  }
}

export default withTags(TheComponent);
