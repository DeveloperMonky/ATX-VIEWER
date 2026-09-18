import os
import re
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

# HTML + CSS + JS Integrado con un diseño moderno (Drag & Drop)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-adsense-account" content="ca-pub-6961767322971888">
    <title>Visualizador ANTEX (.atx) - IGS</title>
    
    <!-- Script de verificación de Google AdSense -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6961767322971888"
         crossorigin="anonymous"></script>

    <style>
        :root {
            --primary: #1b365d;
            --secondary: #00a8cc;
            --bg: #f4f6f8;
            --card-bg: #ffffff;
            --text: #2c3e50;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        header {
            background: linear-gradient(135deg, var(--primary), #2c3e50);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        header h1 { margin: 0; font-size: 22pt; }
        header p { margin: 5px 0 0; color: #dbe2ef; font-size: 10.5pt; }
        
        /* Zona Drag & Drop */
        .drop-zone {
            background-color: var(--card-bg);
            border: 3px dashed var(--secondary);
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .drop-zone.dragover {
            background-color: #e1eff6;
            border-color: var(--primary);
        }
        .drop-zone p {
            margin: 10px 0 0;
            font-size: 11pt;
            color: #555;
        }
        .drop-zone input { display: none; }
        
        /* Controles de búsqueda */
        .controls {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .controls input {
            flex: 1;
            padding: 10px 15px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 10pt;
        }
        
        /* Tarjetas de antenas */
        .antenna-list {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 15px;
            max-height: 600px;
            overflow-y: auto;
            padding-right: 5px;
        }
        .antenna-card {
            background: var(--card-bg);
            border-radius: 6px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 5px solid var(--secondary);
        }
        .antenna-card h3 {
            margin: 0 0 8px 0;
            font-size: 11pt;
            color: var(--primary);
            word-break: break-all;
        }
        .antenna-card p {
            margin: 4px 0;
            font-size: 9pt;
            color: #555;
        }
        .badge {
            background: #e1eff6;
            color: #0b5ed7;
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 8pt;
            font-weight: bold;
        }
        .loader {
            text-align: center;
            font-weight: bold;
            color: var(--primary);
            display: none;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Visualizador de Archivos ANTEX (.atx)</h1>
            <p>Servicio Internacional GNSS (IGS)</p>
        </header>

        <!-- Zona Drag & Drop -->
        <div id="dropZone" class="drop-zone">
            <svg width="48" height="48" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" style="color: var(--secondary);">
                <path stroke-linecap="round" stroke-linejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"></path>
            </svg>
            <p><strong>Arrastra y suelta tu archivo .atx aquí</strong> o haz clic para seleccionarlo</p>
            <input type="file" id="fileInput" accept=".atx,.TXT">
        </div>

        <div id="loader" class="loader">Procesando archivo ANTEX, por favor espera...</div>

        <!-- Bloque de Anuncio de Google AdSense -->
        <div style="text-align: center; margin: 20px 0;">
            <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6961767322971888"
                 crossorigin="anonymous"></script>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-6961767322971888"
                 data-ad-slot="AQUÍ_EL_ID_DE_TU_BLOQUE_DE_ANUNCIO"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>

        <div id="resultsContainer" style="display: none;">
            <div class="controls">
                <input type="text" id="searchInput" placeholder="Filtrar por nombre de antena o número de serie..." onkeyup="filterAntennas()">
            </div>
            <div id="antennaCount" style="margin-bottom: 10px; font-weight: bold; font-size: 9.5pt;"></div>
            <div class="antenna-list" id="antennaList"></div>
        </div>
    </div>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const loader = document.getElementById('loader');
        const resultsContainer = document.getElementById('resultsContainer');
        const antennaList = document.getElementById('antennaList');
        const searchInput = document.getElementById('searchInput');
        const antennaCount = document.getElementById('antennaCount');

        let allAntennas = [];

        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length) {
                handleFile(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length) {
                handleFile(e.target.files[0]);
            }
        });

        function handleFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            loader.style.display = 'block';
            resultsContainer.style.display = 'none';

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                loader.style.display = 'none';
                if (data.error) {
                    alert('Error: ' + data.error);
                    return;
                }
                allAntennas = data.antennas;
                renderAntennas(allAntennas);
                resultsContainer.style.display = 'block';
            })
            .catch(err => {
                loader.style.display = 'none';
                alert('Ocurrió un error al procesar el archivo.');
                console.error(err);
            });
        }

        function renderAntennas(antennas) {
            antennaList.innerHTML = '';
            antennaCount.innerText = `Total de antenas encontradas: ${antennas.length}`;
            
            antennas.forEach(ant => {
                const card = document.createElement('div');
                card.className = 'antenna-card';
                card.innerHTML = `
                    <h3>${ant.name}</h3>
                    <p><strong>Modelo / Radomo:</strong> <span class="badge">${ant.radome || 'NINGUNO'}</span></p>
                    <p><strong>N/S:</strong> ${ant.serial_number || 'N/D'}</p>
                    <p><strong>Calibración:</strong> ${ant.calibration_method || 'N/D'}</p>
                `;
                antennaList.appendChild(card);
            });
        }

        function filterAntennas() {
            const query = searchInput.value.toLowerCase();
            const filtered = allAntennas.filter(ant => 
                ant.name.toLowerCase().includes(query) || 
                (ant.serial_number && ant.serial_number.toLowerCase().includes(query)) ||
                (ant.radome && ant.radome.toLowerCase().includes(query))
            );
            renderAntennas(filtered);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)
@app.route('/ads.txt')
def ads_txt():
    # Reemplaza esta línea con el texto exacto que te pide Google AdSense en su panel
    return "google.com, pub-6961767322971888, DIRECT, f08c47fec0942fa0"

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No se encontró ningún archivo'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Archivo no seleccionado'}), 400

    try:
        content = file.read().decode('utf-8', errors='ignore')
        antennas = []
        
        current_antenna = {}
        for line in content.splitlines():
            if 'START OF ANTENNA' in line:
                current_antenna = {'name': '', 'serial_number': '', 'radome': '', 'calibration_method': ''}
            elif 'END OF ANTENNA' in line:
                if current_antenna:
                    antennas.append(current_antenna)
                current_antenna = {}
            elif current_antenna is not None:
                if 'TYPE / SERIAL NO' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        current_antenna['name'] = parts[0]
                        current_antenna['radome'] = parts[1] if len(parts) > 1 else ''
                    if len(parts) >= 3:
                        current_antenna['serial_number'] = " ".join(parts[2:])
                elif 'METH / BY / # / PCV' in line:
                    current_antenna['calibration_method'] = line[:20].strip()

        return jsonify({'antennas': antennas})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Iniciando servidor web en http://localhost:1209")
    app.run(host='0.0.0.0', port=1209, debug=False)
