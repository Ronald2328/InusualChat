// Variables globales
let chatContainer = null;
let isExpanded = false;
const serverUrl = "http://localhost:5000";

// Función para crear la burbuja de chat
function createChatBubble() {
  // Crear el contenedor principal
  chatContainer = document.createElement('div');
  chatContainer.className = 'chat-assistant-container';
  
  // Crear el botón de la burbuja
  const chatBubble = document.createElement('div');
  chatBubble.className = 'chat-assistant-bubble';
  chatBubble.innerHTML = '💬';
  
  // Crear el panel de chat (inicialmente oculto)
  const chatPanel = document.createElement('div');
  chatPanel.className = 'chat-assistant-panel hidden';
  
  // Añadir el título al panel
  const panelHeader = document.createElement('div');
  panelHeader.className = 'chat-assistant-header';
  panelHeader.innerHTML = '<span>Asistente de Chat</span><button class="chat-assistant-close">×</button>';
  
  // Añadir el área de conversación
  const chatMessages = document.createElement('div');
  chatMessages.className = 'chat-assistant-messages';
  
  // Añadir mensaje de bienvenida
  const welcomeMessage = document.createElement('div');
  welcomeMessage.className = 'chat-assistant-message assistant';
  welcomeMessage.textContent = 'Explora lo inusual, el dato escondido… responderé, aunque no lo sé todo, te lo digo.';
  chatMessages.appendChild(welcomeMessage);
  
  // Añadir el formulario de entrada
  const inputForm = document.createElement('form');
  inputForm.className = 'chat-assistant-input-form';
  
  const textInput = document.createElement('input');
  textInput.type = 'text';
  textInput.className = 'chat-assistant-input';
  textInput.placeholder = 'Escribe tu pregunta aquí...';
  
  const sendButton = document.createElement('button');
  sendButton.type = 'submit';
  sendButton.className = 'chat-assistant-send';
  sendButton.textContent = '➤';
  
  // Armar la estructura del DOM
  inputForm.appendChild(textInput);
  inputForm.appendChild(sendButton);
  
  chatPanel.appendChild(panelHeader);
  chatPanel.appendChild(chatMessages);
  chatPanel.appendChild(inputForm);
  
  chatContainer.appendChild(chatBubble);
  chatContainer.appendChild(chatPanel);
  
  document.body.appendChild(chatContainer);
  
  // Añadir event listeners
  chatBubble.addEventListener('click', toggleChat);
  panelHeader.querySelector('.chat-assistant-close').addEventListener('click', toggleChat);
  inputForm.addEventListener('submit', handleSubmit);
}

// Función para alternar la visibilidad del chat
function toggleChat(e) {
  e.preventDefault();
  const panel = document.querySelector('.chat-assistant-panel');
  isExpanded = !isExpanded;
  
  if (isExpanded) {
    panel.classList.remove('hidden');
  } else {
    panel.classList.add('hidden');
  }
}

// Función para manejar el envío de preguntas
async function handleSubmit(e) {
  e.preventDefault();
  
  const input = document.querySelector('.chat-assistant-input');
  const question = input.value.trim();
  
  if (!question) return;
  
  // Añadir la pregunta del usuario al chat
  addMessage(question, 'user');
  input.value = '';
  
  // Añadir mensaje de "pensando"
  const thinkingId = "thinking-" + Date.now();
  addThinkingMessage(thinkingId);
  
  try {
    // Obtener el contenido de la página
    const pageContent = document.body.innerText.substring(0, 5000); // Limitamos para evitar problemas
    
    // Enviar al servidor Flask
    const response = await fetch(`${serverUrl}/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: question,
        content: pageContent
      })
    });
    
    if (!response.ok) {
      throw new Error(`Error en el servidor: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Eliminar el mensaje de "pensando"
    removeThinkingMessage(thinkingId);
    
    // Añadir la respuesta al chat
    addMessage(data.response, 'assistant');
    
  } catch (error) {
    // Eliminar el mensaje de "pensando"
    removeThinkingMessage(thinkingId);
    
    // Añadir mensaje de error
    addMessage('Hmmm hay un error, parece que el universo no quiere que sepas esto. Prueba preguntarle a tu almohada.');
  }
}

// Función para añadir un mensaje al chat
function addMessage(text, sender) {
  const messages = document.querySelector('.chat-assistant-messages');
  const message = document.createElement('div');
  message.className = `chat-assistant-message ${sender}`;

  message.innerHTML = text;

  // Añadir el mensaje al chat
  messages.appendChild(message);

  // Scroll al final de los mensajes
  messages.scrollTop = messages.scrollHeight;
}

// Función para añadir un mensaje de "pensando"
function addThinkingMessage(id) {
  const messages = document.querySelector('.chat-assistant-messages');
  const message = document.createElement('div');
  message.className = 'chat-assistant-message assistant thinking';
  message.innerHTML = '<div class="thinking-dots"><span>.</span><span>.</span><span>.</span></div>';
  message.id = id;
  messages.appendChild(message);
  
  // Scroll al final de los mensajes
  messages.scrollTop = messages.scrollHeight;
}

// Función para eliminar el mensaje de "pensando"
function removeThinkingMessage(id) {
  const message = document.getElementById(id);
  if (message) {
    message.remove();
  }
}

// Inicia directamente en todas las páginas
createChatBubble();