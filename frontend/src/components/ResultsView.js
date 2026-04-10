import React, { useState } from 'react';
import {
  CheckCircle,
  Warning,
  XCircle,
  Info,
  Dna,
  ChartBar,
  Sparkle,
  Scroll,
  Target,
} from '@phosphor-icons/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { Separator } from './ui/separator';
import AlignmentViewer from './AlignmentViewer';
import MutationMap from './MutationMap';
import EvidenceList from './EvidenceList';
import AIExplanation from './AIExplanation';

const ResultsView = ({ results }) => {
  const [activeTab, setActiveTab] = useState('overview');

  const classification = results?.classification;
  const alignment = results?.alignment;
  const evidence = results?.evidence;
  const mutationList = Array.isArray(results?.mutations) ? results.mutations : [];
  const summary = classification?.summary || {};

  const pathogenicCount = summary['Pathogenic'] || 0;
  const potentiallyPathogenicCount = summary['Potentially Pathogenic'] || 0;
  const uncertainCount = summary['Uncertain'] || 0;
  const benignCount = summary['Benign'] || 0;

  const classifiedMutations = classification?.classified_mutations || [];
  const validationErrors = results?.validation?.errors || [];
  const allWarnings = results?.warnings || [];
  const allErrors = results?.errors || [];

  const getRiskBadge = (riskLevel) => {
    const styles = {
      HIGH: 'risk-high',
      MODERATE: 'risk-moderate',
      LOW: 'risk-low',
    };
    return (
      <Badge
        data-testid="risk-badge"
        className={`${styles[riskLevel] || 'risk-moderate'} px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider`}
      >
        {riskLevel || 'UNKNOWN'} RISK
      </Badge>
    );
  };

  const getClassificationIcon = (classificationValue) => {
    if (
      classificationValue === 'Pathogenic' ||
      classificationValue === 'Potentially Pathogenic'
    ) {
      return <Warning size={20} weight="fill" className="text-[#C16353]" />;
    }
    if (classificationValue === 'Benign') {
      return <CheckCircle size={20} weight="fill" className="text-[#52745E]" />;
    }
    return <Info size={20} weight="fill" className="text-[#D19B53]" />;
  };

  if (!results) {
    return null;
  }

  if (results.status === 'failed') {
    return (
      <Alert data-testid="validation-error" className="border-[#C16353] bg-[#F5E6E3]">
        <XCircle size={20} weight="fill" className="text-[#C16353]" />
        <AlertDescription className="text-[#C16353]">
          <strong>Analysis Failed:</strong>{' '}
          {[...validationErrors, ...allErrors].filter(Boolean).join(', ') || 'Unknown error'}
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {allWarnings.length > 0 && (
        <Alert className="border-[#D19B53] bg-[#FEF3E8]">
          <Info size={20} className="text-[#D19B53]" />
          <AlertDescription className="text-slate-700">
            {allWarnings.join(' | ')}
          </AlertDescription>
        </Alert>
      )}

      <Card data-testid="overview-card" className="border border-[#E5E4DE] shadow-sm">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              {getClassificationIcon(classification?.overall_classification)}
              <div>
                <CardTitle className="text-2xl" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                  {classification?.overall_classification || 'Analysis Complete'}
                </CardTitle>
                <CardDescription className="mt-1">
                  Analysis ID: {results.analysis_id?.slice(0, 8)}
                </CardDescription>
              </div>
            </div>
            {classification && getRiskBadge(classification.risk_level)}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-slate-700 leading-relaxed">
            {classification?.rationale || 'Analysis finished successfully.'}
          </p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4">
            <div className="space-y-1">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Gene</p>
              <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {results.gene}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Mutations</p>
              <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {mutationList.length}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Identity</p>
              <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {alignment?.identity_percent != null ? `${alignment.identity_percent.toFixed(1)}%` : 'N/A'}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-xs font-bold uppercase tracking-wider text-slate-500">Evidence</p>
              <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                {evidence?.total_evidence || 0}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card data-testid="results-tabs" className="border border-[#E5E4DE] shadow-sm">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <CardHeader className="pb-0">
            <TabsList className="w-full justify-start border-b border-[#E5E4DE] bg-transparent p-0 h-auto rounded-none">
              <TabsTrigger data-testid="tab-overview" value="overview" className="tabs-trigger rounded-none px-4 py-3">
                <ChartBar size={18} weight="duotone" className="mr-2" />Overview
              </TabsTrigger>
              <TabsTrigger data-testid="tab-mutations" value="mutations" className="tabs-trigger rounded-none px-4 py-3">
                <Target size={18} weight="duotone" className="mr-2" />Mutations
              </TabsTrigger>
              <TabsTrigger data-testid="tab-alignment" value="alignment" className="tabs-trigger rounded-none px-4 py-3">
                <Dna size={18} weight="duotone" className="mr-2" />Alignment
              </TabsTrigger>
              <TabsTrigger data-testid="tab-evidence" value="evidence" className="tabs-trigger rounded-none px-4 py-3">
                <Scroll size={18} weight="duotone" className="mr-2" />Evidence
              </TabsTrigger>
              <TabsTrigger data-testid="tab-explanation" value="explanation" className="tabs-trigger rounded-none px-4 py-3">
                <Sparkle size={18} weight="duotone" className="mr-2" />Interpretation
              </TabsTrigger>
            </TabsList>
          </CardHeader>

          <CardContent className="pt-6">
            <TabsContent value="overview" className="mt-0 space-y-6">
              <div>
                <h3 className="text-lg font-medium mb-3" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                  Mutation Map
                </h3>
                <MutationMap
                  mutations={mutationList}
                  sequenceLength={alignment?.reference_length || results?.validation?.length || 1}
                />
              </div>
              <Separator className="bg-[#E5E4DE]" />
              <div>
                <h3 className="text-lg font-medium mb-3" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                  Classification Summary
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  <div className="bg-[#F5E6E3] p-3 rounded-lg border border-[#EACCC8]">
                    <p className="text-xs font-bold uppercase tracking-wider text-[#C16353] mb-1">Pathogenic</p>
                    <p className="text-2xl font-semibold text-[#C16353]" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{pathogenicCount}</p>
                  </div>
                  <div className="bg-[#FEF3E8] p-3 rounded-lg border border-[#F5E4CC]">
                    <p className="text-xs font-bold uppercase tracking-wider text-[#D19B53] mb-1">Potential</p>
                    <p className="text-2xl font-semibold text-[#D19B53]" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{potentiallyPathogenicCount}</p>
                  </div>
                  <div className="bg-[#F4F3EF] p-3 rounded-lg border border-[#E5E4DE]">
                    <p className="text-xs font-bold uppercase tracking-wider text-[#8A948F] mb-1">Uncertain</p>
                    <p className="text-2xl font-semibold text-[#8A948F]" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{uncertainCount}</p>
                  </div>
                  <div className="bg-[#E6EBE8] p-3 rounded-lg border border-[#CCD7D1]">
                    <p className="text-xs font-bold uppercase tracking-wider text-[#52745E] mb-1">Benign</p>
                    <p className="text-2xl font-semibold text-[#52745E]" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{benignCount}</p>
                  </div>
                </div>
              </div>
              <Separator className="bg-[#E5E4DE]" />
              <div>
                <h3 className="text-lg font-medium mb-3" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                  Recommendation
                </h3>
                <Alert className="border-[#52745E] bg-[#E6EBE8]">
                  <Info size={20} className="text-[#52745E]" />
                  <AlertDescription className="text-slate-700">
                    {classification?.recommendation || 'No recommendation available.'}
                  </AlertDescription>
                </Alert>
              </div>
            </TabsContent>

            <TabsContent value="mutations" className="mt-0 space-y-4">
              {classifiedMutations.length > 0 ? (
                classifiedMutations.map((mutation, index) => (
                  <Card key={index} data-testid={`mutation-${index}`} className="border border-[#E5E4DE]">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-base" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                          Mutation {index + 1}
                        </CardTitle>
                        <Badge className={mutation.risk_level === 'HIGH' ? 'risk-high' : mutation.risk_level === 'MODERATE' ? 'risk-moderate' : 'risk-low'}>
                          {mutation.final_classification}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3 text-sm">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Position</p>
                          <p className="font-mono text-slate-900">{mutation.position}</p>
                        </div>
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Effect</p>
                          <p className="font-mono text-slate-900">{mutation.effect}</p>
                        </div>
                      </div>
                      {mutation.protein_change && (
                        <div>
                          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Protein Change</p>
                          <p className="font-mono text-slate-900">{mutation.protein_change}</p>
                        </div>
                      )}
                      <div>
                        <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Rationale</p>
                        <p className="text-slate-700">{mutation.rationale}</p>
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <Alert className="border-[#52745E] bg-[#E6EBE8]">
                  <CheckCircle size={20} className="text-[#52745E]" />
                  <AlertDescription className="text-slate-700">
                    No classified mutations available.
                  </AlertDescription>
                </Alert>
              )}
            </TabsContent>

            <TabsContent value="alignment" className="mt-0">
              <AlignmentViewer alignment={alignment} />
            </TabsContent>
            <TabsContent value="evidence" className="mt-0">
              <EvidenceList evidence={evidence} />
            </TabsContent>
            <TabsContent value="explanation" className="mt-0">
              <AIExplanation
                classification={classification}
                evidence={evidence}
                gene={results.gene}
                mutationCount={mutationList.length}
              />
            </TabsContent>
          </CardContent>
        </Tabs>
      </Card>
    </div>
  );
};

export default ResultsView;
