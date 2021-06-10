import TagsStore from '../stores/tags-store';

const getState = () => (
    {

        tags: TagsStore.model,
        tagsLoading: TagsStore.isLoading,
        tagsSaving: TagsStore.isSaving,
    }
);
export default (WrappedComponent) => {
    class HOC extends React.Component {
        static displayName = 'withFoo';

        constructor(props) {
            super(props);
            ES6Component(this);
            this.state = getState();

            this.listenTo(TagsStore, 'change', () => {
                this.setState(getState());
            });
        }


        isSelected = tag => this.props.value && this.props.value.includes(tag.id)


        render() {
            return (
                <WrappedComponent
                  ref="wrappedComponent"
                  isSelected={this.isSelected}
                  {...this.props}
                  {...this.state}
                />
            );
        }
    }

    return HOC;
};
