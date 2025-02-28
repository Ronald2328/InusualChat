document.addEventListener('DOMContentLoaded', function() {
    const serverStatus = document.getElementById('server-status');
    
    // Función para verificar el estado del servidor Flask
    function checkServerStatus() {
      fetch('http://localhost:5000/status')
        .then(response => {
          if (response.ok) {
            return response.json();
          }
          throw new Error('Server not available');
        })
        .then(data => {
          serverStatus.textContent = 'Estado del servidor: Conectado ✅';
          serverStatus.style.color = 'green';
        })
        .catch(error => {
          serverStatus.innerHTML = 'Estado del servidor: No conectado ❌<br>Asegúrate de ejecutar el servidor Flask en http://localhost:5000';
          serverStatus.style.color = 'red';
        });
    }
    
    // Verificar el estado del servidor al cargar
    checkServerStatus();
    
    // Verificar el estado cada 5 segundos
    setInterval(checkServerStatus, 5000);
  });