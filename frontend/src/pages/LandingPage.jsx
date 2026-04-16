import React from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/button';
import { FileText, Brain, TrendingUp, Award, ArrowRight, BookOpen, Users } from 'lucide-react';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_instant-feedback-hub-1/artifacts/t71o3bm7_image.png";
const BG_IMAGE = "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=1920&q=80";

const fadeUp = {
  hidden: { opacity: 0, y: 40 },
  visible: (i) => ({ opacity: 1, y: 0, transition: { delay: i * 0.15, duration: 0.6, ease: 'easeOut' } })
};

const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    { icon: FileText, title: "Smart OCR", desc: "AI reads handwritten & typed answer scripts with precision" },
    { icon: Brain, title: "Semantic Grading", desc: "Understands context & intent, not just keywords" },
    { icon: TrendingUp, title: "Performance Tracking", desc: "Track your progress over time with detailed analytics" },
    { icon: Award, title: "Career Guidance", desc: "AI-powered commerce career advisor for CA, CS, ACCA, CMA" },
  ];

  return (
    <div className="min-h-screen bg-[#030712] overflow-hidden">
      {/* Hero Section */}
      <div className="relative min-h-screen flex items-center">
        {/* Background */}
        <div className="absolute inset-0">
          <img src={BG_IMAGE} alt="" className="w-full h-full object-cover opacity-10" />
          <div className="absolute inset-0 bg-gradient-to-b from-[#030712]/60 via-[#030712]/80 to-[#030712]" />
        </div>

        {/* Floating particles */}
        <div className="absolute inset-0 overflow-hidden">
          {[...Array(6)].map((_, i) => (
            <motion.div
              key={i}
              className="absolute w-2 h-2 bg-primary-teal/20 rounded-full"
              style={{ left: `${15 + i * 15}%`, top: `${20 + (i % 3) * 25}%` }}
              animate={{ y: [-20, 20, -20], opacity: [0.2, 0.6, 0.2] }}
              transition={{ duration: 4 + i, repeat: Infinity, ease: 'easeInOut' }}
            />
          ))}
        </div>

        {/* Nav */}
        <header className="absolute top-0 left-0 right-0 z-50 py-4 px-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <img src={LOGO_URL} alt="ArivuPro" className="w-10 h-10 rounded-xl" />
              <div>
                <span className="text-xl font-bold font-heading text-text-primary">ArivuPro</span>
                <span className="text-xl font-heading text-primary-teal ml-1">AI</span>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                data-testid="landing-login-btn"
                variant="outline"
                onClick={() => navigate('/auth')}
                className="border-border-gray text-text-primary hover:bg-surface-elevated hover:text-primary-teal"
              >
                Sign In
              </Button>
              <Button
                data-testid="landing-signup-btn"
                onClick={() => navigate('/auth')}
                className="bg-primary-teal hover:bg-primary-teal-glow text-white"
              >
                Get Started
              </Button>
            </div>
          </div>
        </header>

        {/* Hero Content */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 pt-32 pb-20">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <motion.div initial="hidden" animate="visible" className="space-y-6">
                <motion.div custom={0} variants={fadeUp} className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-teal/10 border border-primary-teal/20">
                  <BookOpen size={16} className="text-primary-teal" />
                  <span className="text-primary-teal text-sm font-medium">South India's No. 1 Commerce Academy</span>
                </motion.div>

                <motion.h1 custom={1} variants={fadeUp} className="text-4xl sm:text-5xl lg:text-6xl font-bold font-heading text-text-primary leading-tight">
                  Think Commerce?
                  <br />
                  <span className="text-primary-teal">Think ArivuPro!</span>
                </motion.h1>

                <motion.p custom={2} variants={fadeUp} className="text-base md:text-lg text-text-secondary max-w-lg leading-relaxed">
                  AI-powered exam grading for CA, CS, ACCA, CMA students. Upload your answer scripts, get instant feedback, track your progress, and ace your exams.
                </motion.p>

                <motion.div custom={3} variants={fadeUp} className="flex flex-wrap gap-4 pt-2">
                  <Button
                    data-testid="hero-get-started-btn"
                    onClick={() => navigate('/auth')}
                    className="bg-primary-teal hover:bg-primary-teal-glow text-white px-8 py-6 text-lg font-semibold transition-all hover:shadow-[0_0_40px_rgba(13,148,136,0.5)]"
                  >
                    Start Grading <ArrowRight size={20} className="ml-2" />
                  </Button>
                </motion.div>

                <motion.div custom={4} variants={fadeUp} className="flex items-center gap-8 pt-4">
                  <div className="flex items-center gap-2">
                    <Users size={18} className="text-primary-teal" />
                    <span className="text-text-secondary text-sm">1,00,000+ Students</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Award size={18} className="text-primary-teal" />
                    <span className="text-text-secondary text-sm">300+ Ranks</span>
                  </div>
                </motion.div>
              </motion.div>
            </div>

            {/* Right: Animated preview */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9, x: 40 }}
              animate={{ opacity: 1, scale: 1, x: 0 }}
              transition={{ delay: 0.4, duration: 0.8, ease: 'easeOut' }}
              className="hidden lg:block"
            >
              <div className="relative">
                <div className="absolute -inset-4 bg-primary-teal/10 rounded-3xl blur-xl" />
                <div className="relative bg-surface/80 backdrop-blur-xl border border-border-gray rounded-2xl p-8 space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-error" />
                    <div className="w-3 h-3 rounded-full bg-warning-wn" />
                    <div className="w-3 h-3 rounded-full bg-success" />
                    <span className="ml-auto text-text-secondary text-xs font-mono">ArivuPro AI Grader</span>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {['Question Paper', 'Answer Key', 'Your Script'].map((label, i) => (
                      <motion.div
                        key={label}
                        className="bg-surface-elevated border border-border-gray rounded-lg p-4 text-center"
                        animate={{ borderColor: ['#374151', '#0D9488', '#374151'] }}
                        transition={{ duration: 2, delay: i * 0.5, repeat: Infinity }}
                      >
                        <FileText size={24} className="mx-auto text-primary-teal mb-2" />
                        <p className="text-xs text-text-secondary">{label}</p>
                      </motion.div>
                    ))}
                  </div>
                  <motion.div
                    className="bg-primary-teal/10 border border-primary-teal/30 rounded-lg p-4"
                    animate={{ opacity: [0.5, 1, 0.5] }}
                    transition={{ duration: 2, repeat: Infinity }}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-primary-teal text-sm font-semibold">Score: 82%</span>
                      <span className="text-success text-xs">+15% improvement</span>
                    </div>
                    <div className="mt-2 h-2 bg-surface rounded-full overflow-hidden">
                      <motion.div
                        className="h-full bg-primary-teal rounded-full"
                        initial={{ width: '0%' }}
                        animate={{ width: '82%' }}
                        transition={{ duration: 2, delay: 1 }}
                      />
                    </div>
                  </motion.div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Features */}
      <section className="py-24 px-6 relative">
        <div className="max-w-7xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-2xl sm:text-3xl font-bold font-heading text-text-primary">
              Everything You Need to <span className="text-primary-teal">Excel</span>
            </h2>
            <p className="text-base text-text-secondary mt-3 max-w-lg mx-auto">
              Powered by AI to help you prepare better and score higher
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                custom={i}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
                variants={fadeUp}
              >
                <div className="bg-surface border border-border-gray rounded-xl p-6 hover:border-primary-teal/40 transition-all group h-full">
                  <div className="w-12 h-12 rounded-xl bg-primary-teal/10 flex items-center justify-center mb-4 group-hover:bg-primary-teal/20 transition-colors">
                    <feature.icon size={24} className="text-primary-teal" />
                  </div>
                  <h3 className="text-lg font-semibold text-text-primary mb-2 font-heading">{feature.title}</h3>
                  <p className="text-sm text-text-secondary leading-relaxed">{feature.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border-gray py-8 px-6">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src={LOGO_URL} alt="ArivuPro" className="w-8 h-8 rounded-lg" />
            <span className="text-text-secondary text-sm">ArivuPro Academy - South India's No. 1 Commerce Academy</span>
          </div>
          <a href="https://www.arivupro.com/" target="_blank" rel="noopener noreferrer" className="text-primary-teal text-sm hover:underline">
            www.arivupro.com
          </a>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
