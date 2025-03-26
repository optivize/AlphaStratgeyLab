import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import ThemeToggle from '../components/ThemeToggle';

const Register: React.FC = () => {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreeTerms, setAgreeTerms] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { register, user, error } = useAuth();
  const { theme } = useTheme();
  const navigate = useNavigate();

  // If user is already logged in, redirect to dashboard
  useEffect(() => {
    if (user) {
      navigate('/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const validateForm = () => {
    if (password !== confirmPassword) {
      setFormError('Passwords do not match');
      return false;
    }

    if (password.length < 8) {
      setFormError('Password must be at least 8 characters long');
      return false;
    }

    if (!agreeTerms) {
      setFormError('You must agree to the terms and conditions');
      return false;
    }

    return true;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await register(username, email, password);
      // Upon successful registration, auth context will update the user state,
      // triggering the useEffect above to redirect
    } catch (err: any) {
      setFormError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="register-page">
      <div className="position-absolute top-0 end-0 p-3">
        <ThemeToggle />
      </div>
      
      <div className="container mt-5 pt-5">
        <div className="row justify-content-center">
          <div className="col-md-6 col-lg-5">
            <div className="card shadow">
              <div className="card-body p-4">
                <div className="text-center mb-4">
                  <img 
                    src="/static/images/logo.svg" 
                    alt="Stock Backtest" 
                    height="60" 
                    className="mb-3" 
                  />
                  <h2 className="h4 mb-1">Create an Account</h2>
                  <p className="text-muted">Get started with StockTester</p>
                </div>

                {(formError || error) && (
                  <div className="alert alert-danger" role="alert">
                    {formError || error}
                  </div>
                )}

                <form onSubmit={handleSubmit}>
                  <div className="mb-3">
                    <label htmlFor="username" className="form-label">Username</label>
                    <input
                      type="text"
                      className="form-control"
                      id="username"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      required
                      autoFocus
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="email" className="form-label">Email Address</label>
                    <input
                      type="email"
                      className="form-control"
                      id="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label htmlFor="password" className="form-label">Password</label>
                    <input
                      type="password"
                      className="form-control"
                      id="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                    />
                    <div className="form-text">
                      Password must be at least 8 characters long.
                    </div>
                  </div>

                  <div className="mb-3">
                    <label htmlFor="confirmPassword" className="form-label">Confirm Password</label>
                    <input
                      type="password"
                      className="form-control"
                      id="confirmPassword"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                    />
                  </div>

                  <div className="form-check mb-3">
                    <input
                      type="checkbox"
                      className="form-check-input"
                      id="agreeTerms"
                      checked={agreeTerms}
                      onChange={(e) => setAgreeTerms(e.target.checked)}
                      required
                    />
                    <label className="form-check-label" htmlFor="agreeTerms">
                      I agree to the <a href="#" onClick={(e) => e.preventDefault()}>Terms and Conditions</a>
                    </label>
                  </div>

                  <div className="d-grid">
                    <button
                      type="submit"
                      className="btn btn-primary"
                      disabled={isSubmitting}
                    >
                      {isSubmitting ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                          Creating Account...
                        </>
                      ) : 'Register'}
                    </button>
                  </div>
                </form>

                <div className="text-center mt-4">
                  <p>
                    Already have an account? <Link to="/login">Sign in</Link>
                  </p>
                </div>
              </div>
            </div>

            <div className="text-center mt-3">
              <p className="text-muted small">
                &copy; {new Date().getFullYear()} StockTester
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;