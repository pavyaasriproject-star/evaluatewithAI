import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  FileText, Key, PenLine, Upload, Sparkles, Download, TrendingUp,
  AlertCircle, CheckCircle, Clock, BarChart3, LogOut, MessageSquare,
  Send, Plus, X, GraduationCap
} from 'lucide-react';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_instant-feedback-hub-1/artifacts/t71o3bm7_image.png";
const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [documents, setDocuments] = useState({ questionPaper: null, answerKey: null, answerScript: null });
  const [batchScripts, setBatchScripts] = useState([]);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [batchResults, setBatchResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [performanceHistory, setPerformanceHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('analyze');
  const [careerQuestion, setCareerQuestion] = useState('');
  const [careerMessages, setCareerMessages] = useState([]);
  const [careerLoading, setCareerLoading] = useState(false);
  const [uploadMode, setUploadMode] = useState('single');

  useEffect(() => {
    fetchPerformance();
  }, []);

  const fetchPerformance = async () => {
    try {
      const { data } = await axios.get(`${API}/performance`, { withCredentials: true });
      setPerformanceHistory(data.records || []);
    } catch {
      const local = localStorage.getItem('arivupro_history');
      if (local) setPerformanceHistory(JSON.parse(local));
    }
  };

  const fileToBase64 = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = reject;
  });

  const handleFileUpload = async (type, file) => {
    if (!file) return;
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf'];
    if (!validTypes.includes(file.type)) { toast.error('Upload JPEG, PNG, WEBP, or PDF only'); return; }
    if (file.size > 10 * 1024 * 1024) { toast.error('File must be under 10MB'); return; }
    try {
      const base64 = await fileToBase64(file);
      setDocuments(prev => ({ ...prev, [type]: { file, base64, mime: file.type } }));
      toast.success(`${type === 'questionPaper' ? 'Question Paper' : type === 'answerKey' ? 'Answer Key' : 'Answer Script'} uploaded`);
    } catch { toast.error('Failed to process file'); }
  };

  const handleBatchUpload = async (files) => {
    const validFiles = [];
    for (const file of files) {
      if (file.size > 10 * 1024 * 1024) continue;
      try {
        const base64 = await fileToBase64(file);
        validFiles.push({ file, base64, mime: file.type });
      } catch {}
    }
    setBatchScripts(prev => [...prev, ...validFiles]);
    toast.success(`${validFiles.length} script(s) added to batch`);
  };

  const removeBatchScript = (idx) => {
    setBatchScripts(prev => prev.filter((_, i) => i !== idx));
  };

  const analyzeScript = async () => {
    if (!documents.questionPaper || !documents.answerKey) {
      toast.error('Please upload Question Paper and Answer Key');
      return;
    }

    if (uploadMode === 'batch') {
      if (batchScripts.length === 0) { toast.error('Add at least one script to batch'); return; }
      setIsAnalyzing(true);
      try {
        const { data } = await axios.post(`${API}/analyze-batch`, {
          question_paper: documents.questionPaper.base64,
          answer_key: documents.answerKey.base64,
          answer_scripts: batchScripts.map(s => s.base64),
          question_mime: documents.questionPaper.mime,
          key_mime: documents.answerKey.mime,
          script_mimes: batchScripts.map(s => s.mime),
        }, { withCredentials: true, timeout: 300000 });
        setBatchResults(data);
        toast.success(`Batch analysis complete! ${data.total} scripts graded.`);
        fetchPerformance();
      } catch (e) {
        toast.error(e.response?.data?.detail || 'Batch analysis failed');
      } finally { setIsAnalyzing(false); }
    } else {
      if (!documents.answerScript) { toast.error('Please upload Answer Script'); return; }
      setIsAnalyzing(true);
      try {
        const { data } = await axios.post(`${API}/analyze`, {
          question_paper: documents.questionPaper.base64,
          answer_key: documents.answerKey.base64,
          answer_script: documents.answerScript.base64,
          question_mime: documents.questionPaper.mime,
          key_mime: documents.answerKey.mime,
          script_mime: documents.answerScript.mime,
        }, { withCredentials: true, timeout: 120000 });
        setAnalysisResult(data);
        toast.success('Analysis complete!');
        fetchPerformance();
      } catch (e) {
        console.error('Analysis error:', e);
        toast.error(e.response?.data?.detail || 'Analysis failed. Please try again.');
      } finally { setIsAnalyzing(false); }
    }
  };

  const downloadReport = async () => {
    if (!analysisResult) return;
    try {
      const { data } = await axios.post(`${API}/generate-report`, {
        analysis_result: analysisResult,
        student_name: user?.name || 'Student',
      }, { responseType: 'blob', withCredentials: true });
      const url = window.URL.createObjectURL(new Blob([data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `ArivuPro_Report_${Date.now()}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success('Report downloaded');
    } catch { toast.error('Failed to download report'); }
  };

  const sendCareerQuestion = async () => {
    if (!careerQuestion.trim()) return;
    const q = careerQuestion;
    setCareerMessages(prev => [...prev, { role: 'user', text: q }]);
    setCareerQuestion('');
    setCareerLoading(true);
    try {
      const { data } = await axios.post(`${API}/career-advisor`, {
        question: q,
        course: user?.course || null,
      }, { withCredentials: true, timeout: 60000 });
      setCareerMessages(prev => [...prev, { role: 'ai', text: data.response }]);
    } catch {
      setCareerMessages(prev => [...prev, { role: 'ai', text: 'Sorry, I encountered an error. Please try again.' }]);
    } finally { setCareerLoading(false); }
  };

  const UploadZone = ({ title, icon: Icon, type, file }) => (
    <motion.div
      data-testid={`upload-zone-${type}`}
      whileHover={{ y: -4, borderColor: '#0D9488' }}
      className="upload-zone relative border-2 border-dashed border-border-gray rounded-xl p-5 text-center cursor-pointer transition-all bg-surface-elevated/30"
      onClick={() => document.getElementById(`file-${type}`).click()}
    >
      <input id={`file-${type}`} data-testid={`file-input-${type}`} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" className="hidden" onChange={(e) => handleFileUpload(type, e.target.files[0])} />
      <div className="flex flex-col items-center gap-2">
        <Icon size={36} className={file ? 'text-primary-teal' : 'text-text-secondary'} />
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        {file ? (
          <p className="text-xs text-primary-teal flex items-center gap-1"><CheckCircle size={12} /> {file.file.name.length > 20 ? file.file.name.slice(0, 20) + '...' : file.file.name}</p>
        ) : (
          <p className="text-xs text-text-secondary">Click to upload</p>
        )}
      </div>
    </motion.div>
  );

  return (
    <div className="min-h-screen bg-[#030712]">
      {/* Header */}
      <header className="sticky top-0 z-50 py-3 px-6 bg-[#030712]/80 backdrop-blur-xl border-b border-border-gray/50">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="ArivuPro" className="w-9 h-9 rounded-xl" />
            <div>
              <h1 className="text-xl font-bold font-heading text-text-primary">ArivuPro <span className="text-primary-teal">AI</span></h1>
              <p className="text-[10px] text-text-secondary tracking-wider">Think Commerce? Think ArivuPro!</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {user && (
              <div className="hidden sm:flex items-center gap-2 text-sm">
                <GraduationCap size={16} className="text-primary-teal" />
                <span className="text-text-secondary">{user.name}</span>
                <Badge className="bg-primary-teal/10 text-primary-teal border-primary-teal/20 text-xs">{user.course}</Badge>
              </div>
            )}
            {analysisResult && (
              <Button data-testid="download-report-btn" onClick={downloadReport} size="sm" className="bg-primary-teal hover:bg-primary-teal-glow text-white">
                <Download size={16} className="mr-1" /> Report
              </Button>
            )}
            <Button data-testid="logout-btn" variant="ghost" size="sm" onClick={() => { logout(); navigate('/'); }} className="text-text-secondary hover:text-error">
              <LogOut size={18} />
            </Button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="bg-surface border border-border-gray p-1">
            <TabsTrigger data-testid="tab-analyze" value="analyze" className="data-[state=active]:bg-primary-teal data-[state=active]:text-white">
              <FileText size={16} className="mr-2" /> Analyze
            </TabsTrigger>
            <TabsTrigger data-testid="tab-performance" value="performance" className="data-[state=active]:bg-primary-teal data-[state=active]:text-white">
              <BarChart3 size={16} className="mr-2" /> Performance
            </TabsTrigger>
            <TabsTrigger data-testid="tab-advisor" value="advisor" className="data-[state=active]:bg-primary-teal data-[state=active]:text-white">
              <MessageSquare size={16} className="mr-2" /> Career Advisor
            </TabsTrigger>
          </TabsList>

          {/* ── ANALYZE TAB ── */}
          <TabsContent value="analyze" className="space-y-6">
            <Card className="bg-surface border-border-gray">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                    <Upload size={20} className="text-primary-teal" /> Upload Documents
                  </CardTitle>
                  <div className="flex gap-2">
                    <Button data-testid="mode-single" size="sm" variant={uploadMode === 'single' ? 'default' : 'outline'}
                      className={uploadMode === 'single' ? 'bg-primary-teal text-white' : 'border-border-gray text-text-secondary'}
                      onClick={() => setUploadMode('single')}>Single</Button>
                    <Button data-testid="mode-batch" size="sm" variant={uploadMode === 'batch' ? 'default' : 'outline'}
                      className={uploadMode === 'batch' ? 'bg-primary-teal text-white' : 'border-border-gray text-text-secondary'}
                      onClick={() => setUploadMode('batch')}>Batch</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <UploadZone title="Question Paper" icon={FileText} type="questionPaper" file={documents.questionPaper} />
                  <UploadZone title="Answer Key" icon={Key} type="answerKey" file={documents.answerKey} />
                  {uploadMode === 'single' && (
                    <UploadZone title="Answer Script" icon={PenLine} type="answerScript" file={documents.answerScript} />
                  )}
                </div>

                {/* Batch Scripts Area */}
                {uploadMode === 'batch' && (
                  <div className="mt-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-text-secondary">Batch Scripts ({batchScripts.length})</span>
                      <Button data-testid="add-batch-scripts" size="sm" variant="outline" className="border-primary-teal/30 text-primary-teal hover:bg-primary-teal/10"
                        onClick={() => document.getElementById('batch-upload').click()}>
                        <Plus size={16} className="mr-1" /> Add Scripts
                      </Button>
                      <input id="batch-upload" type="file" multiple accept="image/jpeg,image/png,image/webp,application/pdf" className="hidden"
                        onChange={(e) => handleBatchUpload(Array.from(e.target.files))} />
                    </div>
                    {batchScripts.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {batchScripts.map((s, i) => (
                          <Badge key={i} className="bg-surface-elevated border-border-gray text-text-secondary py-1 px-3 flex items-center gap-2">
                            {s.file.name.length > 15 ? s.file.name.slice(0, 15) + '...' : s.file.name}
                            <X size={14} className="cursor-pointer hover:text-error" onClick={() => removeBatchScript(i)} />
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="mt-6 text-center">
                  <Button data-testid="analyze-btn" onClick={analyzeScript} disabled={isAnalyzing}
                    className="bg-primary-teal hover:bg-primary-teal-glow text-white px-8 py-5 text-base font-semibold transition-all hover:shadow-[0_0_40px_rgba(13,148,136,0.4)]">
                    {isAnalyzing ? (
                      <><div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-3" /> Analyzing...</>
                    ) : (
                      <><Sparkles size={20} className="mr-2" /> {uploadMode === 'batch' ? `Analyze Batch (${batchScripts.length})` : 'Analyze with AI'}</>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Single Analysis Result */}
            <AnimatePresence>
              {analysisResult && (
                <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <Card className="bg-surface border-border-gray">
                      <CardContent className="p-6 flex flex-col items-center">
                        <div className="w-36 h-36">
                          <CircularProgressbar value={analysisResult.score_percentage}
                            text={`${analysisResult.score_percentage.toFixed(1)}%`}
                            styles={buildStyles({ pathColor: analysisResult.score_percentage >= 60 ? '#0D9488' : analysisResult.score_percentage >= 40 ? '#F59E0B' : '#EF4444', textColor: '#F9FAFB', trailColor: '#1F2937', textSize: '22px' })} />
                        </div>
                        <p className="text-sm text-text-secondary mt-3">Score</p>
                        <p className="text-xl font-bold text-text-primary font-heading">{analysisResult.obtained_marks}/{analysisResult.total_marks}</p>
                      </CardContent>
                    </Card>
                    {[
                      { label: 'Errors', value: analysisResult.errors.length, icon: AlertCircle, color: 'text-error' },
                      { label: 'Strengths', value: analysisResult.strengths.length, icon: CheckCircle, color: 'text-success' },
                      { label: 'Working Notes', value: analysisResult.working_notes_found.length, icon: BarChart3, color: 'text-warning-wn' },
                    ].map(stat => (
                      <Card key={stat.label} className="bg-surface border-border-gray">
                        <CardContent className="p-6">
                          <div className="flex items-center gap-2 mb-2">
                            <stat.icon size={20} className={stat.color} />
                            <span className="text-sm text-text-secondary">{stat.label}</span>
                          </div>
                          <p className="text-3xl font-bold text-text-primary font-heading">{stat.value}</p>
                        </CardContent>
                      </Card>
                    ))}
                  </div>

                  {analysisResult.errors.length > 0 && (
                    <Card className="bg-surface border-border-gray">
                      <CardHeader><CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                        <AlertCircle size={20} className="text-error" /> Correction Log
                      </CardTitle></CardHeader>
                      <CardContent>
                        <div className="overflow-x-auto">
                          <Table>
                            <TableHeader><TableRow className="border-border-gray">
                              <TableHead className="text-text-secondary">Q#</TableHead>
                              <TableHead className="text-text-secondary">Type</TableHead>
                              <TableHead className="text-text-secondary">Lost</TableHead>
                              <TableHead className="text-text-secondary">Your Answer</TableHead>
                              <TableHead className="text-text-secondary">Correct Answer</TableHead>
                              <TableHead className="text-text-secondary">Feedback</TableHead>
                            </TableRow></TableHeader>
                            <TableBody>
                              {analysisResult.errors.map((error, idx) => (
                                <TableRow key={idx} className="border-border-gray">
                                  <TableCell className="font-mono text-text-primary">{error.question_number}</TableCell>
                                  <TableCell><Badge className={error.error_type === 'incorrect' ? 'bg-error/15 text-error border-error/30' : error.error_type === 'missing_wn' ? 'bg-warning-wn/15 text-warning-wn border-warning-wn/30' : 'bg-primary-teal/15 text-primary-teal border-primary-teal/30'}>
                                    {error.error_type.replace('_', ' ').toUpperCase()}
                                  </Badge></TableCell>
                                  <TableCell className="text-error font-semibold">-{error.marks_deducted}</TableCell>
                                  <TableCell className="text-text-secondary text-xs max-w-[200px] truncate">{error.student_answer}</TableCell>
                                  <TableCell className="text-success text-xs max-w-[200px] truncate">{error.correct_answer}</TableCell>
                                  <TableCell className="text-text-secondary text-xs max-w-[250px]">{error.feedback}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                    {analysisResult.strengths.length > 0 && (
                      <Card className="bg-surface border-border-gray">
                        <CardHeader><CardTitle className="text-base font-heading text-text-primary flex items-center gap-2">
                          <CheckCircle size={18} className="text-success" /> Strengths
                        </CardTitle></CardHeader>
                        <CardContent><ul className="space-y-2">
                          {analysisResult.strengths.map((s, i) => (
                            <li key={i} className="text-text-secondary text-sm flex items-start gap-2"><span className="text-success mt-0.5">&#8226;</span>{s}</li>
                          ))}
                        </ul></CardContent>
                      </Card>
                    )}
                    {analysisResult.improvements.length > 0 && (
                      <Card className="bg-surface border-border-gray">
                        <CardHeader><CardTitle className="text-base font-heading text-text-primary flex items-center gap-2">
                          <TrendingUp size={18} className="text-warning-wn" /> Areas for Improvement
                        </CardTitle></CardHeader>
                        <CardContent><ul className="space-y-2">
                          {analysisResult.improvements.map((s, i) => (
                            <li key={i} className="text-text-secondary text-sm flex items-start gap-2"><span className="text-warning-wn mt-0.5">&#8226;</span>{s}</li>
                          ))}
                        </ul></CardContent>
                      </Card>
                    )}
                  </div>

                  <Card className="bg-surface border-border-gray">
                    <CardHeader><CardTitle className="text-base font-heading text-text-primary flex items-center gap-2">
                      <Sparkles size={18} className="text-primary-teal" /> Overall Feedback
                    </CardTitle></CardHeader>
                    <CardContent><p className="text-text-secondary leading-relaxed text-sm">{analysisResult.overall_feedback}</p></CardContent>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Batch Results */}
            <AnimatePresence>
              {batchResults && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
                  <h3 className="text-lg font-heading text-text-primary">Batch Results ({batchResults.total} scripts)</h3>
                  {batchResults.results.map((r, i) => (
                    <Card key={i} className="bg-surface border-border-gray">
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <span className="text-text-primary font-medium">Script #{r.index + 1}</span>
                          {r.status === 'success' ? (
                            <div className="flex items-center gap-4">
                              <Badge className="bg-primary-teal/15 text-primary-teal border-primary-teal/30">{r.result.score_percentage.toFixed(1)}%</Badge>
                              <span className="text-text-secondary text-sm">{r.result.obtained_marks}/{r.result.total_marks} marks</span>
                              <span className="text-error text-sm">{r.result.errors.length} errors</span>
                            </div>
                          ) : (
                            <Badge className="bg-error/15 text-error border-error/30">Failed</Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </TabsContent>

          {/* ── PERFORMANCE TAB ── */}
          <TabsContent value="performance" className="space-y-6">
            <Card className="bg-surface border-border-gray">
              <CardHeader><CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                <TrendingUp size={20} className="text-primary-teal" /> Your Performance Journey
              </CardTitle></CardHeader>
              <CardContent>
                {performanceHistory.length === 0 ? (
                  <div className="text-center py-16">
                    <BarChart3 size={48} className="mx-auto text-text-secondary/30 mb-4" />
                    <p className="text-text-secondary">No assessments yet. Upload and analyze your first script!</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {performanceHistory.map((record, idx) => (
                      <motion.div key={idx} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }}
                        className="flex items-center justify-between p-4 bg-surface-elevated rounded-lg border border-border-gray/50 hover:border-primary-teal/30 transition-colors">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-primary-teal/10 flex items-center justify-center">
                            <Clock size={18} className="text-primary-teal" />
                          </div>
                          <div>
                            <p className="text-text-primary text-sm font-medium">{new Date(record.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
                            <p className="text-text-secondary text-xs">{record.obtained_marks}/{record.total_marks} marks | {record.errors_count} errors</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="w-32 hidden sm:block"><Progress value={record.score_percentage} className="h-2" /></div>
                          <span className={`font-bold text-lg font-heading ${record.score_percentage >= 60 ? 'text-primary-teal' : record.score_percentage >= 40 ? 'text-warning-wn' : 'text-error'}`}>
                            {record.score_percentage.toFixed(1)}%
                          </span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* ── CAREER ADVISOR TAB ── */}
          <TabsContent value="advisor" className="space-y-4">
            <Card className="bg-surface border-border-gray h-[calc(100vh-220px)] flex flex-col">
              <CardHeader className="pb-3 border-b border-border-gray/50">
                <CardTitle className="text-lg font-heading text-text-primary flex items-center gap-2">
                  <GraduationCap size={20} className="text-primary-teal" /> Commerce Career Advisor
                  {user?.course && <Badge className="bg-primary-teal/10 text-primary-teal border-primary-teal/20 text-xs ml-2">{user.course}</Badge>}
                </CardTitle>
                <p className="text-xs text-text-secondary">Expert guidance for CA, CS, ACCA, CMA, CPA, CFA, FRM courses</p>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col p-4 overflow-hidden">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
                  {careerMessages.length === 0 && (
                    <div className="text-center py-12">
                      <GraduationCap size={48} className="mx-auto text-primary-teal/30 mb-4" />
                      <p className="text-text-secondary mb-4">Ask anything about your commerce career!</p>
                      <div className="flex flex-wrap justify-center gap-2">
                        {['How to prepare for CA Final?', 'ACCA vs CMA US career scope?', 'Best study plan for CS Executive?', 'Tips for passing CMA India Foundation'].map(q => (
                          <button key={q} onClick={() => { setCareerQuestion(q); }}
                            className="text-xs px-3 py-2 rounded-full bg-surface-elevated border border-border-gray text-text-secondary hover:text-primary-teal hover:border-primary-teal/30 transition-colors">
                            {q}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  {careerMessages.map((msg, i) => (
                    <motion.div key={i} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                      className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${msg.role === 'user' ? 'bg-primary-teal text-white rounded-br-md' : 'bg-surface-elevated border border-border-gray text-text-primary rounded-bl-md'}`}>
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                      </div>
                    </motion.div>
                  ))}
                  {careerLoading && (
                    <div className="flex justify-start">
                      <div className="bg-surface-elevated border border-border-gray rounded-2xl rounded-bl-md px-4 py-3">
                        <div className="flex gap-1">
                          {[0, 1, 2].map(i => (<div key={i} className="w-2 h-2 bg-primary-teal/50 rounded-full animate-bounce" style={{ animationDelay: `${i * 0.15}s` }} />))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <input data-testid="career-input" value={careerQuestion} onChange={(e) => setCareerQuestion(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendCareerQuestion()}
                    placeholder="Ask about your commerce career..."
                    className="flex-1 h-11 px-4 rounded-xl bg-surface-elevated border border-border-gray text-text-primary text-sm placeholder:text-text-secondary/50 focus:outline-none focus:border-primary-teal" />
                  <Button data-testid="career-send-btn" onClick={sendCareerQuestion} disabled={careerLoading || !careerQuestion.trim()}
                    className="bg-primary-teal hover:bg-primary-teal-glow text-white h-11 w-11 p-0 rounded-xl">
                    <Send size={18} />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default Dashboard;
