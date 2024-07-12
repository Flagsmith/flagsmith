import React, { FC } from 'react';
import PageTitle from './PageTitle';
import { Line } from 'react-chartjs-2';
import '../App.css';  // Adjust the path if necessary

type SDKEventType = {
  match: {
    params: {
      environmentId: string;
      projectId: string;
    };
  };
};

const EventAndRequestPage: FC<SDKEventType> = ({
  match: {
    params: { environmentId, projectId },
  },
}) => {
  const successfulRequestsData = {
    labels: ['Jul 1', 'Jul 2', 'Jul 3', 'Jul 4', 'Jul 5', 'Jul 6', 'Jul 7'],
    datasets: [
      {
        label: 'Successful Requests',
        data: [12, 19, 3, 5, 2, 3, 7],
        backgroundColor: 'rgba(255, 99, 132, 0.2)',
        borderColor: 'rgba(255, 99, 132, 1)',
        borderWidth: 1,
        fill: false,
      },
    ],
  };

  const eventAndIdentifyCountsData = {
    labels: ['Jul 1', 'Jul 2', 'Jul 3', 'Jul 4', 'Jul 5', 'Jul 6', 'Jul 7'],
    datasets: [
      {
        label: 'Event and Identify Counts',
        data: [22, 29, 15, 20, 30, 25, 18],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1,
        fill: false,
      },
    ],
  };

  const errorRequestsData = {
    labels: ['Jul 1', 'Jul 2', 'Jul 3', 'Jul 4', 'Jul 5', 'Jul 6', 'Jul 7'],
    datasets: [
      {
        label: 'Error Requests',
        data: [2, 3, 1, 4, 6, 2, 3],
        backgroundColor: 'rgba(75, 192, 192, 0.2)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        fill: false,
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
    <div className='app-container'>
      <PageTitle title='SDK Request'>
        View the number of requests from the SDK.
      </PageTitle>
      <div className='charts-container'>
        <div className='chart-container'>
          <Line data={successfulRequestsData} options={options} />
        </div>
        <div className='chart-container'>
          <Line data={eventAndIdentifyCountsData} options={options} />
        </div>
        <div className='chart-container'>
          <Line data={errorRequestsData} options={options} />
        </div>
      </div>
    </div>
  );
};

export default EventAndRequestPage;
