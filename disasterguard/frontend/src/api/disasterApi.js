import axios from 'axios';
import { useQuery, useMutation } from '@tanstack/react-query';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// ---- API Functions ----

export const fetchRiskMap = async () => {
  const { data } = await api.get('/risk-map');
  return data;
};

export const fetchPrediction = async (district) => {
  const { data } = await api.get('/prediction', { params: { district } });
  return data;
};

export const fetchDistricts = async () => {
  const { data } = await api.get('/districts');
  return data;
};

export const fetchTimeSeries = async (district, days = 7) => {
  const { data } = await api.get('/time-series', { params: { district, days } });
  return data;
};

export const fetchDamageAssessment = async (district, date) => {
  const { data } = await api.get('/damage-assessment', { params: { district, date } });
  return data;
};

export const fetchEvacuationRoutes = async (district) => {
  const { data } = await api.get('/evacuation-routes', { params: { district } });
  return data;
};

export const fetchCrowdReports = async () => {
  const { data } = await api.get('/crowd-reports');
  return data;
};

export const fetchAlertHistory = async () => {
  const { data } = await api.get('/alerts/history');
  return data;
};

export const triggerAlert = async (alertData) => {
  const { data } = await api.post('/alert', alertData);
  return data;
};

export const submitCrowdReport = async (report) => {
  const { data } = await api.post('/crowd-report', report);
  return data;
};

// ---- React Query Hooks ----

export const useRiskMap = () =>
  useQuery({ queryKey: ['riskMap'], queryFn: fetchRiskMap, refetchInterval: 5 * 60 * 1000 });

export const usePrediction = (district) =>
  useQuery({ queryKey: ['prediction', district], queryFn: () => fetchPrediction(district), enabled: !!district });

export const useDistricts = () =>
  useQuery({ queryKey: ['districts'], queryFn: fetchDistricts });

export const useTimeSeries = (district, days = 7) =>
  useQuery({ queryKey: ['timeSeries', district, days], queryFn: () => fetchTimeSeries(district, days), enabled: !!district });

export const useDamageAssessment = (district) =>
  useQuery({ queryKey: ['damage', district], queryFn: () => fetchDamageAssessment(district), enabled: !!district });

export const useEvacuationRoutes = (district) =>
  useQuery({ queryKey: ['evacuation', district], queryFn: () => fetchEvacuationRoutes(district), enabled: !!district });

export const useCrowdReports = () =>
  useQuery({ queryKey: ['crowdReports'], queryFn: fetchCrowdReports });

export const useAlertHistory = () =>
  useQuery({ queryKey: ['alertHistory'], queryFn: fetchAlertHistory });

export const useTriggerAlert = () =>
  useMutation({ mutationFn: triggerAlert });

export const useSubmitCrowdReport = () =>
  useMutation({ mutationFn: submitCrowdReport });
