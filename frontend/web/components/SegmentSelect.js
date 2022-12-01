import React from 'react';
import { Component } from 'react';
import { components } from 'react-select';
import _data from '../../common/data/base/_data';
const PAGE_SIZE = 100;
class FlagSelect extends Component {
    state = {
        search: '',
    }

    componentDidMount() {
        this.fetch();
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.projectId !== this.props.projectId) {
            this.fetch();
        }
    }

    search =  _.throttle((search) => {
        this.setState({search},this.fetch)
    }, 1000)

    loadMore = ()=>{
        this.setState({ isLoading: true, loadingMore: true });
        _data.get(this.state.next)
            .then((res)=>{
                this.setState({ isLoading: false, loadingMore:false, data: this.state.data.concat(res.results), next:res.next })
            }).catch(()=>{
            this.setState({loading:false, loadingMore:false})
        })

    }
    fetch =() => {
        this.setState({ isLoading: true });
        const search = this.state.search;
        _data.get(`${Project.api}projects/${this.props.projectId}/segments/?page_size=${PAGE_SIZE}&q=${encodeURIComponent(this.state.search || '')}`)
            .then(res => {
                this.setState({loading:false})
                if (search !== this.state.search) {
                    return
                }
                this.setState({ data: res.results, next:res.next, isLoading: false })
            }).catch(()=>{
                this.setState({loading:false})
            })
    }


    render() {
        if (!this.state.data) {
            return <div className="text-center"><Loader/></div>;
        }

        const options =  (this.state.data ? this.props.filter ? this.state.data.filter(this.props.filter) : this.state.data : [])
            .map(({ name: label, id: value, feature }) => ({ value, label, feature }))
        return (
            <Select
                data-test={this.props['data-test']}
                placeholder={this.props.placeholder}
                value={this.props.value}
                onChange={this.props.onChange}
                onInputChange={(e)=>{
                    this.search(e)
                }}
                components={{
                    Menu: ({...props})=> {
                        return     <components.Menu {...props}>
                            {props.children}
                            {!!this.state.next && (
                                <div className="text-center mb-4">
                                    <ButtonOutline onClick={this.loadMore} disabled={this.state.loadingMore}>
                                        Load More
                                    </ButtonOutline>
                                </div>
                            )
                            }
                        </components.Menu>
                    },
                    Option: ({ innerRef, innerProps, children, data }) => (
                        <div ref={innerRef} {...innerProps} className="react-select__option">
                            {children}{!!data.feature && (
                            <div className="unread ml-2 px-2">
                                Feature-Specific
                            </div>
                        )}
                        </div>
                    ),
                }}
                options={
                    options
                }
                styles={{
                    control: base => ({
                        ...base,
                        '&:hover': { borderColor: '$bt-brand-secondary' },
                        border: '1px solid $bt-brand-secondary',
                    }),
                }}
            />
        );
    }
}

export default FlagSelect;
