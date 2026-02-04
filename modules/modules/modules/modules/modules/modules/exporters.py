"""
Module d'export (Excel, HTML, CSV)
"""

import pandas as pd
from datetime import datetime
import io

class PlanningExporter:
    """Exporteur multi-formats"""
    
    def export_to_excel(self, df):
        """
        Exporte vers Excel avec mise en forme
        
        Returns:
            BytesIO buffer
        """
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            # Onglet données complètes
            df.to_excel(writer, sheet_name='Planning Complet', index=False)
            
            # Onglet tâches uniquement
            tasks = df[df['level'] == 'tache']
            tasks.to_excel(writer, sheet_name='Tâches', index=False)
            
            # Onglet synthèse par BLOC
            if 'bloc' in df.columns:
                blocs = df[df['level'] == 'bloc'][['bloc']].drop_duplicates()
                blocs.to_excel(writer, sheet_name='BLOCs', index=False)
            
            # Mise en forme
            workbook = writer.book
            
            # Format dates
            date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
            
            # Format pourcentage
            percent_format = workbook.add_format({'num_format': '0%'})
            
            # Appliquer formats
            worksheet = writer.sheets['Planning Complet']
            worksheet.set_column('D:E', 12, date_format)
        
        buffer.seek(0)
        return buffer
    
    def export_to_html(self, df, alerts, kpis):
        """
        Génère rapport HTML complet
        
        Returns:
            HTML string
        """
        html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport Planning - {datetime.now().strftime('%Y-%m-%d')}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1f77b4;
            border-bottom: 3px solid #1f77b4;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #333;
            margin-top: 30px;
        }}
        .kpi-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .kpi-card {{
            background: #f0f8ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #1f77b4;
        }}
        .kpi-value {{
            font-size: 2em;
            font-weight: bold;
            color: #1f77b4;
        }}
        .kpi-label {{
            color: #666;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #1f77b4;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .alert {{
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .alert-error {{
            background-color: #ffebee;
            border-left: 4px solid #f44336;
        }}
        .alert-warning {{
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .alert-info {{
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Rapport d'Analyse Planning</h1>
        <p><strong>Date génération:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        
        <h2>📈 KPI Principaux</h2>
        <div class="kpi-grid">
            <div class="kpi-card">
                <div class="kpi-value">{kpis.get('total_tasks', 0)}</div>
                <div class="kpi-label">Tâches totales</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpis.get('completed_tasks', 0)}</div>
                <div class="kpi-label">Tâches achevées</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpis.get('completion_rate', 0):.1f}%</div>
                <div class="kpi-label">Taux achèvement</div>
            </div>
            <div class="kpi-card">
                <div class="kpi-value">{kpis.get('total_value', 0)/1e6:.1f}M</div>
                <div class="kpi-label">Valeur totale</div>
            </div>
        </div>
        
        <h2>⚠️ Alertes & Validation</h2>
        <p><strong>Total alertes:</strong> {len(alerts)}</p>
        """
        
        # Alertes
        for alert in alerts[:20]:  # Limite 20 alertes
            severity = alert['severity']
            message = alert['message']
            html += f'<div class="alert alert-{severity}">{message}</div>\n'
        
        # Tableau tâches
        tasks = df[df['level'] == 'tache'].head(50)
        
        html += """
        <h2>📋 Tâches (échantillon)</h2>
        <table>
            <tr>
                <th>BLOC</th>
                <th>Phase</th>
                <th>Tâche</th>
                <th>Début</th>
                <th>Fin</th>
                <th>Durée</th>
                <th>Avancement</th>
            </tr>
        """
        
        for idx, row in tasks.iterrows():
            html += f"""
            <tr>
                <td>{row.get('bloc', 'N/A')}</td>
                <td>{row.get('phase', 'N/A')}</td>
                <td>{row.get('task_name', 'N/A')}</td>
                <td>{row.get('start_date', 'N/A')}</td>
                <td>{row.get('end_date', 'N/A')}</td>
                <td>{row.get('duration', 'N/A')}</td>
                <td>{row.get('progress', 0):.0f}%</td>
            </tr>
            """
        
        html += """
        </table>
        
        <div class="footer">
            <p>Rapport généré par Planning Analyzer</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html
