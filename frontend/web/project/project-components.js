import { PureComponent } from 'react';
import { hot } from 'react-hot-loader';
import Select from 'react-select';
import Button, { ButtonLink, ButtonOutline, ButtonProject } from '../components/base/forms/Button';
import RemoveIcon from '../components/RemoveIcon';
import Paging from '../components/Paging';
import ToggleChip from '../components/ToggleChip';


window.Dispatcher = require('../../common/dispatcher/dispatcher');
window.AppActions = require('../../common/dispatcher/app-actions');
window.Actions = require('../../common/dispatcher/action-constants');
window.Format = require('../../common/utils/format');
window.ES6Component = require('../../common/ES6Component');

window.Permission = require('../../common/providers/Permission');
window.IdentityProvider = require('../../common/providers/IdentityProvider');
window.IdentitySegmentsProvider = require('../../common/providers/IdentitySegmentsProvider');
window.SegmentListProvider = require('../../common/providers/SegmentListProvider');
window.AccountProvider = require('../../common/providers/AccountProvider');
window.AccountStore = require('../../common/stores/account-store');
window.FeatureListProvider = require('../../common/providers/FeatureListProvider');
window.OrganisationProvider = require('../../common/providers/OrganisationProvider');
window.SelectedProjectProvider = require('../../common/providers/SelectedProjectProvider');
window.ProjectProvider = require('../../common/providers/ProjectProvider');
window.EnvironmentProvider = require('../../common/providers/EnvironmentProvider');
window.IdentityListProvider = require('../../common/providers/IdentityListProvider');
window.AuditLogProvider = require('../../common/providers/AuditLogProvider');
window.ConfigProvider = require('../../common/providers/ConfigProvider');
window.OrganisationSelect = require('../components/OrganisationSelect');

window.Paging = Paging;

// Useful components
window.Gif = require('../components/base/Gif');
window.Row = require('../components/base/grid/Row');
window.Flex = require('../components/base/grid/Flex');
window.Column = require('../components/base/grid/Column');
window.Input = require('../components/base/forms/Input');

window.Button = Button;
window.ButtonOutline = ButtonOutline;
window.ButtonLink = ButtonLink;
window.ButtonProject = ButtonProject;
window.Panel = require('../components/base/grid/Panel');
window.FormGroup = require('../components/base/grid/FormGroup');
window.InputGroup = require('../components/base/forms/InputGroup');
window.Panel = require('../components/base/grid/Panel');
window.FormGroup = require('../components/base/grid/FormGroup');
window.InputGroup = require('../components/base/forms/InputGroup');


window.PanelSearch = require('../components/PanelSearch');
window.FeatureValue = require('../components/FeatureValue');
window.CodeHelp = require('../components/CodeHelp');

// Useful for components used all the time within a project
window.Loader = class extends PureComponent {
  static displayName = 'Loader';

  render() {
      return (
          <svg
            className="loader"
            version="1.1" id="loader-1" x="0px"
            y="0px"
            width="40px" height="40px" viewBox="0 0 50 50"
            style={{ enableBackground: '0 0 50 50' }}
          >
              <path
                fill="#6633ff"
                d="M25.251,6.461c-10.318,0-18.683,8.365-18.683,18.683h4.068c0-8.071,6.543-14.615,14.615-14.615V6.461z"
              >
                  <animateTransform
                    attributeType="xml"
                    attributeName="transform"
                    type="rotate"
                    from="0 25 25"
                    to="360 25 25"
                    dur="0.6s"
                    repeatCount="indefinite"
                  />
              </path>
          </svg>
      );
  }
};

window.Tooltip = require('../components/Toolip');

global.hot = hot;
global.ToggleChip = ToggleChip;
global.RemoveIcon = RemoveIcon;
global.Select = class extends PureComponent {
    static displayName = 'Select';

    render() {
        const props = this.props;
        return E2E ? (
            <div>
                <input
                  type="text"
                  ref={input => this.input = input}
                  value={props.value && props.value.value}
                  onChange={e => props.onChange({ value: Utils.safeParseEventValue(e) })}
                  id={props.id} data-test={props['data-test']}
                />
                {
                    this.props.options && this.props.options.map((option, index) => (
                        <a
                          onClick={() => props.onChange(option)}
                          data-test={`${props['data-test']}-option-${index}`}
                        >
                          .
                        </a>
                    ))
                }
            </div>
        ) : (
            <Select className="react-select" classNamePrefix="react-select" {...props}/>
        );
    }
};
