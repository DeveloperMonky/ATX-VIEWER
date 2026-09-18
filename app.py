from flask import Flask, jsonify, render_template_string, request
import os

app = Flask(__name__)

# --- HTML INTEGRADO CON DRAG & DROP, BARRA DE BÚSQUEDA Y LA NUEVA UI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Visualizador ATX - Calibración de Antenas</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .drop-zone {
            border: 2px dashed #0d6efd;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background-color: #f8f9fa;
            cursor: pointer;
            transition: background-color 0.2s ease-in-out;
        }
        .drop-zone:hover, .drop-zone.dragover {
            background-color: #e9ecef;
        }
    </style>
</head>
<body class="bg-light">

    <div class="container mt-5 mb-5">
        <h2 class="mb-4 text-center">Visualizador de Archivos ATX</h2>
        
        <!-- Zona de Drag and Drop para cargar el archivo -->
        <div class="card shadow-sm mb-4">
            <div class="card-body">
                <div id="drop-zone" class="drop-zone">
                    <p class="mb-2 fs-5">📂 Arrastra y suelta tu archivo `.atx` aquí</p>
                    <p class="text-muted mb-3">o haz clic para seleccionarlo manualmente</p>
                    <input type="file" id="file-input" class="d-none" accept=".atx,.txt">
                    <button class="btn btn-outline-primary btn-sm" onclick="document.getElementById('file-input').click()">Examinar archivo</button>
                </div>
            </div>
        </div>

        <!-- Barra de búsqueda y Contenedor de la Tabla -->
        <div class="card shadow-sm">
            <div class="card-body">
                <div class="row mb-3">
                    <div class="col-md-6">
                        <input type="text" id="search-input" class="form-control" placeholder="🔍 Buscar por PRN, Bloque o Serial..." onkeyup="filterTable()">
                    </div>
                </div>

                <div class="table-responsive">
                    <table class="table table-striped table-hover align-middle">
                        <thead class="table-dark">
                            <tr>
                                <th>Block Type</th>
                                <th>PRN / Slot</th>
                                <th>Serial Number (SN)</th>
                                <th>Cospar ID (Type/Serial No)</th>
                                <th>Valid From</th>
                                <th>Valid Until</th>
                            </tr>
                        </thead>
                        <tbody id="atx-table-body">
                            <tr>
                                <td colspan="6" class="text-center text-muted">Sube un archivo ATX para ver los datos.</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        let allData = [];

        const dropZone = document.getElementById('drop-zone');
        const fileInput = document.getElementById('file-input');

        // Eventos de Drag & Drop
        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.add('dragover');
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                dropZone.classList.remove('dragover');
            }, false);
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadFile(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                uploadFile(e.target.files[0]);
            }
        });

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('file', file);

            const tbody = document.getElementById('atx-table-body');
            tbody.innerHTML = `<tr><td colspan="6" class="text-center">Procesando archivo...</td></tr>`;

            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                allData = data;
                renderTable(allData);
            })
            .catch(error => {
                console.error('Error:', error);
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error al procesar el archivo.</td></tr>`;
            });
        }

        function renderTable(data) {
            const tbody = document.getElementById('atx-table-body');
            tbody.innerHTML = '';

            if.length === 0) {
                tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No se encontraron registros.</td></tr>`;
                return;
            }

            data.forEach(item => {
                const row = `
                    <tr>
                        <td><span class="badge bg-secondary">${item.block_type || 'N/A'}</span></td>
                        <td><strong>${item.prn_slot || 'N/A'}</strong></td>
                        <td>${item.serial_number || 'N/A'}</td>
                        <td><code>${item.cospar_id || 'N/A'}</code></td>
                        <td>${item.valid_from || 'N/A'}</td>
                        <td>${item.valid_until || 'N/A'}</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            });
        }

        function filterTable() {
            const query = document.getElementById('search-input').value.toLowerCase();
            const filtered = allData.filter(item => {
                return (
                    (item.block_type && item.block_type.toLowerCase().includes(query)) ||
                    (item.prn_slot && item.prn_slot.toLowerCase().includes(query)) ||
                    (item.serial_number && item.serial_number.toLowerCase().includes(query)) ||
                    (item.cospar_id && item.cospar_id.toLowerCase().includes(query))
                );
            });
            renderTable(filtered);
        }
    </script>
</body>
</html>
"""

# --- LÓGICA DE PARSEO DEL ARCHIVO ATX ---
def parse_atx_content(file_stream):
    satellites = []
    current_sat = {}
    
    for line in file_stream:
        line_str = line.decode('utf-8', errors='ignore')
        if "START OF ANTENNA" in line_str:
            current_sat = {}
        elif "TYPE / SERIAL NO" in line_str:
            parts = line_str.split()
            current_sat['block_type'] = parts[3] if len(parts) > 3 else (parts[0] if len(parts) > 0 else "UNKNOWN")
            current_sat['serial_number'] = parts[1] if len(parts) > 1 else ""
            current_sat['cospar_id'] = parts[2] if len(parts) > 2 else ""
        elif "PRN / SLOT" in line_str:
            parts = line_str.split()
            current_sat['prn_slot'] = parts[0] if len(parts) > 0 else ""
        elif "VALID FROM" in line_str:
            current_sat['valid_from'] = line_str[:20].strip()
        elif "VALID UNTIL" in line_str:
            current_sat['valid_until'] = line_str[:20].strip()
        elif "END OF ANTENNA" in line_str:
            if 'valid_until' not in current_sat or not current_sat['valid_until']:
                current_sat['valid_until'] = "Present (Ongoing)"
            satellites.append(current_sat)
            
    return satellites

# --- RUTAS DE FLASK ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify([])
    file = request.files['file']
    if file.filename == '':
        return jsonify([])
    
    data = parse_atx_content(file.stream)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
