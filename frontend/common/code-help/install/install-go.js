import Utils from '../../utils/utils';

module.exports = ({ NPM_NODE_CLIENT, URL_CLIENT }) => `go get github.com/flagsmith/flagsmith-go-client

import (
  "github.com/flagsmith/flagsmith-go-client"
)
`;
