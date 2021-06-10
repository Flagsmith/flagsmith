import data from '../data/base/_data';

export default (WrappedComponent) => {
    class HOC extends React.Component {
        static displayName = 'withWebhooks';

        getWebhooks = () => {
            return data.get(`${Project.api}organisations/${AccountStore.getOrganisation().id}/webhooks/`)
                .then((webhooks) => {
                    this.setState({
                        webhooks: webhooks.results,
                        webhooksLoading: false,
                    });
                });
        }

        deleteWebhook = (webhook) => {
            this.setState({ webhooksLoading: true });
            return data.delete(`${Project.api}organisations/${AccountStore.getOrganisation().id}/webhooks/${webhook.id}/`)
                .then((webhooks) => {
                    this.getWebhooks();
                });
        }


        saveWebhook = (webhook) => {
            this.setState({ webhooksLoading: true });
            return data.put(`${Project.api}organisations/${AccountStore.getOrganisation().id}/webhooks/${webhook.id}/`, webhook)
                .then((webhooks) => {
                    this.getWebhooks();
                });
        }


        createWebhook = (webhook) => {
            this.setState({ webhooksLoading: true });
            return data.post(`${Project.api}organisations/${AccountStore.getOrganisation().id}/webhooks/`, webhook)
                .then((webhooks) => {
                    this.getWebhooks();
                });
        }

        render() {
            return (
                <WrappedComponent
                  ref="wrappedComponent"
                  saveWebhook={this.saveWebhook}
                  createWebhook={this.createWebhook}
                  deleteWebhook={this.deleteWebhook}
                  getWebhooks={this.getWebhooks}
                  {...this.props}
                  {...this.state}
                />
            );
        }
    }

    return HOC;
};
