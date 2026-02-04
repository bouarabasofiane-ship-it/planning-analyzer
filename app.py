"""
Planning Analyzer - Application Streamlit
Analyse de plannings chantier avec détection automatique
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Import modules
from modules.planning_parser import PlanningParser, generate_demo_data
from modules.validators import PlanningValidator
from modules.analytics import PlanningAnalytics
from modules.exporters import PlanningExporter

# Configuration page
st.set_page_config(
    page_title="Planning Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-error {
        background-color: #ffebee;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #f44336;
    }
    .alert-warning {
        background-color: #fff3e0;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #ff9800;
    }
    .alert-info {
        background-color: #e3f2fd;
        padding: 0.5rem;
        border-radius: 0.3rem;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation session state
if 'df_planning' not in st.session_state:
    st.session_state.df_planning = None
if 'alerts' not in st.session_state:
    st.session_state.alerts = []
if 'kpis' not in st.session_state:
    st.session_state.kpis = {}
if 'excel_buffer' not in st.session_state:
    st.session_state.excel_buffer = None
if 'html_report' not in st.session_state:
    st.session_state.html_report = None

# SIDEBAR - CONFIGURATION
st.sidebar.title("⚙️ Configuration")

demo_mode = st.sidebar.checkbox("🔬 Mode démo (sans fichier)")

if not demo_mode:
    uploaded_file = st.sidebar.file_uploader(
        "📁 Charger un fichier Excel",
        type=['xlsx', 'xls'],
        help="Formats supportés: .xlsx, .xls"
    )
else:
    uploaded_file = None

st.sidebar.markdown("---")
st.sidebar.markdown("""
### 📖 À propos
**Planning Analyzer v1.0**

Analyse automatique de plannings chantier:
- ✅ Parsing intelligent
- ✅ Validation qualité
- ✅ KPI & métriques
- ✅ Visualisations interactives
- ✅ Exports multi-formats
""")

# HEADER
st.markdown('<h1 class="main-header">📊 Planning Analyzer</h1>', unsafe_allow_html=True)
st.markdown("**Analyse intelligente de plannings de chantier**")
st.markdown("---")

# CHARGEMENT DONNÉES
parser = PlanningParser()
validator = PlanningValidator()
analytics = PlanningAnalytics()
exporter = PlanningExporter()

if demo_mode:
    st.info("🔬 Mode démo activé - Chargement données de démonstration...")
    st.session_state.df_planning = generate_demo_data()
    st.success("✅ Planning de démonstration chargé")
    
elif uploaded_file is not None:
    try:
        with st.spinner("⏳ Parsing du fichier Excel..."):
            df = parser.parse_excel(uploaded_file)
            
            if df is not None and len(df) > 0:
                st.session_state.df_planning = df
                st.success(f"✅ Fichier chargé: {uploaded_file.name} ({len(df)} lignes)")
            else:
                st.error("❌ Erreur: Impossible de parser le fichier")
                st.session_state.df_planning = None
                
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {str(e)}")
        st.session_state.df_planning = None

# AFFICHAGE SI DONNÉES DISPONIBLES
if st.session_state.df_planning is not None:
    df = st.session_state.df_planning
    
    # Validation
    st.session_state.alerts = validator.validate(df)
    
    # KPI
    st.session_state.kpis = analytics.calculate_kpis(df)
    
    # SECTION 1: APERÇU & STRUCTURE
    st.header("1️⃣ Aperçu & Structure")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Lignes totales", len(df))
    
    with col2:
        blocs = df[df['level'] == 'bloc']['bloc'].nunique()
        st.metric("🏗️ BLOCs", blocs)
    
    with col3:
        phases = df[df['level'] == 'phase']['phase'].nunique()
        st.metric("📋 Phases", phases)
    
    with col4:
        taches = len(df[df['level'] == 'tache'])
        st.metric("✅ Tâches", taches)
    
    with st.expander("🔍 Structure détectée"):
        st.write("**Distribution hiérarchique:**")
        level_counts = df['level'].value_counts()
        st.dataframe(level_counts, use_container_width=True)
        
        st.write("**Colonnes détectées:**")
        st.write(df.columns.tolist())
    
    # SECTION 2: VALIDATION & QUALITÉ
    st.header("2️⃣ Validation & Contrôle Qualité")
    
    alert_summary = validator.get_summary(st.session_state.alerts)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔴 Erreurs", alert_summary['error'])
    
    with col2:
        st.metric("🟡 Avertissements", alert_summary['warning'])
    
    with col3:
        st.metric("🔵 Informations", alert_summary['info'])
    
    with col4:
        st.metric("📊 Total alertes", alert_summary['total'])
    
    if len(st.session_state.alerts) > 0:
        st.warning(f"⚠️ {len(st.session_state.alerts)} alerte(s) détectée(s)")
        
        with st.expander("📋 Détail des alertes"):
            for alert in st.session_state.alerts:
                severity = alert['severity']
                message = alert['message']
                
                if severity == 'error':
                    st.markdown(f'<div class="alert-error">🔴 {message}</div>', unsafe_allow_html=True)
                elif severity == 'warning':
                    st.markdown(f'<div class="alert-warning">🟡 {message}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-info">🔵 {message}</div>', unsafe_allow_html=True)
    else:
        st.success("✅ Aucune alerte - Planning conforme")
    
    # SECTION 3: KPI & MÉTRIQUES
    st.header("3️⃣ KPI & Métriques")
    
    kpis = st.session_state.kpis
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📅 Tâches totales", kpis.get('total_tasks', 0))
        st.metric("🎯 Tâches achevées", kpis.get('completed_tasks', 0))
    
    with col2:
        completion_rate = kpis.get('completion_rate', 0)
        st.metric("📊 Taux achèvement", f"{completion_rate:.1f}%")
        
        avg_duration = kpis.get('avg_duration', 0)
        st.metric("⏱️ Durée moyenne", f"{avg_duration:.1f} jours")
    
    with col3:
        total_value = kpis.get('total_value', 0)
        st.metric("💰 Valeur totale", f"{total_value/1e6:.1f}M")
        
        start_date = kpis.get('start_date')
        end_date = kpis.get('end_date')
        
        if start_date and end_date:
            st.metric("📆 Durée projet", f"{(end_date - start_date).days} jours")
    
    # KPI par BLOC
    if 'kpi_by_bloc' in kpis and len(kpis['kpi_by_bloc']) > 0:
        st.subheader("📊 KPI par BLOC")
        df_kpi_bloc = pd.DataFrame(kpis['kpi_by_bloc']).T
        st.dataframe(df_kpi_bloc, use_container_width=True)
    
    # Earned Value Management
    ev_metrics = analytics.calculate_earned_value(df)
    
    if ev_metrics:
        st.subheader("💰 Earned Value Management")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("PV (Planned)", f"{ev_metrics['planned_value']/1e6:.1f}M")
        
        with col2:
            st.metric("EV (Earned)", f"{ev_metrics['earned_value']/1e6:.1f}M")
        
        with col3:
            spi = ev_metrics.get('spi', 0)
            st.metric("SPI", f"{spi:.2f}")
        
        with col4:
            status = ev_metrics.get('status', 'N/A')
            st.metric("Statut", status)
    
    # SECTION 4: VISUALISATIONS
    st.header("4️⃣ Visualisations")
    
    # Filtres
    st.subheader("🎛️ Filtres")
    
    col1, col2 = st.columns(2)
    
    with col1:
        blocs_list = df[df['level'] == 'bloc']['bloc'].dropna().unique().tolist()
        selected_blocs = st.multiselect(
            "BLOCs",
            blocs_list,
            default=blocs_list
        )
    
    with col2:
        phases_list = df[df['level'] == 'phase']['phase'].dropna().unique().tolist()
        selected_phases = st.multiselect(
            "Phases",
            phases_list,
            default=phases_list
        )
    
    # Filtrage données
    df_filtered = df[df['level'] == 'tache'].copy()
    
    if selected_blocs:
        df_filtered = df_filtered[df_filtered['bloc'].isin(selected_blocs)]
    
    if selected_phases:
        df_filtered = df_filtered[df_filtered['phase'].isin(selected_phases)]
    
    df_filtered = df_filtered.dropna(subset=['start_date', 'end_date'])
    
    # Gantt Chart
    st.subheader("📊 Diagramme de Gantt")
    
    if len(df_filtered) > 0:
        gantt_data = analytics.prepare_gantt_data(df_filtered)
        
        fig = px.timeline(
            gantt_data,
            x_start='start_date',
            x_end='end_date',
            y='task',
            color='bloc',
            title=f"Planning Gantt ({len(gantt_data)} tâches)",
            hover_data=['duration', 'progress']
        )
        
        fig.update_yaxes(categoryorder='total ascending')
        fig.update_layout(height=max(400, len(gantt_data) * 30))
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Aucune donnée à afficher avec les filtres sélectionnés")
    
    # Distribution durées
    st.subheader("📊 Distribution des durées")
    
    df_duration = df[df['level'] == 'tache'].dropna(subset=['duration'])
    
    if len(df_duration) > 0:
        fig = px.histogram(
            df_duration,
            x='duration',
            nbins=20,
            title="Distribution des durées de tâches",
            labels={'duration': 'Durée (jours)', 'count': 'Nombre de tâches'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # SECTION 5: EXPORTS
    st.header("5️⃣ Exports")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Générer exports Excel"):
            with st.spinner("Génération Excel..."):
                try:
                    buffer_clean = exporter.export_to_excel(df)
                    st.session_state.excel_buffer = buffer_clean
                    
                    st.success("✅ Exports Excel générés")
                except Exception as e:
                    st.error(f"❌ Erreur export: {str(e)}")
        
        if st.session_state.excel_buffer:
            st.download_button(
                label="📊 Télécharger Planning nettoyé",
                data=st.session_state.excel_buffer,
                file_name=f"planning_clean_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        if st.button("🔄 Générer rapport HTML"):
            with st.spinner("Génération rapport..."):
                try:
                    html_content = exporter.export_to_html(
                        df,
                        st.session_state.alerts,
                        st.session_state.kpis
                    )
                    st.session_state.html_report = html_content
                    
                    st.success("✅ Rapport HTML généré")
                except Exception as e:
                    st.error(f"❌ Erreur rapport: {str(e)}")
        
        if st.session_state.html_report:
            st.download_button(
                label="📝 Télécharger Rapport HTML",
                data=st.session_state.html_report,
                file_name=f"rapport_planning_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html"
            )

else:
    st.info("""
    👋 **Bienvenue dans Planning Analyzer**
    
    Pour commencer:
    1. 🔬 Activez le **Mode démo** dans la barre latérale pour tester l'application
    2. 📁 Ou **chargez votre fichier Excel** de planning
    
    L'application détectera automatiquement la structure et générera les analyses.
    """)
    
    st.markdown("---")
    
    st.markdown("""
    ### 🎯 Fonctionnalités
    
    - ✅ **Parsing intelligent** - Détection automatique de structure
    - ✅ **Validation qualité** - 8 règles de contrôle
    - ✅ **KPI & métriques** - Calculs automatiques
    - ✅ **Visualisations** - Gantt interactif, graphiques
    - ✅ **Exports** - Excel, HTML, CSV
    """)
