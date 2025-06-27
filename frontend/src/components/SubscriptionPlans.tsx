import React, { useState, useEffect } from 'react';
import { Crown, Check, Zap, ArrowRight, CreditCard } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService } from '../services/api';
import toast from 'react-hot-toast';

interface SubscriptionPlan {
  id: string;
  name: string;
  plan_type: string;
  price_monthly: number;
  price_yearly?: number;
  currency: string;
  conversations_limit: number;
  file_uploads_limit: number;
  knowledge_base_size_limit: number;
  description: string;
  is_popular: boolean;
  features: string[];
}

interface SubscriptionPlansProps {
  onPlanSelected?: (planId: string) => void;
  showCurrentPlan?: boolean;
}

export const SubscriptionPlans: React.FC<SubscriptionPlansProps> = ({
  onPlanSelected,
  showCurrentPlan = true
}) => {
  const { user } = useAuth();
  const [plans, setPlans] = useState<SubscriptionPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [subscribing, setSubscribing] = useState<string | null>(null);
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly');

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await apiService.get('/subscription/plans');
      setPlans(response.data);
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
      toast.error('Failed to load subscription plans');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (planId: string) => {
    if (!user) {
      toast.error('Please log in to subscribe');
      return;
    }

    setSubscribing(planId);
    
    try {
      const response = await apiService.post('/subscription/checkout', {
        plan_id: planId,
        billing_period: billingPeriod,
        success_url: `${window.location.origin}/subscription/success`,
        cancel_url: `${window.location.origin}/subscription/cancel`
      });

      // Redirect to Stripe checkout
      window.location.href = response.data.checkout_url;
      
    } catch (error: any) {
      console.error('Error creating checkout session:', error);
      toast.error(error.response?.data?.detail || 'Failed to start subscription process');
      setSubscribing(null);
    }
  };

  const formatPrice = (plan: SubscriptionPlan) => {
    if (plan.price_monthly === 0) {
      return 'Free';
    }
    
    const price = billingPeriod === 'yearly' && plan.price_yearly 
      ? plan.price_yearly / 12 
      : plan.price_monthly;
    
    return `$${price.toFixed(2)}`;
  };

  const formatLimit = (limit: number, unit: string) => {
    if (limit === -1) return 'Unlimited';
    if (unit === 'MB') return `${limit / (1024 * 1024)}${unit}`;
    return `${limit}`;
  };

  const getPlanIcon = (planType: string) => {
    switch (planType.toLowerCase()) {
      case 'free':
        return <Zap className="w-6 h-6" />;
      case 'pro':
        return <Crown className="w-6 h-6" />;
      case 'enterprise':
        return <CreditCard className="w-6 h-6" />;
      default:
        return <Zap className="w-6 h-6" />;
    }
  };

  const isCurrentPlan = (planType: string) => {
    return user?.subscription_tier === planType.toLowerCase();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="py-12 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Choose Your Plan
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Unlock the full potential of AI-powered CPG business assistance
          </p>
          
          {/* Billing Period Toggle */}
          <div className="mt-8 flex justify-center">
            <div className="relative bg-gray-100 p-1 rounded-lg">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`relative px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  billingPeriod === 'monthly'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`relative px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  billingPeriod === 'yearly'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-900'
                }`}
              >
                Yearly
                <span className="ml-1 text-xs text-green-600 font-semibold">Save 17%</span>
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl shadow-lg overflow-hidden transition-all hover:shadow-xl ${
                plan.is_popular 
                  ? 'ring-2 ring-blue-500 transform scale-105' 
                  : 'hover:scale-105'
              }`}
            >
              {plan.is_popular && (
                <div className="absolute top-0 left-0 right-0 bg-blue-500 text-white text-center py-2 text-sm font-medium">
                  Most Popular
                </div>
              )}
              
              <div className={`p-8 ${plan.is_popular ? 'pt-16' : ''}`}>
                {/* Plan Header */}
                <div className="text-center mb-6">
                  <div className={`inline-flex items-center justify-center w-12 h-12 rounded-full mb-4 ${
                    plan.plan_type === 'free' ? 'bg-gray-100 text-gray-600' :
                    plan.plan_type === 'pro' ? 'bg-blue-100 text-blue-600' :
                    'bg-purple-100 text-purple-600'
                  }`}>
                    {getPlanIcon(plan.plan_type)}
                  </div>
                  
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">
                    {plan.name}
                  </h3>
                  
                  <p className="text-gray-600 mb-4">
                    {plan.description}
                  </p>
                  
                  <div className="mb-6">
                    <span className="text-4xl font-bold text-gray-900">
                      {formatPrice(plan)}
                    </span>
                    {plan.price_monthly > 0 && (
                      <span className="text-gray-600 ml-1">
                        /{billingPeriod === 'yearly' ? 'month' : 'month'}
                      </span>
                    )}
                    {billingPeriod === 'yearly' && plan.price_yearly && (
                      <div className="text-sm text-gray-500 mt-1">
                        Billed annually (${plan.price_yearly}/year)
                      </div>
                    )}
                  </div>
                </div>

                {/* Features List */}
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <Check className="w-5 h-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                {/* Current Plan Badge or Subscribe Button */}
                {showCurrentPlan && isCurrentPlan(plan.plan_type) ? (
                  <button
                    disabled
                    className="w-full bg-gray-100 text-gray-500 py-3 px-6 rounded-lg font-medium cursor-not-allowed"
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => {
                      if (onPlanSelected) {
                        onPlanSelected(plan.id);
                      } else {
                        handleSubscribe(plan.id);
                      }
                    }}
                    disabled={subscribing === plan.id}
                    className={`w-full py-3 px-6 rounded-lg font-medium transition-all flex items-center justify-center ${
                      plan.plan_type === 'free'
                        ? 'bg-gray-900 text-white hover:bg-gray-800'
                        : plan.is_popular
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'bg-purple-600 text-white hover:bg-purple-700'
                    } ${subscribing === plan.id ? 'opacity-50 cursor-not-allowed' : ''}`}
                  >
                    {subscribing === plan.id ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Processing...
                      </>
                    ) : (
                      <>
                        {plan.plan_type === 'free' ? 'Get Started' : 'Subscribe'}
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-12">
          <p className="text-gray-600 mb-4">
            Need a custom solution? <a href="mailto:support@chatcpg.com" className="text-blue-600 hover:underline">Contact our sales team</a>
          </p>
          <p className="text-sm text-gray-500">
            All plans include 24/7 support and can be canceled anytime
          </p>
        </div>
      </div>
    </div>
  );
}; 