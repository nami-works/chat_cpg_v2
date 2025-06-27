import React, { useState, useEffect } from 'react';
import { BarChart3, MessageCircle, Upload, Database, Crown, AlertCircle, TrendingUp } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

interface UsageData {
  conversations: {
    used: number;
    limit: number;
    unlimited: boolean;
    percentage: number;
  };
  file_uploads: {
    used: number;
    limit: number;
    unlimited: boolean;
    percentage: number;
  };
  knowledge_base: {
    used_bytes: number;
    limit_bytes: number;
    used_mb: number;
    limit_mb: number;
    unlimited: boolean;
    percentage: number;
  };
  subscription: {
    tier: string;
    status?: string;
    current_period_end?: string;
    is_premium: boolean;
    last_reset?: string;
  };
}

interface UsageDashboardProps {
  showUpgradePrompt?: boolean;
  onUpgradeClick?: () => void;
}

export const UsageDashboard: React.FC<UsageDashboardProps> = ({ 
  showUpgradePrompt = true,
  onUpgradeClick 
}) => {
  const { user } = useAuth();
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const response = await apiService.get('/subscription/usage');
      setUsage(response.data);
    } catch (error) {
      console.error('Error fetching usage data:', error);
      toast.error('Failed to load usage data');
    } finally {
      setLoading(false);
    }
  };

  const getUsageColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500';
    if (percentage >= 75) return 'bg-yellow-500';
    if (percentage >= 50) return 'bg-blue-500';
    return 'bg-green-500';
  };

  const getUsageTextColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600';
    if (percentage >= 75) return 'text-yellow-600';
    if (percentage >= 50) return 'text-blue-600';
    return 'text-green-600';
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 MB';
    const mb = bytes / (1024 * 1024);
    if (mb < 1) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${mb.toFixed(1)} MB`;
  };

  const formatTierName = (tier: string) => {
    return tier.charAt(0).toUpperCase() + tier.slice(1).toLowerCase();
  };

  const getTierIcon = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'free':
        return <BarChart3 className="w-5 h-5" />;
      case 'pro':
        return <Crown className="w-5 h-5" />;
      case 'enterprise':
        return <TrendingUp className="w-5 h-5" />;
      default:
        return <BarChart3 className="w-5 h-5" />;
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier.toLowerCase()) {
      case 'free':
        return 'bg-gray-100 text-gray-800';
      case 'pro':
        return 'bg-blue-100 text-blue-800';
      case 'enterprise':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const isNearLimit = (percentage: number) => percentage >= 80;
  const isAtLimit = (percentage: number) => percentage >= 100;

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!usage) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="text-center text-gray-500">
          <AlertCircle className="w-8 h-8 mx-auto mb-2" />
          <p>Unable to load usage data</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
      {/* Header */}
      <div className="border-b bg-gray-50 px-6 py-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">Usage Overview</h3>
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getTierColor(usage.subscription.tier)}`}>
            {getTierIcon(usage.subscription.tier)}
            <span className="ml-2">{formatTierName(usage.subscription.tier)} Plan</span>
          </div>
        </div>
      </div>

      <div className="p-6">
        {/* Usage Stats */}
        <div className="space-y-6">
          {/* Conversations */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <MessageCircle className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Conversations</p>
                <p className="text-sm text-gray-500">
                  {usage.conversations.unlimited ? 'Unlimited' : `${usage.conversations.used} of ${usage.conversations.limit}`}
                </p>
              </div>
            </div>
            <div className="text-right">
              {!usage.conversations.unlimited && (
                <>
                  <p className={`text-lg font-bold ${getUsageTextColor(usage.conversations.percentage)}`}>
                    {usage.conversations.percentage.toFixed(0)}%
                  </p>
                  {isNearLimit(usage.conversations.percentage) && (
                    <p className="text-xs text-red-600 font-medium">Near limit</p>
                  )}
                </>
              )}
            </div>
          </div>

          {!usage.conversations.unlimited && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getUsageColor(usage.conversations.percentage)}`}
                style={{ width: `${Math.min(usage.conversations.percentage, 100)}%` }}
              ></div>
            </div>
          )}

          {/* File Uploads */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <Upload className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">File Uploads</p>
                <p className="text-sm text-gray-500">
                  {usage.file_uploads.unlimited ? 'Unlimited' : `${usage.file_uploads.used} of ${usage.file_uploads.limit}`}
                </p>
              </div>
            </div>
            <div className="text-right">
              {!usage.file_uploads.unlimited && (
                <>
                  <p className={`text-lg font-bold ${getUsageTextColor(usage.file_uploads.percentage)}`}>
                    {usage.file_uploads.percentage.toFixed(0)}%
                  </p>
                  {isNearLimit(usage.file_uploads.percentage) && (
                    <p className="text-xs text-red-600 font-medium">Near limit</p>
                  )}
                </>
              )}
            </div>
          </div>

          {!usage.file_uploads.unlimited && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getUsageColor(usage.file_uploads.percentage)}`}
                style={{ width: `${Math.min(usage.file_uploads.percentage, 100)}%` }}
              ></div>
            </div>
          )}

          {/* Knowledge Base */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Database className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Knowledge Base</p>
                <p className="text-sm text-gray-500">
                  {usage.knowledge_base.unlimited 
                    ? `${formatBytes(usage.knowledge_base.used_bytes)} used` 
                    : `${formatBytes(usage.knowledge_base.used_bytes)} of ${formatBytes(usage.knowledge_base.limit_bytes)}`
                  }
                </p>
              </div>
            </div>
            <div className="text-right">
              {!usage.knowledge_base.unlimited && (
                <>
                  <p className={`text-lg font-bold ${getUsageTextColor(usage.knowledge_base.percentage)}`}>
                    {usage.knowledge_base.percentage.toFixed(0)}%
                  </p>
                  {isNearLimit(usage.knowledge_base.percentage) && (
                    <p className="text-xs text-red-600 font-medium">Near limit</p>
                  )}
                </>
              )}
            </div>
          </div>

          {!usage.knowledge_base.unlimited && (
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all ${getUsageColor(usage.knowledge_base.percentage)}`}
                style={{ width: `${Math.min(usage.knowledge_base.percentage, 100)}%` }}
              ></div>
            </div>
          )}
        </div>

        {/* Upgrade Prompt */}
        {showUpgradePrompt && !usage.subscription.is_premium && (
          <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <Crown className="w-6 h-6 text-blue-600 mt-0.5" />
              <div className="flex-1">
                <h4 className="font-semibold text-gray-900 mb-1">
                  Unlock More with Pro
                </h4>
                <p className="text-sm text-gray-600 mb-3">
                  Get 10x more conversations, unlimited file uploads, and advanced AI features.
                </p>
                <button
                  onClick={onUpgradeClick}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  Upgrade Now
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Usage Reset Info */}
        {usage.subscription.last_reset && (
          <div className="mt-4 text-xs text-gray-500 text-center">
            Usage resets monthly. Last reset: {new Date(usage.subscription.last_reset).toLocaleDateString()}
          </div>
        )}
      </div>
    </div>
  );
}; 