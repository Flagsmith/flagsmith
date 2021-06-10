import React, { Component } from 'react';
import { ButtonLink } from '../base/forms/Button';
import Tabs from '../base/forms/Tabs';
import TabItem from '../base/forms/TabItem';
import PricingPanel from '../PricingPanel';
import ChipInput from '../ChipInput';

export default class ExampleOne extends Component {
    static displayName = 'CreateOrganisastionPage'

    constructor(props, context) {
        super(props, context);
        this.state = { name: '', tab: '', text: '',
            value: [], };
    }


    render() {
        // We can inject some CSS into the DOM.
        const styles = {
            root: {
                background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
                borderRadius: 3,
                border: 0,
                color: 'white',
                height: 48,
                padding: '0 30px',
                boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
            },
        };
        return (
            <div className="mt-5">
                <div className="container">
                    <section className="pt-5 pb-3">
                        <h2>Typeography</h2>
                        <h1>Heading H1</h1>
                        <h2>Heading H2</h2>
                        <h3>Heading H3</h3>
                        <h4>Heading H4</h4>
                        <h5>Heading H5</h5>
                        <h6>Heading H6</h6>
                        <p className="no-mb">This is a paragraph.</p>
                        <p className="text-small no-mb">This is some small paragraph text.</p>
                        <p>
                            View and manage
                            {' '}
                            <Tooltip
                              title={<ButtonLink href="#" buttonText="feature flags" />}
                              place="right"
                            >
                                {Constants.strings.FEATURE_FLAG_DESCRIPTION}
                            </Tooltip>
                            {' '}
                            and
                            {' '}
                            {' '}
                            <Tooltip
                              title={<ButtonLink buttonText="remote config" />}
                              place="right"
                            >
                                {Constants.strings.REMOTE_CONFIG_DESCRIPTION}
                            </Tooltip>
                            {' '}
                            for
                            your selected environment.

                        </p>
                    </section>

                    <section className="pt-5 pb-3">
                        <h2 className="mb-3">color</h2>

                        <h4>Brand</h4>
                        <div className="color-block color-block--brand-primary"/>
                        <div className="color-block color-block--brand-secondary"/>


                    </section>

                    <section className="pt-5 pb-3">
                        <h2>Buttons</h2>
                        <FormGroup>
                            <Button className="mr-3">Primary</Button>

                            <ButtonOutline className="mr-3">Outline</ButtonOutline>

                            <ButtonLink href="https://www.google.com/" buttonText="Text Button" />


                            <ButtonProject>S</ButtonProject>

                        </FormGroup>

                    </section>

                    <section className="pt-5 pb-3">
                        <h2>Forms</h2>

                        <FormGroup>
                            <Input
                              inputProps={{
                                  name: 'firstName',
                                  className: 'full-width',
                              }}
                              className="input-default full-width"
                              placeholder="First name"
                              type="text"
                              name="firstName" id="firstName"
                            />
                        </FormGroup>

                        <FormGroup>
                            <ChipInput
                                placeholder="User1, User2, User3"
                                inputStyle={{ border: '1px solid green', color: 'red' }}
                                textFieldStyle={{ border: '1px solid red' }}
                            />
                            <ChipInput
                                defaultValue={['foo', 'bar']}
                                fullWidth
                                chipRenderer={({ value, isFocused, isDisabled, handleClick, handleRequestDelete }, key) => (
                                    <Chip
                                        key={key}
                                        style={{ margin: '8px 8px 0 0', float: 'left', pointerEvents: isDisabled ? 'none' : undefined }}
                                        backgroundColor={isFocused ? 'red' : 'blue'}
                                        onTouchTap={handleClick}
                                        onRequestDelete={handleRequestDelete}
                                    >
                                        <Avatar size={32}>{value[0].toUpperCase()}</Avatar>
                                        {value}
                                    </Chip>
                                )}
                            />
                        </FormGroup>

                        <FormGroup className="mt-3">
                            <InputGroup
                              inputProps={{
                                  className: 'full-width',
                                  name: 'featureID',
                              }}
                              value={null}
                              type="text" title="ID"
                              placeholder="E.g. header_size"
                            />
                        </FormGroup>

                        <FormGroup className="mt-3">
                            <Select
                              data-test="select-segment"
                              placeholder="Select a segment"
                              value={0}
                              styles={{
                                  control: (base, state) => ({
                                      ...base,
                                      '&:hover': { borderColor: '$bt-brand-secondary' }, // border style on hover
                                      border: '1px solid $bt-brand-secondary', // default border color
                                      boxShadow: 'none', // no box-shadow
                                  }),
                              }}
                            />
                        </FormGroup>
                    </section>

                    <section className="pt-5 pb-3">
                        <h2 className="mb-5">Components</h2>

                        <FormGroup>
                            <h3>Panel</h3>
                            <Panel title="Panel" className="mb-5" >
                                Panel content
                            </Panel>

                            <Panel className="panel--grey mb-5" title="Panel Grey">
                                Panel content
                            </Panel>

                        </FormGroup>

                        <FormGroup>
                            <Tabs value={this.state.tab}>
                                <TabItem tabLabel="Hello">
                                    <p>Tab 1 content</p>
                                </TabItem>
                                <TabItem tabLabel="Tab 2">
                                    <p>Tab 2 content</p>
                                </TabItem>
                            </Tabs>


                        </FormGroup>

                        <FormGroup>
                            <PricingPanel/>
                        </FormGroup>
                    </section>

                </div>
            </div>
        );
    }
}
