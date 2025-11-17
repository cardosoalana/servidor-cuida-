<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Monitoramento Geriátrico | Profissional</title>
    <!-- Carrega Tailwind CSS para estilização rápida e responsiva -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        /* Definindo a paleta de cores (Salmão e neutros) */
        :root {
            --color-salmon-light: #FFDAB9; /* Salmão Claro */
            --color-salmon-mid: #FA8072;   /* Salmão Padrão */
            --color-red-alert: #EF4444;    /* Vermelho de Alerta */
            --color-yellow-alert: #F59E0B; /* Amarelo de Pânico */
            --color-text-dark: #374151;    /* Texto Escuro */
        }

        body { 
            font-family: 'Inter', sans-serif; 
            background-color: #f8f8f8; 
        }
        .card { 
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06); 
        }
        /* Destaque para Queda: Salmão escuro e borda sólida */
        .fall-alert { 
            background-color: #ffe4e1; /* Cor de fundo suave */
            border-left: 5px solid var(--color-red-alert); 
        }
        /* Destaque para Pânico: Amarelo suave e borda sólida */
        .panic-alert { 
            background-color: #fff8e1;
            border-left: 5px solid var(--color-yellow-alert); 
        }
        .header-bg {
             background-color: var(--color-salmon-mid);
        }
    </style>
</head>
<body class="p-4 md:p-10">

    <!-- Cabeçalho Principal e Logo -->
    <header class="header-bg text-white rounded-t-lg p-6 text-center shadow-lg">
        <div class="max-w-4xl mx-auto flex items-center justify-center">
            <!-- Logo Placeholder Profissional (SVG Simples) -->
            <svg class="w-8 h-8 mr-3 text-white" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
            </svg>
            <h1 class="text-3xl font-bold tracking-tight">Cuida + | Monitoramento de Quedas </h1>
        </div>
        <!-- Removido o subtítulo anterior que mencionava a ABB -->
    </header>

    <!-- Status Atual e Contagem -->
    <div class="mb-8 p-4 bg-white rounded-b-lg card border-t-4 border-gray-200">
        <h2 class="text-xl font-semibold text-gray-700 mb-2">Painel de Status</h2>
        <p class="text-sm text-gray-600">Última atualização: <span id="last-update" class="font-medium">--</span></p>
        <p class="mt-2 text-lg">Total de Eventos Registrados: <span id="total-events" class="font-bold text-gray-800">0</span></p>
    </div>

    <!-- Tabela de Eventos -->
    <div class="bg-white rounded-lg card overflow-hidden">
        <div class="p-4 header-bg text-white">
            <h2 class="text-xl font-semibold">Histórico de Eventos Registrados</h2>
            <!-- Título da tabela simplificado para Histórico de Eventos Registrados -->
        </div>
        <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                    <tr>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Data/Hora (Registro)</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tipo de Evento</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Localização GPS</th>
                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Aceleração Máxima</th>
                    </tr>
                </thead>
                <tbody id="events-table-body" class="bg-white divide-y divide-gray-200">
                    <tr>
                        <td colspan="4" class="text-center py-4 text-gray-500">Aguardando dados do ESP32...</td>
                    </tr>
                </tbody>
            </table>
        </div>
        <div id="loading-indicator" class="text-center py-4 text-gray-500 hidden">Carregando dados...</div>
    </div>
    
    <!-- Lógica JavaScript -->
    <script>
        const API_URL = '/api/eventos'; 
        const tableBody = document.getElementById('events-table-body');
        const totalEventsSpan = document.getElementById('total-events');
        const lastUpdateSpan = document.getElementById('last-update');
        const placeholderRow = '<tr><td colspan="4" class="text-center py-4 text-gray-500">Nenhum evento registrado.</td></tr>';

        function formatTimestamp(timestamp) {
            const date = new Date(timestamp * 1000); 
            return date.toLocaleString('pt-BR');
        }

        function formatEventType(type) {
            if (type === 'queda') {
                // Fundo vermelho escuro para Queda
                return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-600 text-white">QUEDA GRAVE</span>';
            }
            if (type === 'panico') {
                // Fundo amarelo/laranja para Pânico
                return '<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-500 text-white">PÂNICO MANUAL</span>';
            }
            return type;
        }

        function renderTable(events) {
            tableBody.innerHTML = '';
            
            if (events.length === 0) {
                 tableBody.innerHTML = placeholderRow;
                 totalEventsSpan.textContent = 0;
                 return;
            }

            // Reverte a ordem para que os eventos MAIS RECENTES fiquem no topo da tabela
            events.reverse();

            events.forEach(event => {
                const row = tableBody.insertRow();
                
                let rowClass = 'hover:bg-gray-50';
                if (event.data.tipo === 'queda') {
                    rowClass = 'fall-alert hover:bg-red-50';
                } else if (event.data.tipo === 'panico') {
                    rowClass = 'panic-alert hover:bg-yellow-50';
                }
                row.className = rowClass;

                // Célula 1: Data e Hora
                const dateCell = row.insertCell();
                dateCell.className = "px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900";
                dateCell.textContent = formatTimestamp(event.key);

                // Célula 2: Tipo de Evento (Formatado com cores)
                const typeCell = row.insertCell();
                typeCell.className = "px-6 py-4 whitespace-nowrap";
                typeCell.innerHTML = formatEventType(event.data.tipo);
                
                // Célula 3: Localização
                const locationCell = row.insertCell();
                locationCell.className = "px-6 py-4 whitespace-nowrap text-sm text-gray-500";
                locationCell.innerHTML = 
                    `<a href="https://www.google.com/maps/search/?api=1&query=${event.data.lat},${event.data.lon}" target="_blank" class="text-blue-600 hover:text-blue-800 underline">
                        ${event.data.lat}, ${event.data.lon}
                    </a>`;

                // Célula 4: Aceleração
                const acelCell = row.insertCell();
                acelCell.className = "px-6 py-4 whitespace-nowrap text-sm font-bold text-gray-700";
                acelCell.textContent = event.data.acel;
            });

            totalEventsSpan.textContent = events.length;
            lastUpdateSpan.textContent = new Date().toLocaleTimeString('pt-BR');
        }

        async function fetchEvents() {
            try {
                const response = await fetch(API_URL);
                const result = await response.json();
                
                if (result && result.eventos) {
                    renderTable(result.eventos);
                }
            } catch (error) {
                console.error("Erro ao buscar eventos da ABB:", error);
            }
        }

        // 1. Executa a função imediatamente ao carregar a página
        fetchEvents();

        // 2. Define o intervalo de atualização (Polling) a cada 2 segundos
        setInterval(fetchEvents, 2000); 
    </script>
</body>
</html>
