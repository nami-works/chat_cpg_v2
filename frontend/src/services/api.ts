// Remove unused axios import

// API Base URL with fallback
const getApiBaseUrl = () => {
  try {
    return (window as any).REACT_APP_API_URL || 'http://localhost:8001';
  } catch {
    return 'http://localhost:8001';
  }
};

const API_BASE_URL = getApiBaseUrl();

// Types
export interface User {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  is_active: boolean;
  created_at: string;
  subscription_tier?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Brand {
  id: string;
  name: string;
  slug: string;
  website_url?: string;
  blog_url?: string;
  brand_description?: string;
  style_guide?: string;
  products_info?: string;
  format_recommendations?: string;
  knowledge_base?: string;
  benchmarks?: string[];
  is_active: boolean;
}

export interface ContentProject {
  id: string;
  name: string;
  description?: string;
  project_type: string;
  themes?: Record<string, string>;
  seo_themes?: Record<string, string>;
  macro_name?: string;
  status: string;
  brand_id?: string;
  created_at: string;
  updated_at: string;
}

export interface ContentOutput {
  id: string;
  theme_key: string;
  theme_title: string;
  content_type: string;
  title?: string;
  content?: string;
  seo_title?: string;
  meta_description?: string;
  h1_tag?: string;
  h2_tags?: string[];
  keywords?: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  function_type: string;
  brand_id?: string;
  project_id?: string;
  model_provider: string;
  model_name: string;
  reference: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  id: string;
  content: string;
  is_user: boolean;
  created_at: string;
  metadata?: any;
}

export interface ChatContext {
  available_functions: string[];
  available_models: Record<string, Record<string, string>>;
  available_references: Record<string, string>;
  brands: Array<{
    id: string;
    name: string;
    slug: string;
  }>;
}

export interface ChatResponse {
  content: string;
  conversation_id: string;
  message_id: string;
}

// Backend availability check
let backendAvailable = true;

const checkBackendAvailability = async (): Promise<boolean> => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });
    backendAvailable = response.ok;
    return backendAvailable;
  } catch {
    backendAvailable = false;
    return false;
  }
};

// Demo data for fallback mode
const demoUsers: User[] = [
  {
    id: 'demo-1',
    email: 'demo@chatcpg.com',
    full_name: 'Demo User',
    avatar_url: null,
    is_active: true,
    created_at: new Date().toISOString()
  }
];

const demoBrands: Brand[] = [
  {
    id: 'demo-brand-1',
    name: 'GE Beauty',
    slug: 'gebeauty',
    website_url: 'https://gebeauty.com.br',
    blog_url: 'https://gebeauty.com.br/blogs/gebeauty',
    brand_description: 'Premium hair care brand focused on natural beauty',
    benchmarks: ['Gisou', 'The Crown Affair', 'Glossier'],
    is_active: true
  }
];

const demoConversations: Conversation[] = [
  {
    id: 'demo-conv-1',
    title: 'Redação CPG - GE Beauty',
    function_type: 'redacao',
    brand_id: 'demo-brand-1',
    model_provider: 'openai',
    model_name: 'gpt-4o-mini',
    reference: 'ryb',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    message_count: 0
  }
];

// Auth state management
let currentToken: string | null = localStorage.getItem('auth_token');
let currentUser: User | null = JSON.parse(localStorage.getItem('current_user') || 'null');

const setAuthData = (token: string, user: User) => {
  currentToken = token;
  currentUser = user;
  localStorage.setItem('auth_token', token);
  localStorage.setItem('current_user', JSON.stringify(user));
};

const clearAuthData = () => {
  currentToken = null;
  currentUser = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('current_user');
};

// HTTP request helper
const makeRequest = async (
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> => {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers as Record<string, string>,
  };

  if (currentToken) {
    headers.Authorization = `Bearer ${currentToken}`;
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  const response = await fetch(url, config);
  
  if (response.status === 401) {
    clearAuthData();
    throw new Error('Authentication required');
  }

  return response;
};

// API functions
export const api = {
  // Health check
  checkHealth: async (): Promise<boolean> => {
    return await checkBackendAvailability();
  },

  // Authentication
  login: async (credentials: LoginRequest): Promise<AuthResponse> => {
    if (!backendAvailable) {
      // Demo mode
      const user = demoUsers[0];
      const authResponse: AuthResponse = {
        access_token: 'demo-token',
        token_type: 'bearer',
        user
      };
      setAuthData(authResponse.access_token, authResponse.user);
      return authResponse;
    }

    const response = await makeRequest('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const authResponse: AuthResponse = await response.json();
    setAuthData(authResponse.access_token, authResponse.user);
    return authResponse;
  },

  register: async (userData: RegisterRequest): Promise<AuthResponse> => {
    if (!backendAvailable) {
      // Demo mode
      const user: User = {
        id: 'demo-new-user',
        email: userData.email,
        full_name: userData.full_name,
        avatar_url: null,
        is_active: true,
        created_at: new Date().toISOString()
      };
      const authResponse: AuthResponse = {
        access_token: 'demo-token',
        token_type: 'bearer',
        user
      };
      setAuthData(authResponse.access_token, authResponse.user);
      return authResponse;
    }

    const response = await makeRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const authResponse: AuthResponse = await response.json();
    setAuthData(authResponse.access_token, authResponse.user);
    return authResponse;
  },

  logout: async (): Promise<void> => {
    clearAuthData();
  },

  getCurrentUser: (): User | null => {
    return currentUser;
  },

  // Chat context
  getChatContext: async (): Promise<ChatContext> => {
    if (!backendAvailable) {
      return {
        available_functions: ['redacao', 'oraculo', 'general'],
        available_models: {
          openai: {
            'gpt-4o-mini': 'GPT-4o Mini',
            'gpt-4o': 'GPT-4o',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo'
          },
          groq: {
            'llama-3.3-70b': 'LLaMA 3.3 70B',
            'llama-3.1-8b': 'LLaMA 3.1 8B'
          }
        },
        available_references: {
          ryb: 'Ramping your Brand',
          tgcw: 'The Great CEO Within'
        },
        brands: demoBrands.map(brand => ({
          id: brand.id,
          name: brand.name,
          slug: brand.slug
        }))
      };
    }

    const response = await makeRequest('/chat/context');
    if (!response.ok) {
      throw new Error('Failed to fetch chat context');
    }
    return await response.json();
  },

  // Conversations
  createConversation: async (data: {
    title?: string;
    function_type?: string;
    brand_id?: string;
    project_id?: string;
    model_provider?: string;
    model_name?: string;
    reference?: string;
    api_key?: string;
  }): Promise<Conversation> => {
    if (!backendAvailable) {
      const conversation: Conversation = {
        id: `demo-conv-${Date.now()}`,
        title: data.title || 'New Conversation',
        function_type: data.function_type || 'general',
        brand_id: data.brand_id,
        project_id: data.project_id,
        model_provider: data.model_provider || 'openai',
        model_name: data.model_name || 'gpt-4o-mini',
        reference: data.reference || 'ryb',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: 0
      };
      return conversation;
    }

    const response = await makeRequest('/chat/conversations', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create conversation');
    }

    return await response.json();
  },

  getConversations: async (): Promise<Conversation[]> => {
    if (!backendAvailable) {
      return demoConversations;
    }

    const response = await makeRequest('/chat/conversations');
    if (!response.ok) {
      throw new Error('Failed to fetch conversations');
    }
    return await response.json();
  },

  getConversation: async (id: string): Promise<Conversation> => {
    if (!backendAvailable) {
      const conversation = demoConversations.find(c => c.id === id);
      if (!conversation) throw new Error('Conversation not found');
      return conversation;
    }

    const response = await makeRequest(`/chat/conversations/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch conversation');
    }
    return await response.json();
  },

  getConversationMessages: async (conversationId: string): Promise<Message[]> => {
    if (!backendAvailable) {
      return [];
    }

    const response = await makeRequest(`/chat/conversations/${conversationId}/messages`);
    if (!response.ok) {
      throw new Error('Failed to fetch messages');
    }
    return await response.json();
  },

  sendMessage: async (conversationId: string, content: string): Promise<ChatResponse> => {
    if (!backendAvailable) {
      // Demo response
      const demoResponse = `Esta é uma resposta de demonstração para: "${content}"\n\nO ChatCPG v2 está funcionando em modo demo. Para acessar todas as funcionalidades completas, configure as chaves de API no backend.`;
      return {
        content: demoResponse,
        conversation_id: conversationId,
        message_id: `demo-msg-${Date.now()}`
      };
    }

    const response = await makeRequest(`/chat/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to send message');
    }

    return await response.json();
  },

  deleteConversation: async (id: string): Promise<void> => {
    if (!backendAvailable) {
      return;
    }

    const response = await makeRequest(`/chat/conversations/${id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete conversation');
    }
  },

  // Brands
  getBrands: async (): Promise<Brand[]> => {
    if (!backendAvailable) {
      return demoBrands;
    }

    const response = await makeRequest('/brands/');
    if (!response.ok) {
      throw new Error('Failed to fetch brands');
    }
    return await response.json();
  },

  getBrand: async (id: string): Promise<Brand> => {
    if (!backendAvailable) {
      const brand = demoBrands.find(b => b.id === id);
      if (!brand) throw new Error('Brand not found');
      return brand;
    }

    const response = await makeRequest(`/brands/${id}`);
    if (!response.ok) {
      throw new Error('Failed to fetch brand');
    }
    return await response.json();
  },

  createBrand: async (data: Partial<Brand>): Promise<Brand> => {
    if (!backendAvailable) {
      const brand: Brand = {
        id: `demo-brand-${Date.now()}`,
        name: data.name || '',
        slug: data.slug || '',
        is_active: true,
        ...data
      };
      return brand;
    }

    const response = await makeRequest('/brands/', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create brand');
    }

    return await response.json();
  },

  // Content Projects
  getProjects: async (): Promise<ContentProject[]> => {
    if (!backendAvailable) {
      return [];
    }

    const response = await makeRequest('/content/projects');
    if (!response.ok) {
      throw new Error('Failed to fetch projects');
    }
    return await response.json();
  },

  createProject: async (data: {
    name: string;
    project_type?: string;
    description?: string;
    brand_id?: string;
  }): Promise<ContentProject> => {
    if (!backendAvailable) {
      const project: ContentProject = {
        id: `demo-project-${Date.now()}`,
        name: data.name,
        project_type: data.project_type || 'redacao',
        description: data.description,
        brand_id: data.brand_id,
        status: 'draft',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      };
      return project;
    }

    const response = await makeRequest('/content/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create project');
    }

    return await response.json();
  },

  parseCreativeOutputs: async (projectId: string, responseText: string): Promise<any> => {
    if (!backendAvailable) {
      return { success: true, parsed_data: {} };
    }

    const response = await makeRequest(`/content/projects/${projectId}/parse-outputs`, {
      method: 'POST',
      body: JSON.stringify({ response_text: responseText }),
    });

    if (!response.ok) {
      throw new Error('Failed to parse creative outputs');
    }

    return await response.json();
  },

  createContentOutputs: async (projectId: string): Promise<ContentOutput[]> => {
    if (!backendAvailable) {
      return [];
    }

    const response = await makeRequest(`/content/projects/${projectId}/create-outputs`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Failed to create content outputs');
    }

    return await response.json();
  },

  // Add missing methods for compatibility
  get: async (endpoint: string) => {
    const response = await makeRequest(endpoint);
    return response.json();
  },

  post: async (endpoint: string, data?: any) => {
    const response = await makeRequest(endpoint, {
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
    return response.json();
  },

  signup: async (userData: RegisterRequest): Promise<AuthResponse> => {
    return api.register(userData);
  }
};

// Export missing types and services
export type LoginData = LoginRequest;
export type SignupData = RegisterRequest;
export const apiService = api;

// Initialize backend availability check
checkBackendAvailability(); 