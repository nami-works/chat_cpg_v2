import React, { useState, useEffect, useRef } from 'react';
import { Send, Plus, MessageCircle, LogOut, User, Bot, Loader } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { apiService, Conversation, Message, ChatContext, Brand } from '../services/api';
import { toast } from 'react-hot-toast';

const FUNCTION_DESCRIPTIONS = {
  general: 'General conversation and consultation',
  redacao: 'Content creation and blog post themes generation',
  oraculo: 'Strategic business consultation and insights'
};

const FUNCTION_COLORS = {
  general: 'bg-blue-500',
  redacao: 'bg-green-500',
  oraculo: 'bg-purple-500'
};

export const ChatInterface: React.FC = () => {
  const { user, logout } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatContext, setChatContext] = useState<ChatContext | null>(null);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [showNewChatModal, setShowNewChatModal] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  const [parsedThemes, setParsedThemes] = useState<any>(null);
  const [showThemeActions, setShowThemeActions] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (currentConversation) {
      loadMessages(currentConversation.id);
    }
  }, [currentConversation]);

  const loadInitialData = async () => {
    try {
      const [contextData, conversationsData, brandsData] = await Promise.all([
        apiService.getChatContext(),
        apiService.getConversations(),
        apiService.getBrands()
      ]);
      
      setChatContext(contextData);
      setConversations(conversationsData);
      setBrands(brandsData);
      
      if (conversationsData.length > 0) {
        setCurrentConversation(conversationsData[0]);
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
    }
  };

  const loadMessages = async (conversationId: string) => {
    try {
      const messagesData = await apiService.getConversationMessages(conversationId);
      setMessages(messagesData);
      
      // Check for parsed themes in the last AI message
      const lastAiMessage = messagesData
        .filter(m => !m.is_user && m.metadata?.parsed_data)
        .pop();
      
      if (lastAiMessage?.metadata?.parsed_data) {
        setParsedThemes(lastAiMessage.metadata.parsed_data);
        setShowThemeActions(true);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
      setMessages([]);
    }
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !currentConversation || isLoading) return;

    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      content: inputMessage,
      is_user: true,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await apiService.sendMessage(currentConversation.id, inputMessage);
      
      const aiMessage: Message = {
        id: response.message_id,
        content: response.content,
        is_user: false,
        created_at: new Date().toISOString()
      };

      setMessages(prev => [...prev.slice(0, -1), userMessage, aiMessage]);
      
      // Check for creative outputs in redacao mode
      if (currentConversation.function_type === 'redacao' && currentConversation.project_id) {
        try {
          const parseResult = await apiService.parseCreativeOutputs(currentConversation.project_id, response.content);
          if (parseResult.parsed_data && Object.keys(parseResult.parsed_data).length > 0) {
            setParsedThemes(parseResult.parsed_data);
            setShowThemeActions(true);
          }
        } catch (error) {
          console.error('Error parsing creative outputs:', error);
        }
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setIsLoading(false);
    }
  };

  const createNewConversation = async (data: {
    title?: string;
    function_type: string;
    brand_id?: string;
    model_provider: string;
    model_name: string;
    reference: string;
    api_key?: string;
  }) => {
    try {
      // Create project if redacao mode
      let project_id;
      if (data.function_type === 'redacao') {
        const brand = brands.find(b => b.id === data.brand_id);
        const project = await apiService.createProject({
          name: `${data.title || 'Redação'} - ${brand?.name || 'Projeto'}`,
          project_type: 'redacao',
          brand_id: data.brand_id
        });
        project_id = project.id;
      }

      const conversation = await apiService.createConversation({
        ...data,
        project_id
      });
      
      setConversations(prev => [conversation, ...prev]);
      setCurrentConversation(conversation);
      setMessages([]);
      setShowNewChatModal(false);
      setParsedThemes(null);
      setShowThemeActions(false);
      
    } catch (error) {
      console.error('Error creating conversation:', error);
    }
  };

  const deleteConversation = async (id: string) => {
    try {
      await apiService.deleteConversation(id);
      setConversations(prev => prev.filter(c => c.id !== id));
      
      if (currentConversation?.id === id) {
        const remainingConversations = conversations.filter(c => c.id !== id);
        setCurrentConversation(remainingConversations[0] || null);
        setMessages([]);
        setParsedThemes(null);
        setShowThemeActions(false);
      }
    } catch (error) {
      console.error('Error deleting conversation:', error);
    }
  };

  const requestContent = async () => {
    if (!currentConversation?.project_id) return;
    
    try {
      await apiService.createContentOutputs(currentConversation.project_id);
      setShowThemeActions(false);
      
      // Add system message
      const systemMessage: Message = {
        id: `system-${Date.now()}`,
        content: '✅ Conteúdo solicitado com sucesso! Os temas foram processados e o conteúdo está sendo gerado.',
        is_user: false,
        created_at: new Date().toISOString()
      };
      
      setMessages(prev => [...prev, systemMessage]);
      
    } catch (error) {
      console.error('Error requesting content:', error);
    }
  };

  const makeAdjustments = () => {
    setShowThemeActions(false);
    setParsedThemes(null);
    
    // Add system message
    const systemMessage: Message = {
      id: `system-${Date.now()}`,
      content: '🔴 Modo de ajuste ativado. Você pode solicitar modificações nos temas propostos.',
      is_user: false,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, systemMessage]);
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${showSidebar ? 'w-80' : 'w-0'} transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden`}>
        <div className="p-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">ChatCPG v2</h2>
            <button
              onClick={() => setShowNewChatModal(true)}
              className="bg-blue-500 text-white px-3 py-1 rounded-md text-sm hover:bg-blue-600 transition-colors"
            >
              Nova Conversa
            </button>
          </div>
          
          <div className="text-xs text-gray-500 mb-2">
            Usuário: {user?.full_name}
          </div>
          
          {currentConversation && (
            <div className="text-xs bg-gray-100 rounded-md p-2">
              <div className={`inline-block px-2 py-1 rounded text-white text-xs mb-1 ${FUNCTION_COLORS[currentConversation.function_type as keyof typeof FUNCTION_COLORS]}`}>
                {currentConversation.function_type.toUpperCase()}
              </div>
              <div className="text-gray-600">
                {currentConversation.model_provider} / {currentConversation.model_name}
              </div>
            </div>
          )}
        </div>

        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto">
          {conversations.map((conversation) => (
            <div
              key={conversation.id}
              onClick={() => setCurrentConversation(conversation)}
              className={`p-3 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                currentConversation?.id === conversation.id ? 'bg-blue-50 border-l-4 border-l-blue-500' : ''
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className={`inline-block px-2 py-1 rounded text-white text-xs mb-1 ${FUNCTION_COLORS[conversation.function_type as keyof typeof FUNCTION_COLORS]}`}>
                    {conversation.function_type.toUpperCase()}
                  </div>
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {conversation.title}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {conversation.message_count} mensagens
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteConversation(conversation.id);
                  }}
                  className="text-gray-400 hover:text-red-500 ml-2"
                  title="Deletar conversa"
                >
                  ×
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="mr-3 p-1 rounded-md hover:bg-gray-100"
            >
              ☰
            </button>
            {currentConversation && (
              <div>
                <h1 className="text-lg font-semibold text-gray-900">
                  {currentConversation.title}
                </h1>
                <p className="text-sm text-gray-500">
                  {FUNCTION_DESCRIPTIONS[currentConversation.function_type as keyof typeof FUNCTION_DESCRIPTIONS]}
                </p>
              </div>
            )}
          </div>
          
          {!currentConversation && (
            <button
              onClick={() => setShowNewChatModal(true)}
              className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition-colors"
            >
              Começar Conversa
            </button>
          )}
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.is_user ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl p-3 rounded-lg ${
                  message.is_user
                    ? 'bg-blue-500 text-white'
                    : 'bg-white border border-gray-200 text-gray-900'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                <div className={`text-xs mt-1 ${message.is_user ? 'text-blue-100' : 'text-gray-500'}`}>
                  {new Date(message.created_at).toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {/* Theme Actions */}
          {showThemeActions && parsedThemes && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h4 className="font-semibold text-yellow-800 mb-2">Temas Detectados!</h4>
              
              {parsedThemes.themes && (
                <div className="mb-3">
                  <p className="text-sm text-yellow-700 mb-2">Temas:</p>
                  <ul className="text-xs text-yellow-600 space-y-1">
                    {Object.entries(parsedThemes.themes).map(([key, value]) => (
                      <li key={key}>• {key}: {value as string}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              {parsedThemes.macro_name && (
                <p className="text-sm text-yellow-700 mb-3">
                  Nome do conjunto: <strong>{parsedThemes.macro_name}</strong>
                </p>
              )}
              
              <div className="flex space-x-2">
                <button
                  onClick={makeAdjustments}
                  className="bg-red-500 text-white px-3 py-1 rounded text-sm hover:bg-red-600 transition-colors"
                >
                  🔴 Fazer ajustes
                </button>
                <button
                  onClick={requestContent}
                  className="bg-green-500 text-white px-3 py-1 rounded text-sm hover:bg-green-600 transition-colors"
                >
                  🟢 Solicitar conteúdo
                </button>
              </div>
            </div>
          )}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white border border-gray-200 rounded-lg p-3 text-gray-500">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                  <span className="text-sm">Digitando...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        {currentConversation && (
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="flex space-x-2">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="Digite sua mensagem..."
                className="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isLoading}
              />
              <button
                onClick={sendMessage}
                disabled={isLoading || !inputMessage.trim()}
                className="bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Enviar
              </button>
            </div>
          </div>
        )}
      </div>

      {/* New Chat Modal */}
      {showNewChatModal && chatContext && (
        <NewChatModal
          chatContext={chatContext}
          brands={brands}
          onClose={() => setShowNewChatModal(false)}
          onCreate={createNewConversation}
        />
      )}
    </div>
  );
};

// New Chat Modal Component
interface NewChatModalProps {
  chatContext: ChatContext;
  brands: Brand[];
  onClose: () => void;
  onCreate: (data: any) => void;
}

const NewChatModal: React.FC<NewChatModalProps> = ({ chatContext, brands, onClose, onCreate }) => {
  const [title, setTitle] = useState('');
  const [functionType, setFunctionType] = useState('general');
  const [brandId, setBrandId] = useState('');
  const [modelProvider, setModelProvider] = useState('openai');
  const [modelName, setModelName] = useState('gpt-4o-mini');
  const [reference, setReference] = useState('ryb');
  const [apiKey, setApiKey] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const data = {
      title: title || `${functionType.charAt(0).toUpperCase() + functionType.slice(1)} - ${new Date().toLocaleDateString()}`,
      function_type: functionType,
      brand_id: brandId || undefined,
      model_provider: modelProvider,
      model_name: modelName,
      reference,
      api_key: apiKey || undefined
    };
    
    onCreate(data);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold mb-4">Nova Conversa</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Título (opcional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Título da conversa"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Função
            </label>
            <select
              value={functionType}
              onChange={(e) => setFunctionType(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {chatContext.available_functions.map((func) => (
                <option key={func} value={func}>
                  {func.charAt(0).toUpperCase() + func.slice(1)} - {FUNCTION_DESCRIPTIONS[func as keyof typeof FUNCTION_DESCRIPTIONS]}
                </option>
              ))}
            </select>
          </div>

          {(functionType === 'redacao' || functionType === 'oraculo') && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Marca
              </label>
              <select
                value={brandId}
                onChange={(e) => setBrandId(e.target.value)}
                className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Selecione uma marca</option>
                {brands.map((brand) => (
                  <option key={brand.id} value={brand.id}>
                    {brand.name}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Provedor do Modelo
            </label>
            <select
              value={modelProvider}
              onChange={(e) => {
                setModelProvider(e.target.value);
                const models = chatContext.available_models[e.target.value];
                setModelName(Object.keys(models)[0]);
              }}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.keys(chatContext.available_models).map((provider) => (
                <option key={provider} value={provider}>
                  {provider.charAt(0).toUpperCase() + provider.slice(1)}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Modelo
            </label>
            <select
              value={modelName}
              onChange={(e) => setModelName(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(chatContext.available_models[modelProvider] || {}).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Referência
            </label>
            <select
              value={reference}
              onChange={(e) => setReference(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {Object.entries(chatContext.available_references).map(([key, value]) => (
                <option key={key} value={key}>
                  {value}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Chave API (opcional)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Chave API personalizada"
            />
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 border border-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="flex-1 bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 transition-colors"
            >
              Criar Conversa
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ChatInterface; 