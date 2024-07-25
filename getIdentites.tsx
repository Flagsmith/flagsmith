import axios from 'axios';

const apiKey = 'cH6prysA.mZ3RZon2oiiEuDA9JamZTFXVYFt7dERa';
const baseUrl = 'https://api.flagsmith.com/api/v1';

const api = axios.create({
    baseURL: baseUrl,
    headers: {
      Authorization: `Api-Key ${apiKey}`,
      'Content-Type': 'application/json',
    },
  });

  const fetchProjects = async () => {
    try {
      const response = await api.get('/projects/');
      return response.data;
    } catch (error) {
      console.error('Error fetching projects:', error);
      throw error;
    }
  };

  const fetchEnvironments = async (projectId: number) => {
    try {
      const response = await api.get(`/projects/${projectId}/environments/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching environments for project ${projectId}:`, error);
      throw error;
    }
  };

  const fetchIdentities = async (environmentApiKey: string) => {
    try {
      const response = await api.get(`/environments/${environmentApiKey}/identities/`);
      return response.data;
    } catch (error) {
      console.error(`Error fetching identities for environment ${environmentApiKey}:`, error);
      throw error;
    }
  };

  const main = async () => {
    try {
      const projects = await fetchProjects();
      console.log('Projects:', projects.id);
  
      if (projects.length > 0) {
        const projectId = projects[0].id;
        const environments = await fetchEnvironments(projectId);
        console.log('Environments:', environments);
  
        if (environments.length > 0) {
          const environmentApiKey = environments[0].api_key;
          const identities = await fetchIdentities(environmentApiKey);
          console.log('Identities:', identities);
        } else {
          console.log('No environments found.');
        }
      } else {
        console.log('No projects found.');
      }
    } catch (error) {
      console.error('Error:', error);
    }
  };
  
  main();