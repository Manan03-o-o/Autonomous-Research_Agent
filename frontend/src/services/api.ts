import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export interface ResearchJobCreate {
  user_question: string;
  research_depth?: string;
}

export const startResearch = async (data: ResearchJobCreate) => {
  const response = await axios.post(`${API_URL}/research`, data);
  return response.data;
};

export const getResearchStreamUrl = (jobId: string) => {
  return `${API_URL}/research/${jobId}/stream`;
};

// ... other endpoints for later
