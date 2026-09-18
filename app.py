from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# --- HTML INTEGRADO EN EL MISMO ARCHIVO ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Calibración de Antenas ATX</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

    <div class="container mt-5">
        <h2 class="mb-4">Visualizador de Datos ATX</h2>
        
        <div class="card shadow-sm">
            <div class="card-body">
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
                                <td colspan="6" class="text-center">Cargando datos...</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function loadAntennaData() {
            try {
                const response = await fetch('/api/antennas');
                const data = await response.json();
                
                const tbody = document.getElementById('atx-table-body');
                tbody.innerHTML = '';

                if (data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No se encontraron registros o el archivo está vacío.</td></tr>`;
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
            } catch (error) {
                console.error('Error al cargar los datos:', error);
                document.getElementById('atx-table-body').innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error al conectar con el servidor.</td></tr>`;
            }
        }

        document.addEventListener('DOMContentLoaded', loadAntennaData);
    </script>

</body>
</html>
"""

# --- LÓGICA DE PARSEO DEL ARCHIVO ATX ---
def parse_atx_file(file_path):
    satellites = []
    current_sat = {}
    
    if not os.path.exists(file_path):
        return satellites

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if "START OF ANTENNA" in line:
                current_sat = {}
            elif "TYPE / SERIAL NO" in line:
                parts = line.split()
                current_sat['block_type'] = parts[3] if len(parts) > 3 else (parts[0] if len(parts) > 0 else "UNKNOWN")
                current_sat['serial_number'] = parts[1] if len(parts) > 1 else ""
                current_sat['cospar_id'] = parts[2] if len(parts) > 2 else ""
            elif "PRN / SLOT" in line:
                parts = line.split()
                current_sat['prn_slot'] = parts[0] if len(parts) > 0 else ""
            elif "VALID FROM" in line:
                current_sat['valid_from'] = line[:20].strip()
            elif "VALID UNTIL" in line:
                current_sat['valid_until'] = line[:20].strip()
            elif "END OF ANTENNA" in line:
                if 'valid_until' not in current_sat or not current_sat['valid_until']:
                    current_sat['valid_until'] = "Present (Ongoing)"
                satellites.append(current_sat)
                
    return satellites

# --- RUTAS DE FLASK ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/antennas')
def get_antennas():
    # Cambia 'igs.atx' por la ruta real de tu archivo de calibración
    file_path = 'igs.atx' 
    data = parse_atx_file(file_path)
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
