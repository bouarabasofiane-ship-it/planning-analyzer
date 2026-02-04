"""
Module de validation de planning
Vérifie la cohérence et la qualité des données
"""

import pandas as pd
from datetime import datetime

class PlanningValidator:
    """Validateur de planning avec règles métier"""
    
    def __init__(self):
        self.rules = [
            self._check_missing_dates,
            self._check_duration_coherence,
            self._check_progress_range,
            self._check_date_order,
            self._check_orphan_tasks,
            self._check_overlapping_tasks,
            self._check_missing_values,
            self._check_future_progress
        ]
    
    def validate(self, df):
        """
        Exécute toutes les règles de validation
        
        Args:
            df: DataFrame à valider
            
        Returns:
            Liste d'alertes {'severity': str, 'message': str, 'row': int}
        """
        alerts = []
        
        for rule in self.rules:
            rule_alerts = rule(df)
            alerts.extend(rule_alerts)
        
        return alerts
    
    def _check_missing_dates(self, df):
        """Vérifie les dates manquantes sur tâches"""
        alerts = []
        
        tasks = df[df['level'] == 'tache']
        
        for idx, row in tasks.iterrows():
            if pd.isna(row.get('start_date')):
                alerts.append({
                    'severity': 'error',
                    'message': f"Date début manquante: {row.get('task_name', 'N/A')}",
                    'row': idx
                })
            
            if pd.isna(row.get('end_date')):
                alerts.append({
                    'severity': 'error',
                    'message': f"Date fin manquante: {row.get('task_name', 'N/A')}",
                    'row': idx
                })
        
        return alerts
    
    def _check_duration_coherence(self, df):
        """Vérifie cohérence durée vs dates"""
        alerts = []
        
        tasks = df[df['level'] == 'tache'].copy()
        tasks = tasks.dropna(subset=['start_date', 'end_date', 'duration'])
        
        for idx, row in tasks.iterrows():
            calc_duration = (row['end_date'] - row['start_date']).days
            stated_duration = row['duration']
            
            if abs(calc_duration - stated_duration) > 1:
                alerts.append({
                    'severity': 'warning',
                    'message': f"Incohérence durée: {row.get('task_name')} (calculé: {calc_duration}j, indiqué: {stated_duration}j)",
                    'row': idx
                })
        
        return alerts
    
    def _check_progress_range(self, df):
        """Vérifie que progress est entre 0 et 100"""
        alerts = []
        
        tasks = df[df['level'] == 'tache'].dropna(subset=['progress'])
        
        for idx, row in tasks.iterrows():
            progress = row['progress']
            
            if progress < 0 or progress > 100:
                alerts.append({
                    'severity': 'error',
                    'message': f"Avancement invalide ({progress}%): {row.get('task_name')}",
                    'row': idx
                })
        
        return alerts
    
    def _check_date_order(self, df):
        """Vérifie que date début < date fin"""
        alerts = []
        
        tasks = df[df['level'] == 'tache'].dropna(subset=['start_date', 'end_date'])
        
        for idx, row in tasks.iterrows():
            if row['start_date'] >= row['end_date']:
                alerts.append({
                    'severity': 'error',
                    'message': f"Date fin avant date début: {row.get('task_name')}",
                    'row': idx
                })
        
        return alerts
    
    def _check_orphan_tasks(self, df):
        """Vérifie que toutes les tâches ont un BLOC et une Phase"""
        alerts = []
        
        tasks = df[df['level'] == 'tache']
        
        for idx, row in tasks.iterrows():
            if pd.isna(row.get('bloc')):
                alerts.append({
                    'severity': 'warning',
                    'message': f"Tâche sans BLOC: {row.get('task_name')}",
                    'row': idx
                })
            
            if pd.isna(row.get('phase')):
                alerts.append({
                    'severity': 'info',
                    'message': f"Tâche sans Phase: {row.get('task_name')}",
                    'row': idx
                })
        
        return alerts
    
    def _check_overlapping_tasks(self, df):
        """Détecte les chevauchements de tâches dans une même phase"""
        alerts = []
        
        tasks = df[df['level'] == 'tache'].dropna(subset=['phase', 'start_date', 'end_date'])
        
        for phase in tasks['phase'].unique():
            phase_tasks = tasks[tasks['phase'] == phase].sort_values('start_date')
            
            for i in range(len(phase_tasks) - 1):
                current = phase_tasks.iloc[i]
                next_task = phase_tasks.iloc[i + 1]
                
                if current['end_date'] > next_task['start_date']:
                    alerts.append({
                        'severity': 'info',
                        'message': f"Chevauchement: {current['task_name']} et {next_task['task_name']}",
                        'row': current.name
                    })
        
        return alerts
    
    def _check_missing_values(self, df):
        """Vérifie les valeurs financières manquantes"""
        alerts = []
        
        tasks = df[df['level'] == 'tache']
        missing_count = tasks['value'].isna().sum()
        
        if missing_count > 0:
            alerts.append({
                'severity': 'info',
                'message': f"{missing_count} tâches sans valeur financière",
                'row': None
            })
        
        return alerts
    
    def _check_future_progress(self, df):
        """Détecte les tâches futures avec avancement > 0"""
        alerts = []
        
        today = pd.Timestamp(datetime.now().date())
        tasks = df[df['level'] == 'tache'].dropna(subset=['start_date', 'progress'])
        
        for idx, row in tasks.iterrows():
            if row['start_date'] > today and row['progress'] > 0:
                alerts.append({
                    'severity': 'warning',
                    'message': f"Tâche future avec avancement: {row.get('task_name')} ({row['progress']}%)",
                    'row': idx
                })
        
        return alerts
    
    def get_summary(self, alerts):
        """Résumé des alertes par sévérité"""
        summary = {
            'error': 0,
            'warning': 0,
            'info': 0,
            'total': len(alerts)
        }
        
        for alert in alerts:
            severity = alert['severity']
            summary[severity] = summary.get(severity, 0) + 1
        
        return summary
