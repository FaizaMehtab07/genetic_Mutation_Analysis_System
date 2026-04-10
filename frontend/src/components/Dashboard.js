import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Flask, Play, FileText, CircleNotch } from '@phosphor-icons/react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import SequenceInput from './SequenceInput';
import ResultsView from './ResultsView';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api/v1`;

const formatApiError = (error) => {
  const detail = error?.response?.data?.detail;

  if (Array.isArray(detail)) {
    return detail
      .map((item) => item?.msg || item?.message || JSON.stringify(item))
      .filter(Boolean)
      .join(' | ');
  }

  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail);
  }

  if (typeof detail === 'string' && detail.trim()) {
    return detail;
  }

  if (typeof error?.message === 'string' && error.message.trim()) {
    return error.message;
  }

  return 'Analysis failed. Please try again.';
};

const Dashboard = () => {
  const [sequence, setSequence] = useState('');
  const [selectedGene, setSelectedGene] = useState('TP53');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');
  const [results, setResults] = useState(null);
  const [availableGenes, setAvailableGenes] = useState([]);

  // Load available genes on mount
  React.useEffect(() => {
    loadGenes();
  }, []);

  const loadGenes = async () => {
    try {
      const response = await axios.get(`${API}/reference-genes`);
      setAvailableGenes(response.data.available_genes || []);
    } catch (error) {
      console.error('Error loading genes:', error);
    }
  };

  const handleAnalyze = async () => {
    if (!sequence.trim()) {
      toast.error('Please enter a gene sequence');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);
    setResults(null);

    const steps = [
      { name: 'Validating sequence...', progress: 14 },
      { name: 'Aligning with reference...', progress: 28 },
      { name: 'Detecting mutations...', progress: 42 },
      { name: 'Annotating changes...', progress: 56 },
      { name: 'Classifying risk...', progress: 70 },
      { name: 'Retrieving evidence...', progress: 84 },
      { name: 'Generating explanation...', progress: 100 }
    ];

    // Simulate progress
    let stepIndex = 0;
    const progressInterval = setInterval(() => {
      if (stepIndex < steps.length) {
        setCurrentStep(steps[stepIndex].name);
        setAnalysisProgress(steps[stepIndex].progress);
        stepIndex++;
      }
    }, 800);

    try {
      const response = await axios.post(`${API}/analyze`, {
        sequence: sequence,
        gene: selectedGene
      });

      clearInterval(progressInterval);
      setAnalysisProgress(100);
      setCurrentStep('Analysis complete!');
      setResults(response.data);
      toast.success('Analysis completed successfully!');
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Analysis error:', error);
      toast.error(formatApiError(error));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleFileUpload = async (file) => {
    try {
      const text = await file.text();
      const cleaned = text
        .split(/\r?\n/)
        .filter((line) => !line.startsWith('>'))
        .join('')
        .replace(/\s/g, '')
        .toUpperCase();

      setSequence(cleaned);
      toast.success(`Loaded sequence (${cleaned.length} nucleotides)`);
    } catch (error) {
      console.error('Upload error:', error);
      toast.error('Failed to read file');
    }
  };

  const handleReset = () => {
    setSequence('');
    setResults(null);
    setAnalysisProgress(0);
    setCurrentStep('');
  };

  return (
    <div className="min-h-screen bg-[#FDFCF9]">
      {/* Header */}
      <header className="border-b border-[#E5E4DE] bg-white shadow-sm">
        <div className="w-full max-w-7xl mx-auto px-4 md:px-8 py-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-[#E6EBE8] rounded-lg">
              <Flask size={28} weight="duotone" className="text-[#52745E]" />
            </div>
            <div>
              <h1 className="text-2xl md:text-3xl font-semibold tracking-tight text-slate-900" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                Gene Mutation Analysis
              </h1>
              <p className="text-sm text-slate-600">Multi-Agent AI System for Clinical Interpretation</p>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="w-full max-w-7xl mx-auto px-4 md:px-8 py-6">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          {/* Left Panel - Input */}
          <div className="col-span-1 md:col-span-4 space-y-6">
            <Card data-testid="input-card" className="border border-[#E5E4DE] shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                  <FileText size={20} weight="duotone" />
                  Sequence Input
                </CardTitle>
                <CardDescription>Upload or paste your gene sequence</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <SequenceInput 
                  sequence={sequence}
                  setSequence={setSequence}
                  onFileUpload={handleFileUpload}
                  selectedGene={selectedGene}
                  setSelectedGene={setSelectedGene}
                  availableGenes={availableGenes}
                />
              </CardContent>
            </Card>

            <Card data-testid="control-card" className="border border-[#E5E4DE] shadow-sm">
              <CardContent className="pt-6 space-y-4">
                <Button 
                  data-testid="analyze-button"
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !sequence.trim()}
                  className="w-full bg-[#52745E] hover:bg-[#425F4C] text-white transition-colors duration-200"
                  size="lg"
                >
                  {isAnalyzing ? (
                    <>
                      <CircleNotch size={20} className="mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Play size={20} weight="fill" className="mr-2" />
                      Run Analysis
                    </>
                  )}
                </Button>

                {sequence && (
                  <Button 
                    data-testid="reset-button"
                    onClick={handleReset}
                    variant="outline"
                    className="w-full border-[#E5E4DE]"
                  >
                    Reset
                  </Button>
                )}
              </CardContent>
            </Card>

            {/* Progress Indicator */}
            {isAnalyzing && (
              <Card data-testid="progress-card" className="border border-[#E5E4DE] shadow-sm">
                <CardContent className="pt-6 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold uppercase tracking-wider text-[#8A948F]">
                      {currentStep}
                    </span>
                    <span className="text-xs font-mono text-[#8A948F]">
                      {analysisProgress}%
                    </span>
                  </div>
                  <Progress value={analysisProgress} className="h-2" />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Right Panel - Results */}
          <div className="col-span-1 md:col-span-8">
            {results ? (
              <ResultsView results={results} />
            ) : (
              <Card data-testid="empty-state" className="border border-[#E5E4DE] shadow-sm">
                <CardContent className="py-16">
                  <div className="text-center space-y-4">
                    <div className="flex justify-center">
                      <div className="p-6 bg-[#F4F3EF] rounded-full">
                        <CircleNotch size={48} weight="duotone" className="text-[#8A948F]" />
                      </div>
                    </div>
                    <div>
                      <h3 className="text-xl font-medium text-slate-800" style={{ fontFamily: 'Work Sans, sans-serif' }}>
                        Ready to Analyze
                      </h3>
                      <p className="text-sm text-slate-600 mt-2 max-w-md mx-auto">
                        Enter a gene sequence and click "Run Analysis" to detect mutations,
                        classify risk, and generate AI-powered clinical interpretations.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
