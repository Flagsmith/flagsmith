
import React, { Component } from 'react';
import _data from '../../common/data/base/_data';
import ProjectStore from '../../common/stores/project-store';

const CreateEditIntegration = require('./modals/CreateEditIntegrationModal');

class Integration extends Component {


    add =() => {
        this.props.addIntegration(this.props.integration, this.props.id);
    }

    remove =(integration) => {
        this.props.removeIntegration(integration, this.props.id);
    }

    edit =(integration) => {
        this.props.editIntegration(this.props.integration, this.props.id, integration);
    }

    render() {
        const { image, title, description, perEnvironment, docs } = this.props.integration;
        const activeIntegrations = this.props.activeIntegrations;
        const showAdd = !(!perEnvironment && activeIntegrations && activeIntegrations.length);
        return (
            <Panel
              className="no-pad panel--transparent m-4"
              title={(
                  <Row style={{ flexWrap: 'noWrap' }}>
                      <Flex>
                          <img width={180} className="mr-4" src={image}/>

                          <div className="subtitle mt-2">
                              {description} {docs && <a href={docs} target="_blank">View docs</a> }
                          </div>
                      </Flex>
                      {showAdd && (
                      <Button
                        className="btn-lg btn-primary ml-4" id="show-create-segment-btn" data-test="show-create-segment-btn"
                        onClick={this.add}
                      >
                          <span className="icon ion-ios-apps text-white"/>
                          {' '}
                          Add integration
                      </Button>
                      )}
                  </Row>
                )}
            >
                {activeIntegrations && activeIntegrations.map(integration => (
                    <div
                      className="list-item clickable" onClick={() => this.edit(integration)}
                    >
                        <Row space>
                            <Flex>
                                <CreateEditIntegration readOnly data={integration} integration={this.props.integration} />
                            </Flex>
                            <Button
                              onClick={(e) => {
                                  e.preventDefault();
                                  e.stopPropagation();
                                  this.remove(integration);
                                  return false;
                              }}
                              className="btn btn--with-icon btn--condensed reveal--child btn--remove"

                              type="submit"
                            >
                                <RemoveIcon/>
                            </Button>
                        </Row>

                    </div>
                ))}
            </Panel>
        );
    }
}


class IntegrationList extends Component {
    state = {}
    static contextTypes = {
        router: propTypes.object.isRequired,
    };
    componentDidMount() {
        this.fetch();
    }

    fetch = () => {
        const integrationList = this.props.getValue('integration_data') && JSON.parse(this.props.getValue('integration_data'));
        this.setState({ isLoading: true });
        Promise.all(this.props.integrations.map((key) => {
            const integration = integrationList[key];
            if (integration) {
                if (integration.perEnvironment) {
                    return Promise.all(ProjectStore.getEnvs().map(env => _data.get(`${Project.api}environments/${env.api_key}/integrations/${key}/`)
                        .catch((e) => {

                        }))).then((res) => {
                        let allItems = [];
                        _.each(res, (envIntegrations, index) => {
                            if (envIntegrations && envIntegrations.length) {
                                allItems = allItems.concat(envIntegrations.map(int => ({ ...int, flagsmithEnvironment: ProjectStore.getEnvs()[index].api_key })));
                            }
                        });
                        return allItems;
                    });
                }
                return _data.get(`${Project.api}projects/${this.props.projectId}/integrations/${key}/`)
                    .catch((e) => {

                    });
            }
        })).then((res) => {
            console.log(res);
            this.setState({ isLoading: false, activeIntegrations: _.map(res, item => (!!item && item.length ? item : [])) });
        });
        const params = Utils.fromParam();
        if (params && params.configure) {
            const integrationList = this.props.getValue('integration_data') && JSON.parse(this.props.getValue('integration_data'));

            if (integrationList && integrationList[params.configure]) {
                setTimeout(()=>{
                    this.addIntegration(integrationList[params.configure], params.configure)
                    this.context.router.history.replace(document.location.pathname);
                },500)
            }
        }
    }

    removeIntegration =(integration, id) => {
        openConfirm('Confirm remove integration', `This will remove your integration from the ${integration.flagsmithEnvironment}` ? 'environment' : 'project' + ', it will no longer recieve data. Are you sure?', () => {
            if (integration.flagsmithEnvironment) {
                _data.delete(`${Project.api}environments/${integration.flagsmithEnvironment}/integrations/${id}/${integration.id}/`)
                    .then(this.fetch).catch(this.onError);
            } else {
                _data.delete(`${Project.api}projects/${this.props.projectId}/integrations/${id}/${integration.id}/`)
                    .then(this.fetch).catch(this.onError);
            }
        });
    }

    addIntegration =(integration, id) => {
        const params = Utils.fromParam()
        openModal(`${integration.title} Integration`, <CreateEditIntegration
          id={id} integration={integration}
          data={params.environment?{
              flagsmithEnvironment:params.environment
          }:null}
          projectId={this.props.projectId} onComplete={this.fetch}
        />);
    }

    editIntegration =(integration, id, data) => {
        openModal(`${integration.title} Integration`, <CreateEditIntegration
          id={id} integration={integration}
          data={data}
          projectId={this.props.projectId} onComplete={this.fetch}
        />);
    }

    render() {
        const integrationList = this.props.getValue('integration_data') && JSON.parse(this.props.getValue('integration_data'));
        return (
            <div>
                <div>
                    {this.props.integrations && !this.state.isLoading && this.state.activeIntegrations && integrationList ? (
                        this.props.integrations.map((i, index) => (
                            <Integration
                              addIntegration={this.addIntegration}
                              editIntegration={this.editIntegration}
                              removeIntegration={this.removeIntegration}
                              projectId={this.props.projectId}
                              id={i}
                              key={i}
                              activeIntegrations={this.state.activeIntegrations[index]}
                              integration={integrationList[i]}
                            />
                        ))
                    ) : (
                        <div className="text-center">
                            <Loader/>
                        </div>
                    )}
                </div>
            </div>
        );
    }
}

export default ConfigProvider(IntegrationList);
