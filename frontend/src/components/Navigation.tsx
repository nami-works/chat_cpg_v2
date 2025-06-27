import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  MessageCircle, 
  CreditCard, 
  BarChart3, 
  User, 
  LogOut, 
  Menu, 
  X,
  Crown,
  Settings
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

interface NavigationProps {
  className?: string;
}

export const Navigation: React.FC<NavigationProps> = ({ className = '' }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    {
      path: '/chat',
      icon: MessageCircle,
      label: 'Chat',
      description: 'AI Assistant'
    },
    {
      path: '/usage',
      icon: BarChart3,
      label: 'Usage',
      description: 'Track your limits'
    },
    {
      path: '/subscription',
      icon: CreditCard,
      label: 'Plans',
      description: 'Manage subscription'
    }
  ];

  const isActive = (path: string) => location.pathname === path;

  const formatTierName = (tier: string) => {
    return tier?.charAt(0).toUpperCase() + tier?.slice(1).toLowerCase() || 'Free';
  };

  const getTierColor = (tier: string) => {
    switch (tier?.toLowerCase()) {
      case 'pro':
        return 'bg-blue-100 text-blue-800';
      case 'enterprise':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  return (
    <nav className={`bg-white border-b border-gray-200 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link to="/chat" className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <MessageCircle className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl text-gray-900">ChatCPG</span>
              <span className="text-xs text-gray-500 font-medium">v2</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <item.icon className="w-4 h-4 mr-2" />
                {item.label}
              </Link>
            ))}
          </div>

          {/* User Menu */}
          <div className="flex items-center space-x-4">
            {/* User Tier Badge */}
            {user && (
              <div className={`hidden sm:flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTierColor(user.subscription_tier)}`}>
                {user.subscription_tier !== 'free' && <Crown className="w-3 h-3 mr-1" />}
                {formatTierName(user.subscription_tier)}
              </div>
            )}

            {/* User Menu Dropdown */}
            <div className="relative">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4" />
                </div>
                {isMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
              </button>

              {/* Dropdown Menu */}
              {isMenuOpen && (
                <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border border-gray-200 py-2 z-50">
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-gray-100">
                    <p className="text-sm font-medium text-gray-900">
                      {user?.full_name || user?.email}
                    </p>
                    <p className="text-xs text-gray-500">{user?.email}</p>
                    <div className={`inline-flex items-center mt-2 px-2 py-1 rounded-full text-xs font-medium ${getTierColor(user?.subscription_tier)}`}>
                      {user?.subscription_tier !== 'free' && <Crown className="w-3 h-3 mr-1" />}
                      {formatTierName(user?.subscription_tier)} Plan
                    </div>
                  </div>

                  {/* Mobile Navigation Items */}
                  <div className="md:hidden border-b border-gray-100 py-2">
                    {navItems.map((item) => (
                      <Link
                        key={item.path}
                        to={item.path}
                        onClick={() => setIsMenuOpen(false)}
                        className={`flex items-center px-4 py-2 text-sm transition-colors ${
                          isActive(item.path)
                            ? 'bg-blue-50 text-blue-700'
                            : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                        }`}
                      >
                        <item.icon className="w-4 h-4 mr-3" />
                        <div>
                          <div className="font-medium">{item.label}</div>
                          <div className="text-xs text-gray-500">{item.description}</div>
                        </div>
                      </Link>
                    ))}
                  </div>

                  {/* Menu Actions */}
                  <div className="py-2">
                    <button
                      onClick={() => {
                        setIsMenuOpen(false);
                        // Add settings functionality here
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900 transition-colors"
                    >
                      <Settings className="w-4 h-4 mr-3" />
                      Settings
                    </button>
                    
                    <button
                      onClick={() => {
                        setIsMenuOpen(false);
                        handleLogout();
                      }}
                      className="flex items-center w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                    >
                      <LogOut className="w-4 h-4 mr-3" />
                      Sign out
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Click outside to close menu */}
      {isMenuOpen && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setIsMenuOpen(false)}
        />
      )}
    </nav>
  );
}; 