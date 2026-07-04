import React from 'react';
import { useReconciliationStore } from '../../store/reconciliationStore';
import { PipelineStep } from './PipelineStep';

export const PipelineStepper: React.FC = () => {
  const { pipelineStage, jobStatus } = useReconciliationStore();

  const stages = [
    "CRM Ingestion",
    "Reports Loading",
    "Validation Engine",
    "Matching Engine",
    "Report Export"
  ];

  const getStageStatus = (index: number) => {
    if (jobStatus === 'done') {
      return 'done';
    }
    
    if (jobStatus === 'error') {
      if (index === pipelineStage) return 'error';
      return index < pipelineStage ? 'done' : 'pending';
    }
    
    if (jobStatus === 'running') {
      if (index < pipelineStage) return 'done';
      if (index === pipelineStage) return 'in-progress';
      return 'pending';
    }
    
    if (jobStatus === 'pending') {
      if (index === 0) return 'in-progress';
      return 'pending';
    }
    
    return 'pending';
  };

  return (
    <div className="pipeline-stepper-container">
      {stages.map((label, index) => (
        <PipelineStep 
          key={index} 
          label={label} 
          status={getStageStatus(index)} 
        />
      ))}
    </div>
  );
};
