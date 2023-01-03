import React from 'react';
import SparklesIcon from './svg/SparklesIcon';

let prom;
class _Headway extends React.Component {
    state = {
        ready:false
    }
    componentDidMount() {
        try {
          if(Project.headway){
              if(!prom) {
                  prom =  Utils.loadScriptPromise("https://cdn.headwayapp.co/widget.js")
              }
              prom.then(()=>{
                  this.setState({ready:true},()=>{
                      Headway.init({
                          enabled: true,
                          selector: '#headway',
                          account: Project.headway,
                      });
                  })
              })
          }
        } catch (e) {}
    }

    render() {
        if(!Project.headway || !this.state.ready){
            return null
        }
        return (
            <Row className={this.props.className}>
                <Row onClick={() => {
                    Headway.show();
                }}
                >
                    <SparklesIcon />
                    Updates
                </Row>
                <span id="headway"/>
            </Row>
        );
    }
}

export default _Headway;
