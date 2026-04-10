import React from 'react';
import { Sparkle, Info, Brain } from '@phosphor-icons/react';
import { Card, CardContent } from './ui/card';
import { Alert, AlertDescription } from './ui/alert';
import { ScrollArea } from './ui/scroll-area';

const AIExplanation = ({ classification, evidence, gene, mutationCount }) => {
  const evidenceCount = evidence?.total_evidence || 0;

  const explanation = classification
    ? [
        `Gene analyzed: ${gene || 'Unknown'}.`,
        `Overall classification: ${classification.overall_classification || 'Unknown'}.`,
        `Risk level: ${classification.risk_level || 'Unknown'}.`,
        classification.rationale ? `Rationale: ${classification.rationale}` : null,
        classification.recommendation
          ? `Recommendation: ${classification.recommendation}`
          : null,
        `Detected mutations: ${mutationCount}.`,
        `Matched ClinVar evidence records: ${evidenceCount}.`,
      ]
        .filter(Boolean)
        .join('\n\n')
    : null;

  if (!explanation) {
    return (
      <div className="text-center py-12">
        <Brain size={48} weight="duotone" className="mx-auto mb-3 text-slate-400" />
        <p className="text-sm text-slate-600">Interpretation not available.</p>
      </div>
    );
  }

  return (
    <div data-testid="ai-explanation" className="space-y-4">
      <div className="flex items-start gap-3">
        <div className="p-2 bg-[#E6EBE8] rounded-lg">
          <Sparkle size={24} weight="duotone" className="text-[#52745E]" />
        </div>
        <div>
          <h3 className="text-lg font-medium" style={{ fontFamily: 'Work Sans, sans-serif' }}>
            Clinical Interpretation
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Rule-based summary from the current analysis pipeline
          </p>
        </div>
      </div>

      <Alert className="border-[#E5E4DE] bg-[#F4F3EF]">
        <Info size={16} className="text-slate-600" />
        <AlertDescription className="text-xs text-slate-600">
          This summary is derived from the backend classification and evidence results.
        </AlertDescription>
      </Alert>

      <Card className="border border-[#E5E4DE] shadow-sm">
        <CardContent className="pt-6">
          <ScrollArea className="h-[420px] pr-4">
            <div
              className="text-slate-700 leading-relaxed whitespace-pre-wrap"
              style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}
            >
              {explanation}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  );
};

export default AIExplanation;
