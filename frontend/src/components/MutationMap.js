import React, { useState } from 'react';
import { MapPin } from '@phosphor-icons/react';

const MutationMap = ({ mutations, sequenceLength }) => {
  const [hoveredMutation, setHoveredMutation] = useState(null);

  if (!mutations || mutations.length === 0) {
    return (
      <div className="mutation-map flex items-center justify-center">
        <p className="text-sm text-slate-500">No mutations to display</p>
      </div>
    );
  }

  return (
    <div data-testid="mutation-map" className="space-y-3">
      <div className="mutation-map relative">
        {mutations.map((mutation, index) => {
          const position = (mutation.position / sequenceLength) * 100;
          const colors = {
            substitution: '#D19B53',
            deletion: '#C16353',
            insertion: '#52745E'
          };
          
          return (
            <div
              key={index}
              className="mutation-marker"
              style={{
                left: `${position}%`,
                background: colors[mutation.type] || '#8A948F'
              }}
              onMouseEnter={() => setHoveredMutation(mutation)}
              onMouseLeave={() => setHoveredMutation(null)}
              data-testid={`mutation-marker-${index}`}
            />
          );
        })}
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
        <span>1</span>
        <span>{Math.floor(sequenceLength / 2)}</span>
        <span>{sequenceLength}</span>
      </div>

      {hoveredMutation && (
        <div className="bg-[#F4F3EF] border border-[#E5E4DE] rounded-lg p-3">
          <div className="flex items-start gap-2">
            <MapPin size={16} weight="fill" className="text-[#52745E] mt-0.5" />
            <div className="text-sm">
              <p className="font-medium text-slate-900">
                Position {hoveredMutation.position}: {hoveredMutation.type.charAt(0).toUpperCase() + hoveredMutation.type.slice(1)}
              </p>
              {hoveredMutation.type === 'substitution' && (
                <p className="text-slate-600 font-mono text-xs mt-1">
                  {hoveredMutation.reference_base} → {hoveredMutation.alternate_base}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ background: '#D19B53' }} />
          <span className="text-slate-600">Substitution</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ background: '#C16353' }} />
          <span className="text-slate-600">Deletion</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded" style={{ background: '#52745E' }} />
          <span className="text-slate-600">Insertion</span>
        </div>
      </div>
    </div>
  );
};

export default MutationMap;