import React from 'react';
import { Component } from 'react';

class Token extends Component {

    constructor() {
        super();
        this.state = {
            showToken: false
        }
    }
    render() {
        if (!this.props.token) return null
        return      <Row>
            <div style={this.props.style} className={`${this.state.showToken?"font-weight-bold":""}`}>
                {this.state.showToken?this.props.token : this.props.token.split("").map((v)=>"*").join("").trim()}
            </div>
            <Button style={{width:80}} className={"ml-2 mr-4"} onClick={()=>this.setState({showToken:!this.state.showToken})}>{this.state.showToken?"Hide":"Show"}</Button>
        </Row>
    }
}

export default Token
