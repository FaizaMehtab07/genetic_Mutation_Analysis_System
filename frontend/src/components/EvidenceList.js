import React from 'react';
import { Database, CheckCircle, Warning, Question } from '@phosphor-icons/react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';

const EvidenceList = ({ evidence }) => {
  if (!evidence || !evidence.evidence || evidence.evidence.length === 0) {
    return (
      <div data-testid="no-evidence" className="text-center py-12">
        <Database size={48} weight="duotone" className="mx-auto mb-3 text-slate-400" />
        <p className="text-sm text-slate-600">No ClinVar evidence found for detected mutations.</p>
        <p className="text-xs text-slate-500 mt-1">This may indicate a novel variant.</p>
      </div>
    );
  }

  const getSignificanceIcon = (significance) => {
    if (significance.toLowerCase().includes('pathogenic')) {
      return <Warning size={16} weight="fill" className="text-[#C16353]" />;
    } else if (significance.toLowerCase().includes('benign')) {
      return <CheckCircle size={16} weight="fill" className="text-[#52745E]" />;
    }
    return <Question size={16} weight="fill" className="text-[#D19B53]" />;
  };

  const getSignificanceBadge = (significance) => {
    if (significance.toLowerCase().includes('pathogenic')) {
      return <Badge className="risk-high text-xs">{significance}</Badge>;
    } else if (significance.toLowerCase().includes('benign')) {
      return <Badge className="risk-low text-xs">{significance}</Badge>;
    }
    return <Badge className="risk-moderate text-xs">{significance}</Badge>;
  };

  return (
    <div data-testid="evidence-list" className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Database size={20} weight="duotone" className="text-[#52745E]" />
          <h4 className="text-sm font-bold uppercase tracking-wider text-slate-600">
            ClinVar Evidence ({evidence.total_evidence || 0} records)
          </h4>
        </div>
      </div>

      <ScrollArea className="h-[500px] pr-4">
        <div className="space-y-3">
          {evidence.evidence.map((record, index) => (
            <Card key={index} data-testid={`evidence-${index}`} className="evidence-card">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-2">
                    {getSignificanceIcon(record.clinical_significance)}
                    <div>
                      <CardTitle className="text-sm" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                        {record.mutation_id || 'Unknown ID'}
                      </CardTitle>
                      <p className="text-xs text-slate-500 mt-1">
                        Position {record.position} • {record.mutation_type}
                      </p>
                    </div>
                  </div>
                  {getSignificanceBadge(record.clinical_significance)}
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                {record.protein_change && record.protein_change !== 'N/A' && (
                  <div>
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Protein Change</p>
                    <p className="font-mono text-slate-900">{record.protein_change}</p>
                  </div>
                )}

                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Associated Condition</p>
                  <p className="text-slate-700">{record.condition || 'Not specified'}</p>
                </div>

                <div>
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Review Status</p>
                  <p className="text-slate-700">{record.review_status || 'Not specified'}</p>
                </div>

                {record.evidence_summary && (
                  <div className="pt-2 border-t border-[#E5E4DE]">
                    <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Evidence Summary</p>
                    <p className="text-slate-700 leading-relaxed">{record.evidence_summary}</p>
                  </div>
                )}

                {record.match_quality && (
                  <div className="pt-2">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-[#F4F3EF] rounded-full h-1.5">
                        <div 
                          className="bg-[#52745E] h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${record.match_quality * 100}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500 font-mono">
                        {(record.match_quality * 100).toFixed(0)}% match
                      </span>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default EvidenceList;