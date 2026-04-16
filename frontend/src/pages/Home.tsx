import React from 'react';
import { Link } from 'react-router-dom';
import { TrendingUp, Zap, BarChart3, Lock, ArrowRight, Sparkles } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

const Home: React.FC = () => {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: Zap,
      title: 'ML-Powered Signals',
      description: 'Advanced machine learning models predict stock movements with high accuracy'
    },
    {
      icon: BarChart3,
      title: 'Real-Time Analytics',
      description: 'Live market data, technical indicators, and performance tracking'
    },
    {
      icon: Lock,
      title: 'Secure Trading',
      description: 'JWT authentication and encrypted transactions for your safety'
    },
    {
      icon: Sparkles,
      title: 'Smart Portfolio',
      description: 'AI-powered portfolio management and risk analysis'
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* Navigation Bar */}
      <nav className="fixed top-0 w-full bg-slate-900/80 backdrop-blur-md border-b border-slate-700 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <TrendingUp className="h-8 w-8 text-blue-500" />
            <span className="text-2xl font-bold">StockPulse</span>
          </div>
          <div className="flex gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
              >
                Go to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  to="/login"
                  className="px-6 py-2 text-slate-300 hover:text-white transition-colors"
                >
                  Login
                </Link>
                <Link
                  to="/signup"
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
                >
                  Get Started
                </Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center space-y-8">
          {/* Main Heading */}
          <div className="space-y-4">
            <div className="inline-block px-4 py-2 bg-blue-500/10 border border-blue-500/20 rounded-full text-sm text-blue-300 mb-4">
              🚀 AI-Powered Stock Trading Platform
            </div>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight">
              Trade Smarter with{' '}
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                AI Intelligence
              </span>
            </h1>
            <p className="text-xl text-slate-400 max-w-2xl mx-auto">
              Harness machine learning predictions, real-time analytics, and secure trading to maximize your investment returns.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to={isAuthenticated ? '/dashboard' : '/signup'}
              className="group px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white font-bold rounded-lg transition-all duration-300 transform hover:scale-105 flex items-center justify-center gap-2"
            >
              {isAuthenticated ? 'Open Dashboard' : 'Get Started Free'}
              <ArrowRight className="h-5 w-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 border border-slate-600 hover:border-slate-500 rounded-lg font-bold transition-colors hover:bg-slate-800"
            >
              View API Docs
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto pt-12">
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">8</div>
              <div className="text-sm text-slate-400">Stocks Tracked</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">22</div>
              <div className="text-sm text-slate-400">API Endpoints</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-400">24/7</div>
              <div className="text-sm text-slate-400">Live Updates</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-slate-800/50">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div
                  key={i}
                  className="p-6 bg-slate-700/50 border border-slate-600 rounded-lg hover:border-blue-500/50 transition-colors group"
                >
                  <div className="mb-4 p-3 bg-blue-500/10 rounded-lg w-fit group-hover:bg-blue-500/20 transition-colors">
                    <Icon className="h-6 w-6 text-blue-400" />
                  </div>
                  <h3 className="text-lg font-bold mb-2">{feature.title}</h3>
                  <p className="text-slate-400 text-sm">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <h2 className="text-4xl font-bold text-center mb-16">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {[
            {
              step: '1',
              title: 'Sign Up',
              description: 'Create your account in seconds and get instant access to trading'
            },
            {
              step: '2',
              title: 'Add Funds',
              description: 'Fund your wallet using our secure payment gateway'
            },
            {
              step: '3',
              title: 'Start Trading',
              description: 'Follow ML signals and execute trades with real-time analytics'
            },
          ].map((item, i) => (
            <div key={i} className="relative">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-blue-600 flex items-center justify-center font-bold text-lg">
                  {item.step}
                </div>
                <div>
                  <h3 className="text-lg font-bold mb-2">{item.title}</h3>
                  <p className="text-slate-400">{item.description}</p>
                </div>
              </div>
              {i < 2 && (
                <div className="hidden md:block absolute right-[-20px] top-6 w-10 h-0.5 bg-gradient-to-r from-blue-600 to-transparent" />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-r from-blue-600 to-cyan-600">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h2 className="text-4xl font-bold">Ready to Start Trading?</h2>
          <p className="text-lg text-blue-100">Join thousands of traders using AI-powered insights to make smarter investment decisions.</p>
          <Link
            to={isAuthenticated ? '/dashboard' : '/signup'}
            className="inline-block px-8 py-4 bg-white text-blue-600 font-bold rounded-lg hover:bg-slate-100 transition-colors"
          >
            {isAuthenticated ? 'Open Dashboard' : 'Get Started Now'}
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-slate-700 bg-slate-900/50">
        <div className="max-w-7xl mx-auto text-center text-slate-400 text-sm">
          <p>&copy; 2026 StockPulse. All rights reserved. | <a href="http://localhost:8000/docs" className="text-blue-400 hover:text-blue-300">API Documentation</a></p>
        </div>
      </footer>
    </div>
  );
};

export default Home;
