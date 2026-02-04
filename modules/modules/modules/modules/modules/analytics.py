"""
Module d'analytics et calcul de KPI
"""

import pandas as pd
import numpy as np
from datetime import datetime

class PlanningAnalytics:
    """Calcul de KPI et métriques de planning"""
    
    def calculate_kpis(self, df):
        """
        Calcule les KPI principaux
        
        Returns:
            dict avec métriques clés
        """
        kpis = {}
        
        tasks = df[df['level'] == 'tache']
        
        # Métriques de base
        kpis['total_tasks'] = len(tasks)
        kpis['completed_tasks'] = len(tasks[tasks['progress'] == 100])
        
        # Taux achèvement
        if kpis['total_tasks'] > 0:
            kpis['completion_rate'] = (kpis['completed_tasks'] / kpis['total_tasks']) * 100
        else:
            kpis['completion_rate'] = 0
        
        # Durée moyenne
        tasks_with_duration = tasks.dropna(subset=['duration'])
        if len(tasks_with_duration) > 0:
            kpis['avg_duration'] = tasks_with_duration['duration'].mean()
        else:
            kpis['avg_duration'] = 0
        
        # Valeur totale
        tasks_with_value = tasks.dropna(subset=['value'])
        kpis['total_value'] = tasks_with_value['value'].sum()
        
        # Dates projet
        tasks_with_dates = tasks.dropna(subset=['start_date', 'end_date'])
        if len(tasks_with_dates) > 0:
            kpis['start_date'] = tasks_with_dates['start_date'].min()
            kpis['end_date'] = tasks_with_dates['end_date'].max()
        
        # KPI par BLOC
        kpis['kpi_by_bloc'] = self._kpi_by_bloc(df)
        
        return kpis
    
    def _kpi_by_bloc(self, df):
        """Calcule KPI par BLOC"""
        tasks = df[df['level'] == 'tache']
        
        kpi_bloc = {}
        
        for bloc in tasks['bloc'].dropna().unique():
            bloc_tasks = tasks[tasks['bloc'] == bloc]
            
            kpi_bloc[bloc] = {
                'total_tasks': len(bloc_tasks),
                'completed': len(bloc_tasks[bloc_tasks['progress'] == 100]),
                'completion_rate': (len(bloc_tasks[bloc_tasks['progress'] == 100]) / len(bloc_tasks) * 100) if len(bloc_tasks) > 0 else 0,
                'avg_progress': bloc_tasks['progress'].mean() if 'progress' in bloc_tasks.columns else 0,
                'total_value': bloc_tasks['value'].sum() if 'value' in bloc_tasks.columns else 0
            }
        
        return kpi_bloc
    
    def calculate_earned_value(self, df):
        """
        Calcule les métriques Earned Value Management
        
        Returns:
            dict avec PV, EV, AC, SPI, CPI
        """
        tasks = df[df['level'] == 'tache'].dropna(subset=['value', 'progress'])
        
        if len(tasks) == 0:
            return None
        
        # Planned Value (budget total)
        pv = tasks['value'].sum()
        
        # Earned Value (valeur réalisée)
        ev = (tasks['value'] * tasks['progress'] / 100).sum()
        
        # Schedule Performance Index
        spi = ev / pv if pv > 0 else 0
        
        # Statut
        if spi >= 1.0:
            status = "En avance"
        elif spi >= 0.9:
            status = "Dans les temps"
        else:
            status = "En retard"
        
        return {
            'planned_value': pv,
            'earned_value': ev,
            'spi': spi,
            'status': status
        }
    
    def prepare_gantt_data(self, df):
        """Prépare données pour diagramme Gantt"""
        tasks = df[df['level'] == 'tache'].dropna(subset=['start_date', 'end_date'])
        
        gantt_data = []
        
        for idx, row in tasks.iterrows():
            gantt_data.append({
                'task': row.get('task_name', 'N/A'),
                'start_date': row['start_date'],
                'end_date': row['end_date'],
                'duration': row.get('duration', 0),
                'progress': row.get('progress', 0),
                'bloc': row.get('bloc', 'Sans BLOC'),
                'phase': row.get('phase', 'Sans phase')
            })
        
        return pd.DataFrame(gantt_data)
