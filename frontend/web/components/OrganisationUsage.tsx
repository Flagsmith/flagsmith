import Utils from 'common/utils/utils';
import React, { FC } from 'react';
import { Bar, Tooltip as _Tooltip, BarChart, ResponsiveContainer, XAxis, YAxis } from 'recharts';
import { useGetOrganisationUsageQuery } from '../../common/services/useOrganisationUsage';

type OrganisationUsageType = {
  organisationId: string
}
type LegendItemType = {
  title: string
  value: number
  colour?: string
}


const LegendItem: FC<LegendItemType> = ({title, value, colour}) => {
  if(!value) {
    return null
  }
  return (
    <div className="col-md-3 text-center mb-4">
      <h1>{Utils.numberWithCommas(value)}</h1>
      <Row className="justify-content-center">
        <span style={{backgroundColor:colour, display:"inline-block", width:20, height:20}}/>
        <span className="text-muted ml-2">
          {title}
        </span>
      </Row>

    </div>
  );
};

const OrganisationUsage: FC<OrganisationUsageType> = ({organisationId}) => {
  const {data} = useGetOrganisationUsageQuery({organisationId})
  const colours = [
    "#6633ff",
    "#00a696",
    "#f18e7f",
    "#F6D46E"
  ]

    return data?.totals?  (
      <div className="mt-4">
        <div className="row">
          <LegendItem colour={colours[0]} value={data.totals.flags} title="Flags"/>
          <LegendItem colour={colours[1]} value={data.totals.traits} title="Traits"/>
          <LegendItem colour={colours[2]} value={data.totals.environmentDocument} title="Environment Document"/>
          <LegendItem value={data.totals.total} title="Total API Calls"/>
        </div>
        <ResponsiveContainer height={400} width="100%">
          <BarChart data={data.events_list}>
            <XAxis allowDataOverflow={false} dataKey="name" />
            <YAxis allowDataOverflow={false} />
            <_Tooltip />
            <Bar dataKey="Flags" stackId="a" fill={colours[0]} />
            <Bar dataKey="Identities" stackId="a" fill={colours[1]} />
            <Bar dataKey="Traits" stackId="a" fill={colours[2]} />
            <Bar
              name="Environment Document" dataKey="Environment-document" stackId="a"
              fill={colours[3]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    ): <div className="text-center"><Loader/></div> ;
};

export default OrganisationUsage;
