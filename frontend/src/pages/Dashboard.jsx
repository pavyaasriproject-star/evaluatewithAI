import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  FileText,
  Key,
  PencilLine,
  Upload,
  Sparkles,
  Download,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  ChartBar,
} from 'lucide-react';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [documents, setDocuments] = useState({
    questionPaper: null,
    answerKey: null,
    answerScript: null,
  });

  const [analysisResult, setAnalysisResult] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [performanceHistory, setPerformanceHistory] = useState([]);

  // Load performance history from localStorage
  useEffect(() => {
    const history = localStorage.getItem('arivupro_history');
    if (history) {
      setPerformanceHistory(JSON.parse(history));
    }
  }, []);

  // Convert file to base64
  const fileToBase64 = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = (error) => reject(error);
    });
  };

  // Handle file upload
  const handleFileUpload = async (type, file) => {
    if (!file) return;

    // Validate file type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    if (!validTypes.includes(file.type)) {
      toast.error('Please upload JPEG, PNG, WEBP, or PDF files only');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    try {
      const base64 = await fileToBase64(file);
      setDocuments((prev) => ({
        ...prev,
        [type]: { file, base64, mime: file.type },
      }));
      toast.success(`${type.replace(/([A-Z])/g, ' $1').trim()} uploaded successfully`);
    } catch (error) {
      toast.error('Failed to process file');
    }
  };

  // Analyze answer script
  const analyzeScript = async () => {
    if (!documents.questionPaper || !documents.answerKey || !documents.answerScript) {
      toast.error('Please upload all three documents');
      return;
    }

    setIsAnalyzing(true);
    try {
      const response = await axios.post(`${API}/analyze`, {
        question_paper: documents.questionPaper.base64,
        answer_key: documents.answerKey.base64,
        answer_script: documents.answerScript.base64,
        question_mime: documents.questionPaper.mime,
        key_mime: documents.answerKey.mime,
        script_mime: documents.answerScript.mime,
      });

      const result = response.data;
      setAnalysisResult(result);

      // Save to localStorage
      const newHistory = [
        {
          date: new Date().toISOString(),
          score: result.score_percentage,
          obtained_marks: result.obtained_marks,
          total_marks: result.total_marks,
        },
        ...performanceHistory,
      ].slice(0, 10); // Keep last 10 results

      setPerformanceHistory(newHistory);
      localStorage.setItem('arivupro_history', JSON.stringify(newHistory));

      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Analysis error:', error);
      toast.error(error.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Download PDF report
  const downloadReport = async () => {
    if (!analysisResult) return;

    try {
      const response = await axios.post(
        `${API}/generate-report`,
        {
          analysis_result: analysisResult,
          student_name: 'Student',
        },
        {
          responseType: 'blob',
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ArivuPro_Report_${Date.now()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      toast.success('Report downloaded successfully');
    } catch (error) {
      console.error('Download error:', error);
      toast.error('Failed to download report');
    }
  };

  // Upload zone component
  const UploadZone = ({ title, icon: Icon, type, file }) => (
    <div
      data-testid={`upload-zone-${type}`}
      className="upload-zone relative border-2 border-dashed border-border-gray rounded-lg p-6 text-center cursor-pointer hover:border-primary-teal transition-all"
      onClick={() => document.getElementById(`file-${type}`).click()}
    >
      <input
        id={`file-${type}`}
        data-testid={`file-input-${type}`}
        type="file"
        accept="image/jpeg,image/png,image/webp,application/pdf"
        className="hidden"
        onChange={(e) => handleFileUpload(type, e.target.files[0])}
      />
      <div className="flex flex-col items-center gap-3">
        <Icon
          size={40}
          className={file ? 'text-primary-teal' : 'text-text-secondary'}
        />
        <div>
          <h3 className="text-sm font-semibold text-text-primary mb-1">{title}</h3>
          {file ? (
            <p className="text-xs text-primary-teal flex items-center justify-center gap-1">
              <CheckCircle size={14} />
              {file.file.name}
            </p>
          ) : (
            <p className="text-xs text-text-secondary">Click to upload</p>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="glass-header sticky top-0 z-50 py-4 px-6">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-teal rounded-lg flex items-center justify-center">
              <Sparkles size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold font-heading text-text-primary">ArivuPro AI</h1>
              <p className="text-xs text-text-secondary">Professional Exam Grading</p>
            </div>
          </div>
          {analysisResult && (
            <Button
              data-testid="download-report-btn"
              onClick={downloadReport}
              className="btn-primary bg-primary-teal hover:bg-primary-teal-glow text-white"
            >
              <Download size={20} className="mr-2" />
              Download Report
            </Button>
          )}
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-8">
        {/* Upload Section */}
        <Card className="bg-surface border-border-gray">
          <CardHeader>
            <CardTitle className="text-xl font-heading text-text-primary flex items-center gap-2">
              <Upload size={24} className="text-primary-teal" />
              Upload Documents
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <UploadZone
                title="Question Paper"
                icon={FileText}
                type="questionPaper"
                file={documents.questionPaper}
              />
              <UploadZone
                title="Answer Key"
                icon={Key}
                type="answerKey"
                file={documents.answerKey}
              />
              <UploadZone
                title="Answer Script"
                icon={PencilLine}
                type="answerScript"
                file={documents.answerScript}
              />
            </div>
            <div className="mt-6 text-center">
              <Button
                data-testid="analyze-btn"
                onClick={analyzeScript}
                disabled={isAnalyzing}
                className="btn-primary bg-primary-teal hover:bg-primary-teal-glow text-white px-8 py-6 text-lg"
              >
                {isAnalyzing ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3"></div>
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles size={24} className="mr-3" />
                    Analyze with AI
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results Section */}
        {analysisResult && (
          <div className="fade-in space-y-8">
            {/* Score Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* Circular Score */}
              <Card className="lg:col-span-1 bg-surface border-border-gray">
                <CardContent className="p-6">
                  <div className="w-full max-w-[200px] mx-auto">
                    <CircularProgressbar
                      value={analysisResult.score_percentage}
                      text={`${analysisResult.score_percentage.toFixed(1)}%`}
                      styles={buildStyles({
                        pathColor: '#0D9488',
                        textColor: '#F9FAFB',
                        trailColor: '#1F2937',
                      })}
                    />
                  </div>
                  <div className="text-center mt-4">
                    <p className="text-sm text-text-secondary">Score</p>
                    <p className="text-2xl font-bold text-text-primary font-heading">
                      {analysisResult.obtained_marks}/{analysisResult.total_marks}
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Stats Cards */}
              <Card className="bg-surface border-border-gray">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <AlertCircle size={24} className="text-error" />
                    <h3 className="text-sm font-medium text-text-secondary">Errors Found</h3>
                  </div>
                  <p className="text-3xl font-bold text-text-primary font-heading">
                    {analysisResult.errors.length}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-surface border-border-gray">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <CheckCircle size={24} className="text-success" />
                    <h3 className="text-sm font-medium text-text-secondary">Strengths</h3>
                  </div>
                  <p className="text-3xl font-bold text-text-primary font-heading">
                    {analysisResult.strengths.length}
                  </p>
                </CardContent>
              </Card>

              <Card className="bg-surface border-border-gray">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-2">
                    <ChartBar size={24} className="text-warning-wn" />
                    <h3 className="text-sm font-medium text-text-secondary">Working Notes</h3>
                  </div>
                  <p className="text-3xl font-bold text-text-primary font-heading">
                    {analysisResult.working_notes_found.length}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Correction Log */}
            {analysisResult.errors.length > 0 && (
              <Card className="bg-surface border-border-gray">
                <CardHeader>
                  <CardTitle className="text-xl font-heading text-text-primary flex items-center gap-2">
                    <AlertCircle size={24} className="text-error" />
                    Detailed Correction Log
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="border-border-gray">
                          <TableHead className="text-text-secondary">Q#</TableHead>
                          <TableHead className="text-text-secondary">Error Type</TableHead>
                          <TableHead className="text-text-secondary">Marks Lost</TableHead>
                          <TableHead className="text-text-secondary">Feedback</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {analysisResult.errors.map((error, idx) => (
                          <TableRow key={idx} className="border-border-gray">
                            <TableCell className="font-mono text-text-primary">
                              {error.question_number}
                            </TableCell>
                            <TableCell>
                              <Badge
                                className={
                                  error.error_type === 'incorrect'
                                    ? 'badge-error'
                                    : error.error_type === 'missing_wn'
                                    ? 'badge-warning'
                                    : 'badge-success'
                                }
                              >
                                {error.error_type.replace('_', ' ').toUpperCase()}
                              </Badge>
                            </TableCell>
                            <TableCell className="text-error font-semibold">
                              -{error.marks_deducted}
                            </TableCell>
                            <TableCell className="text-text-secondary text-sm">
                              {error.feedback}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Strengths & Improvements */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Strengths */}
              {analysisResult.strengths.length > 0 && (
                <Card className="bg-surface border-border-gray">
                  <CardHeader>
                    <CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                      <CheckCircle size={20} className="text-success" />
                      Strengths
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysisResult.strengths.map((strength, idx) => (
                        <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                          <span className="text-success mt-0.5">•</span>
                          {strength}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}

              {/* Improvements */}
              {analysisResult.improvements.length > 0 && (
                <Card className="bg-surface border-border-gray">
                  <CardHeader>
                    <CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                      <TrendingUp size={20} className="text-warning-wn" />
                      Areas for Improvement
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {analysisResult.improvements.map((improvement, idx) => (
                        <li key={idx} className="text-text-secondary text-sm flex items-start gap-2">
                          <span className="text-warning-wn mt-0.5">•</span>
                          {improvement}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Overall Feedback */}
            <Card className="bg-surface border-border-gray">
              <CardHeader>
                <CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                  <Sparkles size={20} className="text-primary-teal" />
                  Overall Feedback
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-text-secondary leading-relaxed">{analysisResult.overall_feedback}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Performance History */}
        {performanceHistory.length > 0 && (
          <Card className="bg-surface border-border-gray">
            <CardHeader>
              <CardTitle className="text-xl font-heading text-text-primary flex items-center gap-2">
                <Clock size={24} className="text-primary-teal" />
                Performance History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {performanceHistory.map((record, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 bg-surface-elevated rounded-lg border border-border-gray"
                  >
                    <div className="flex items-center gap-4">
                      <div className="text-text-secondary text-sm">
                        {new Date(record.date).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric',
                        })}
                      </div>
                      <div className="text-text-primary font-semibold">
                        {record.obtained_marks}/{record.total_marks}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="w-32">
                        <Progress value={record.score} className="h-2" />
                      </div>
                      <div className="text-primary-teal font-bold">{record.score.toFixed(1)}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  );
};

export default Dashboard;