import React from 'react';
import { ScrollArea } from './ui/scroll-area';

const AlignmentViewer = ({ alignment }) => {
  if (!alignment) {
    return <div className="text-sm text-slate-500">No alignment data available</div>;
  }

  const colorNucleotide = (nucleotide) => {
    const colors = {
      'A': 'nucleotide-a',
      'T': 'nucleotide-t',
      'C': 'nucleotide-c',
      'G': 'nucleotide-g'
    };
    return colors[nucleotide] || '';
  };

  return (
    <div data-testid="alignment-viewer" className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-[#F4F3EF] p-3 rounded-lg border border-[#E5E4DE]">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Score</p>
          <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            {alignment.score?.toFixed(1) || 'N/A'}
          </p>
        </div>
        <div className="bg-[#F4F3EF] p-3 rounded-lg border border-[#E5E4DE]">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Matches</p>
          <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            {alignment.matches || 0}
          </p>
        </div>
        <div className="bg-[#F4F3EF] p-3 rounded-lg border border-[#E5E4DE]">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Mismatches</p>
          <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            {alignment.mismatches || 0}
          </p>
        </div>
        <div className="bg-[#F4F3EF] p-3 rounded-lg border border-[#E5E4DE]">
          <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">Gaps</p>
          <p className="text-lg font-semibold text-slate-900" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            {alignment.gaps || 0}
          </p>
        </div>
      </div>

      <div className="bg-[#F4F3EF] border border-[#E5E4DE] rounded-lg p-4">
        <h4 className="text-sm font-bold uppercase tracking-wider text-slate-600 mb-3">Sequence Alignment</h4>
        <ScrollArea className="h-[400px] w-full">
          <div className="sequence-viewer" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
            {alignment.alignment_visual ? alignment.alignment_visual.map((chunk, index) => (
              <div key={index} className="mb-6">
                <div className="flex gap-3">
                  <span className="text-slate-400 w-12 text-right">{chunk.position}</span>
                  <div className="flex-1">
                    <div className="sequence-line">
                      <span className="text-slate-500 mr-2">Ref:</span>
                      {chunk.reference.split('').map((char, i) => (
                        <span key={i} className={colorNucleotide(char)}>{char}</span>
                      ))}
                    </div>
                    <div className="sequence-line text-slate-400">
                      <span className="mr-2 invisible">xxx</span>
                      {chunk.match_line}
                    </div>
                    <div className="sequence-line">
                      <span className="text-slate-500 mr-2">Qry:</span>
                      {chunk.query.split('').map((char, i) => (
                        <span key={i} className={char !== chunk.reference[i] && char !== '-' ? 'mutation-highlight ' + colorNucleotide(char) : colorNucleotide(char)}>
                          {char}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )) : (
              <div className="space-y-3 text-sm">
                <div className="sequence-line break-all">
                  <span className="text-slate-500 mr-2">Ref:</span>
                  {alignment.aligned_reference || 'N/A'}
                </div>
                <div className="sequence-line break-all">
                  <span className="text-slate-500 mr-2">Qry:</span>
                  {alignment.aligned_query || 'N/A'}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      <div className="text-xs text-slate-500">
        <p>Legend: | = match, * = mismatch, (space) = gap</p>
      </div>
    </div>
  );
};

export default AlignmentViewer;
