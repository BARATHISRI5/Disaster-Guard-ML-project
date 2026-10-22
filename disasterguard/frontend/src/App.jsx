import React, { useState, useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import TopBar from './components/TopBar';
import Sidebar from './components/Sidebar';
import RiskMap from './components/RiskMap';
import AlertPanel from './components/AlertPanel';
import PredictionChart from './components/PredictionChart';
import DamageViewer from './components/DamageViewer';
import CrowdReport from './components/CrowdReport';
import LoadingSkeleton from './components/LoadingSkeleton';
import {
  useRiskMap, useDistricts, usePrediction, useTimeSeries,
  useDamageAssessment, useEvacuationRoutes, useCrowdReports,
  useAlertHistory, useTriggerAlert,
} from './api/disasterApi';

// Embedded minimal TN GeoJSON (simplified district boundaries)
import tnGeoJson from './tn_districts_data.js';

export default function App() {
  const queryClient = useQueryClient();
  const [selectedDistrict, setSelectedDistrict] = useState(null);
  const [timeWindow, setTimeWindow] = useState('72h');
  const [disasterType, setDisasterType] = useState('all');
  const [showEvacuation, setShowEvacuation] = useState(false);
  const [showCrowdReports, setShowCrowdReports] = useState(false);
  const [rightPanelTab, setRightPanelTab] = useState('alerts');
  const [alertResult, setAlertResult] = useState(null);

  // API hooks
  const { data: riskMap, isLoading: riskLoading } = useRiskMap();
  const { data: districtsData, isLoading: districtsLoading } = useDistricts();
  const { data: prediction } = usePrediction(selectedDistrict);
  const { data: timeSeries } = useTimeSeries(selectedDistrict);
  const { data: damageData } = useDamageAssessment(selectedDistrict);
  const { data: evacuationData } = useEvacuationRoutes(selectedDistrict);
  const { data: crowdReportsData } = useCrowdReports();
  const { data: alertHistory } = useAlertHistory();
  const triggerAlertMutation = useTriggerAlert();

  // Calculate overall risk
  const overallRisk = riskMap?.features
    ? Math.max(...riskMap.features.map((f) => f.properties.risk_score || 0))
    : 0;

  const handleTriggerAlert = async (alertData) => {
    try {
      const result = await triggerAlertMutation.mutateAsync(alertData);
      setAlertResult(result);
      // Refresh alert history
      queryClient.invalidateQueries({ queryKey: ['alertHistory'] });
      return result;
    } catch (err) {
      console.error('Alert trigger failed:', err);
      throw err;
    }
  };

  return (
    <div className="app-layout">
      <TopBar
        overallRisk={overallRisk}
        lastUpdated={riskMap?.features?.[0]?.properties?.last_updated}
        alerts={alertHistory?.alerts}
      />

      <Sidebar
        districts={districtsData?.districts || []}
        selectedDistrict={selectedDistrict}
        onSelectDistrict={setSelectedDistrict}
        timeWindow={timeWindow}
        onTimeWindowChange={setTimeWindow}
        disasterType={disasterType}
        onDisasterTypeChange={setDisasterType}
        isLoading={districtsLoading}
      />

      <RiskMap
        riskData={riskMap}
        geoJsonData={tnGeoJson}
        selectedDistrict={selectedDistrict}
        onSelectDistrict={setSelectedDistrict}
        showEvacuation={showEvacuation}
        onToggleEvacuation={() => setShowEvacuation(!showEvacuation)}
        showCrowdReports={showCrowdReports}
        onToggleCrowdReports={() => setShowCrowdReports(!showCrowdReports)}
        evacuationData={evacuationData}
        crowdReports={crowdReportsData?.reports}
        timeWindow={timeWindow}
      />

      <div className="alert-panel">
        <div className="panel-header">
          <span>📡 Intelligence Feed</span>
        </div>

        {/* Tabs */}
        <div className="panel-tabs">
          {[
            { key: 'alerts', label: '🚨 Alerts' },
            { key: 'charts', label: '📈 Data' },
            { key: 'damage', label: '🛰️ Damage' },
            { key: 'crowd', label: '📍 Report' },
          ].map((tab) => (
            <button
              key={tab.key}
              className={`panel-tab ${rightPanelTab === tab.key ? 'active' : ''}`}
              onClick={() => setRightPanelTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        {rightPanelTab === 'alerts' && (
          <AlertPanel
            alerts={alertHistory?.alerts || []}
            prediction={prediction}
            onTriggerAlert={handleTriggerAlert}
            selectedDistrict={selectedDistrict}
            alertResult={alertResult}
          />
        )}

        {rightPanelTab === 'charts' && (
          <PredictionChart
            timeSeriesData={timeSeries}
            district={selectedDistrict}
          />
        )}

        {rightPanelTab === 'damage' && (
          <DamageViewer
            damageData={damageData}
            district={selectedDistrict}
          />
        )}

        {rightPanelTab === 'crowd' && (
          <CrowdReport />
        )}
      </div>
    </div>
  );
}
