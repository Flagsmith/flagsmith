import React, { FC } from 'react';
import PageTitle from './PageTitle';
import { Bar } from 'react-chartjs-2';

type SDKEventType = {
  match: {
    params: {
      environmentId: string;
      projectId: string;
    };
  };
};

const SDKEventsPage: FC<SDKEventType> = ({
  match: {
    params: { environmentId, projectId },
  },
}) => {
  const data = {
    labels: ['Jul 1', 'Jul 2', 'Jul 3', 'Jul 4', 'Jul 5', 'jul 6', 'jul 7'],
    datasets: [
      {
        label: 'Number of Requests',
        data: [12, 19, 3, 5],
        backgroundColor: [
          'rgba(255, 99, 132, 0.2)',
          'rgba(54, 162, 235, 0.2)',
          'rgba(255, 206, 86, 0.2)',
          'rgba(75, 192, 192, 0.2)',
        ],
        borderColor: [
          'rgba(255, 99, 132, 1)',
          'rgba(54, 162, 235, 1)',
          'rgba(255, 206, 86, 1)',
          'rgba(75, 192, 192, 1)',
        ],
        borderWidth: 1,
      },
    ],
  };

  const options = {
    scales: {
      y: {
        beginAtZero: true,
      },
    },
  };

  return (
    <div className='app-container container'>
      <PageTitle title='SDK Request'>
        View the number of requests from the SDK.
      </PageTitle>
      <div className='chart-container'>
        <Bar data={data} options={options} />
      </div>
    </div>
  );
};

export default SDKEventsPage;