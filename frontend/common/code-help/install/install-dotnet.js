import Utils from '../../utils/utils';

module.exports = ({ NPM_NODE_CLIENT, URL_CLIENT }) => `// Package Manager
PM> Install-Package BulletTrain -Version 2.1.4

// .NET CLI
dotnet add package BulletTrain --version 2.1.4

// PackageReference
${Utils.escapeHtml('<PackageReference Include="BulletTrain" Version="2.1.4" />')}

// Paket CLI
paket add BulletTrain --version 2.1.4
`;
