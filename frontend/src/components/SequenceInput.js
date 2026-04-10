import React, { useState } from 'react';
import { Upload, FileText } from '@phosphor-icons/react';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Button } from './ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';

const SequenceInput = ({ 
  sequence, 
  setSequence, 
  onFileUpload, 
  selectedGene, 
  setSelectedGene,
  availableGenes 
}) => {
  const [dragActive, setDragActive] = useState(false);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileUpload(e.dataTransfer.files[0]);
    }
  };

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      onFileUpload(e.target.files[0]);
    }
  };

  const loadSampleSequence = () => {
    // Sample TP53 sequence with a known mutation (R175H)
    const sampleWithMutation = `ATGGAGGAGCCGCAGTCAGATCCTAGCGTCGAGCCCCCTCTGAGTCAGGAA
ACATTTTCAGACCTATGGAAACTACTTCCTGAAAACAACGTTCTGTCCCCC
TTGCCGTCCCAGCAATGGATGATTTGATGCTGTCCCCGGACGATATTGAACA
ATGGTTCACTGAAGACCCAGGTCCGGATGATTGAATTGATTTCCAGACAGAG
CAGTACCTGAAATCCAATATTATACCGCTACGAAGTGCTGTCTCCGGGACCT
AGGTCAGATGTTTCCGAGAGCTGAATGAGGCCTTGGAACTCAAGGATGCCCA
GGCTGGGAAGGAGCCAGGGGGGAGCAGGGCTCACTCCAGCCACCTGAAGTCC
AAAAAGGGTCAGTCTACCTCCCGCCATAAAAAAAGAAGCCCAGTGGACCAGA
TGAACGGCCTGTGCCTATGGGCACGGTTGTGAGGCAACACTGACGTCCTGGG
CAGGGCATACCTCGCCGATTGGCGCCGACACCCTCGTCGCCATGGCGATTTC
TGGAATCTTTGGGCACAGTTTTAAAGATATTTATTTCAGATTTCAGGAAACT
AGATAAAGGCATTGCATTTAATATGGTTTCTGTCAAATCTGCTTAGGGATCT
TTTCAATAATAAATCTAAGCAATATGTGCATTTTTTATCTTTCCCCTCACTT
CAGGAACTGAGGATTTATCTTCATGCAGATTTCAGACATCTGGTGGGCAACA
GGAAATGAATCACAACAATTTTAGAATATTTTGACAAGCTCAATATGATAAA
GCTATTTGTCTCTCCTCCGGCTCTGTGCATCGTGCACAATCGATGGCCGAGC
AAACACTGACAATACGATCAGACAAGCAGTATGGGCAGCCTCTGCTCAACCT
GGCCTTTGTCTCCTGGCATTCTGGGACAGCCAAGTCTGTGACTTGCACAGGC
AGCCTCAAACGGGGAAATCAGATGTATGGTGGGCAGATCAGTACCAAGGCCA
TGCCTTGGCACTGCACTTCCACGCAGCAGCTCTACCTCCAGCTGACGCTGCA
CCTTCTCCTGCACTTGGCAAGGTAGGTAGGGACCAGGGGTGCCTCCTCAGGG
CATCTTATCCGAGTGGAAGGAAATTTGCGTGTGGAGTATTTGGATGACGGAA
ACACACTTTTCGACATAGTGTGGTGGTGCCCTATGAGCCGCCTGAGGTTGGC
TCTGACTGTACCACCATCCACTACAACTACAGGCCTACAAAGTTCCTGAGCC`;

    setSequence(sampleWithMutation);
  };

  return (
    <div className="space-y-4">
      {/* Gene Selection */}
      <div className="space-y-2">
        <Label htmlFor="gene-select" className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Reference Gene
        </Label>
        <Select value={selectedGene} onValueChange={setSelectedGene}>
          <SelectTrigger data-testid="gene-select" id="gene-select" className="border-[#E5E4DE]">
            <SelectValue placeholder="Select gene" />
          </SelectTrigger>
          <SelectContent>
            {availableGenes.map((gene) => {
              const geneName = typeof gene === 'string' ? gene : gene?.name;
              const fullName = typeof gene === 'string' ? null : gene?.full_name;

              return (
              <SelectItem key={geneName} value={geneName}>
                <div className="flex flex-col">
                  <span className="font-medium">{geneName}</span>
                  {fullName && <span className="text-xs text-slate-500">{fullName}</span>}
                </div>
              </SelectItem>
              );
            })}
          </SelectContent>
        </Select>
      </div>

      {/* File Upload */}
      <div className="space-y-2">
        <Label className="text-xs font-bold uppercase tracking-wider text-slate-600">
          Upload File
        </Label>
        <div
          data-testid="file-dropzone"
          className={`upload-dropzone rounded-lg p-6 text-center cursor-pointer ${
            dragActive ? 'border-[#52745E] bg-[#E6EBE8]' : ''
          }`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
        >
          <input
            id="file-input"
            type="file"
            className="hidden"
            accept=".fasta,.txt,.fa"
            onChange={handleFileInput}
          />
          <Upload size={32} weight="duotone" className="mx-auto mb-2 text-[#8A948F]" />
          <p className="text-sm text-slate-700 font-medium">Drop FASTA file here</p>
          <p className="text-xs text-slate-500 mt-1">or click to browse</p>
        </div>
      </div>

      {/* Sequence Textarea */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="sequence-input" className="text-xs font-bold uppercase tracking-wider text-slate-600">
            Gene Sequence
          </Label>
          {sequence && (
            <span className="text-xs text-slate-500 font-mono">
              {sequence.replace(/\s/g, '').length} bp
            </span>
          )}
        </div>
        <Textarea
          id="sequence-input"
          data-testid="sequence-input"
          value={sequence}
          onChange={(e) => setSequence(e.target.value)}
          placeholder="Paste nucleotide sequence (A, T, C, G)..."
          className="font-mono text-sm h-48 border-[#E5E4DE] resize-none"
          style={{ fontFamily: 'IBM Plex Mono, monospace' }}
        />
      </div>

      {/* Load Sample Button */}
      <Button
        data-testid="load-sample-button"
        onClick={loadSampleSequence}
        variant="outline"
        size="sm"
        className="w-full border-[#E5E4DE] text-[#52745E] hover:bg-[#F4F3EF]"
      >
        <FileText size={16} weight="duotone" className="mr-2" />
        Load Sample Sequence
      </Button>
    </div>
  );
};

export default SequenceInput;
