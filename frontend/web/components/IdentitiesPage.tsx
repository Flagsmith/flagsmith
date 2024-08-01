import React, { FC, useEffect, useState } from 'react';
import axios from 'axios';
import { Bar } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js';
import PageTitle from './PageTitle';
import '../App.css'; // Adjust the path if necessary

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

type IdentitiesPageType = {
  match: {
    params: {
      environmentId: string;
      projectId: string;
    };
  };
};

const IdentitiesPage: FC<IdentitiesPageType> = ({
  match: {
    params: { environmentId, projectId },
  },
}) => {
  const [identitiesData, setIdentitiesData] = useState<{ identities: number; day: string }[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get(
          `https://api.flagsmith.com/api/v1/organisations/16782/usage-data/`,
          {
            headers: {
              'Authorization': 'Api-Key 8HO39EPu.yAygI95OgZDV6agJnG1EtSALN6QNfO6H',
              'Content-Type': 'application/json'
            }
          }
        );

        const data = response.data;
        const filteredData = data.map((item: any) => ({
          identities: item.identities,
          day: item.day,
        }));

        setIdentitiesData(filteredData);
      } catch (error) {
        console.error('Error fetching identities data:', error);
      }
    };

    fetchData();
  }, [environmentId]);

  const chartData = {
    labels: identitiesData.map(item => item.day),
    datasets: [
      {
        label: 'Identities',
        data: identitiesData.map(item => item.identities),
        backgroundColor: 'rgba(75, 192, 192, 0.6)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className='app-container'>
      <PageTitle title='Identities Data'>
        View the number of identities per day.
      </PageTitle>
      <div className='chart-container'>
        <Bar data={chartData} options={{ responsive: true, plugins: { legend: { position: 'top' }, title: { display: true, text: 'Identities per Day' } } }} />
      </div>
    </div>
  );
};

export default IdentitiesPage;