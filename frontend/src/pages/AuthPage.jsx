import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react';

const LOGO_URL = "https://customer-assets.emergentagent.com/job_instant-feedback-hub-1/artifacts/t71o3bm7_image.png";

const COURSES = ["CA", "CS", "ACCA", "CMA India", "CMA US", "CPA US", "CFA", "FRM"];

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [course, setCourse] = useState('CA');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    let result;
    if (isLogin) {
      result = await login(email, password);
    } else {
      if (!name.trim()) { setError('Name is required'); setLoading(false); return; }
      if (password.length < 6) { setError('Password must be at least 6 characters'); setLoading(false); return; }
      result = await register(name, email, password, course);
    }
    setLoading(false);
    if (result.success) {
      navigate('/dashboard');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="min-h-screen bg-[#030712] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Animated background */}
      <div className="absolute inset-0">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-teal/5 rounded-full blur-3xl animate-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-primary-teal/3 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }} />
        {/* Grid pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(13,148,136,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(13,148,136,0.3) 1px, transparent 1px)', backgroundSize: '60px 60px' }} />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="w-full max-w-md z-10"
      >
        {/* Logo & Branding */}
        <div className="text-center mb-8">
          <motion.img
            src={LOGO_URL}
            alt="ArivuPro Academy"
            className="w-20 h-20 mx-auto mb-4 rounded-2xl"
            initial={{ scale: 0.5 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 200 }}
          />
          <h1 className="text-3xl font-bold font-heading text-text-primary">ArivuPro Academy</h1>
          <p className="text-primary-teal font-medium mt-1 text-sm tracking-wide">Think Commerce? Think ArivuPro!</p>
        </div>

        <Card className="bg-surface/80 border-border-gray backdrop-blur-xl">
          <CardHeader className="pb-4">
            <CardTitle className="text-xl font-heading text-text-primary text-center">
              {isLogin ? 'Welcome Back' : 'Create Account'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <Label className="text-text-secondary text-sm">Full Name</Label>
                  <Input
                    data-testid="auth-name-input"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="bg-surface-elevated border-border-gray text-text-primary mt-1"
                    placeholder="Your full name"
                  />
                </div>
              )}

              <div>
                <Label className="text-text-secondary text-sm">Email</Label>
                <Input
                  data-testid="auth-email-input"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="bg-surface-elevated border-border-gray text-text-primary mt-1"
                  placeholder="student@example.com"
                  required
                />
              </div>

              <div>
                <Label className="text-text-secondary text-sm">Password</Label>
                <div className="relative mt-1">
                  <Input
                    data-testid="auth-password-input"
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="bg-surface-elevated border-border-gray text-text-primary pr-10"
                    placeholder="Enter password"
                    required
                  />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary">
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              {!isLogin && (
                <div>
                  <Label className="text-text-secondary text-sm">Course</Label>
                  <select
                    data-testid="auth-course-select"
                    value={course}
                    onChange={(e) => setCourse(e.target.value)}
                    className="w-full mt-1 h-10 px-3 rounded-md bg-surface-elevated border border-border-gray text-text-primary text-sm"
                  >
                    {COURSES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              )}

              {error && (
                <motion.p
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-error text-sm bg-error/10 p-3 rounded-lg border border-error/20"
                  data-testid="auth-error-message"
                >
                  {error}
                </motion.p>
              )}

              <Button
                data-testid="auth-submit-btn"
                type="submit"
                disabled={loading}
                className="w-full bg-primary-teal hover:bg-primary-teal-glow text-white py-5 text-base font-semibold transition-all hover:shadow-[0_0_30px_rgba(13,148,136,0.4)]"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                ) : isLogin ? (
                  <><LogIn size={20} className="mr-2" /> Sign In</>
                ) : (
                  <><UserPlus size={20} className="mr-2" /> Create Account</>
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <button
                data-testid="auth-toggle-btn"
                onClick={() => { setIsLogin(!isLogin); setError(''); }}
                className="text-text-secondary text-sm hover:text-primary-teal transition-colors"
              >
                {isLogin ? "Don't have an account? " : "Already have an account? "}
                <span className="text-primary-teal font-semibold">{isLogin ? 'Sign Up' : 'Sign In'}</span>
              </button>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
};

export default AuthPage;
