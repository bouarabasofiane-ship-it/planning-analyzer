"""
Module de parsing des fichiers Excel de planning
Détecte automatiquement la structure hiérarchique (BLOC > Phase > Tâche)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

class PlanningParser:
    """Parser intelligent de fichiers Excel de planning"""
    
    def __init__(self):
        self.column_mapping = {
            'bloc': ['bloc', 'block', 'lot', 'secteur'],
            'phase': ['phase', 'etape', 'step'],
            'task': ['tache', 'tâche', 'task', 'activite', 'activité'],
            'start': ['debut', 'début', 'start', 'date_debut', 'date début'],
            'end': ['fin', 'end', 'date_fin', 'date fin'],
            'duration': ['duree', 'durée', 'duration', 'jours'],
            'progress': ['avancement', 'progress', '%', 'pourcent'],
            'status': ['statut', 'status', 'etat', 'état'],
            'responsible': ['responsable', 'responsible', 'pilote'],
            'value': ['valeur', 'value', 'montant', 'cout', 'coût']
        }
    
    def parse_excel(self, file):
        """
        Parse un fichier Excel et détecte la structure
        
        Args:
            file: Fichier uploadé (BytesIO ou path)
            
        Returns:
            DataFrame avec colonnes standardisées
        """
        try:
            # Lecture Excel
            df = pd.read_excel(file, sheet_name=0)
            
            # Nettoyage colonnes
            df.columns = df.columns.str.strip().str.lower()
            
            # Mapping colonnes
            df_mapped = self._map_columns(df)
            
            # Détection structure hiérarchique
            df_structured = self._detect_structure(df_mapped)
            
            # Nettoyage et typage
            df_clean = self._clean_data(df_structured)
            
            return df_clean
            
        except Exception as e:
            raise Exception(f"Erreur parsing: {str(e)}")
    
    def _map_columns(self, df):
        """Mappe les colonnes vers noms standardisés"""
        mapped_df = df.copy()
        
        for standard_name, possible_names in self.column_mapping.items():
            for col in df.columns:
                if any(name in col for name in possible_names):
                    mapped_df[standard_name] = df[col]
                    break
        
        return mapped_df
    
    def _detect_structure(self, df):
        """Détecte la structure hiérarchique BLOC > Phase > Tâche"""
        df_result = df.copy()
        
        # Initialisation colonnes
        df_result['level'] = 'tache'
        df_result['bloc'] = None
        df_result['phase'] = None
        
        current_bloc = None
        current_phase = None
        
        for idx, row in df_result.iterrows():
            # Détection BLOC (ligne en majuscules, pas de dates)
            if 'task' in row and pd.notna(row['task']):
                task_str = str(row['task']).strip()
                
                # BLOC si majuscules et pas de date
                if task_str.isupper() and pd.isna(row.get('start')):
                    df_result.at[idx, 'level'] = 'bloc'
                    df_result.at[idx, 'bloc'] = task_str
                    current_bloc = task_str
                    current_phase = None
                
                # Phase si commence par numéro ou tiret
                elif (task_str[0].isdigit() or task_str.startswith('-')) and pd.isna(row.get('start')):
                    df_result.at[idx, 'level'] = 'phase'
                    df_result.at[idx, 'phase'] = task_str
                    df_result.at[idx, 'bloc'] = current_bloc
                    current_phase = task_str
                
                # Tâche (a des dates)
                else:
                    df_result.at[idx, 'level'] = 'tache'
                    df_result.at[idx, 'bloc'] = current_bloc
                    df_result.at[idx, 'phase'] = current_phase
        
        return df_result
    
    def _clean_data(self, df):
        """Nettoie et type les données"""
        df_clean = df.copy()
        
        # Conversion dates
        for date_col in ['start', 'end']:
            if date_col in df_clean.columns:
                df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
        
        # Calcul durée si manquante
        if 'start' in df_clean.columns and 'end' in df_clean.columns:
            mask = df_clean['duration'].isna()
            df_clean.loc[mask, 'duration'] = (
                df_clean.loc[mask, 'end'] - df_clean.loc[mask, 'start']
            ).dt.days
        
        # Conversion progress en numérique
        if 'progress' in df_clean.columns:
            df_clean['progress'] = pd.to_numeric(
                df_clean['progress'].astype(str).str.replace('%', ''),
                errors='coerce'
            )
        
        # Conversion valeur en numérique
        if 'value' in df_clean.columns:
            df_clean['value'] = pd.to_numeric(df_clean['value'], errors='coerce')
        
        # Renommage colonnes finales
        column_rename = {
            'task': 'task_name',
            'start': 'start_date',
            'end': 'end_date'
        }
        df_clean = df_clean.rename(columns=column_rename)
        
        return df_clean


def generate_demo_data():
    """Génère un planning de démonstration"""
    
    data = []
    start_base = datetime(2024, 1, 1)
    
    # BLOC 1: INFRASTRUCTURE
    data.append({
        'level': 'bloc',
        'bloc': 'INFRASTRUCTURE',
        'phase': None,
        'task_name': 'INFRASTRUCTURE',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Phase 1.1
    data.append({
        'level': 'phase',
        'bloc': 'INFRASTRUCTURE',
        'phase': '1.1 - Terrassement',
        'task_name': '1.1 - Terrassement',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Tâches phase 1.1
    tasks_11 = [
        ('Décapage terrain', 5, 100, 50000),
        ('Excavation générale', 10, 100, 120000),
        ('Remblaiement', 7, 80, 85000)
    ]
    
    current_date = start_base
    for task_name, duration, progress, value in tasks_11:
        data.append({
            'level': 'tache',
            'bloc': 'INFRASTRUCTURE',
            'phase': '1.1 - Terrassement',
            'task_name': task_name,
            'start_date': current_date,
            'end_date': current_date + timedelta(days=duration),
            'duration': duration,
            'progress': progress,
            'status': 'Achevé' if progress == 100 else 'En cours',
            'value': value
        })
        current_date += timedelta(days=duration)
    
    # Phase 1.2
    data.append({
        'level': 'phase',
        'bloc': 'INFRASTRUCTURE',
        'phase': '1.2 - Fondations',
        'task_name': '1.2 - Fondations',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Tâches phase 1.2
    tasks_12 = [
        ('Semelles béton', 8, 100, 180000),
        ('Longrines', 6, 90, 140000),
        ('Murs de soutènement', 12, 60, 220000)
    ]
    
    for task_name, duration, progress, value in tasks_12:
        data.append({
            'level': 'tache',
            'bloc': 'INFRASTRUCTURE',
            'phase': '1.2 - Fondations',
            'task_name': task_name,
            'start_date': current_date,
            'end_date': current_date + timedelta(days=duration),
            'duration': duration,
            'progress': progress,
            'status': 'Achevé' if progress == 100 else 'En cours',
            'value': value
        })
        current_date += timedelta(days=duration)
    
    # BLOC 2: STRUCTURE
    data.append({
        'level': 'bloc',
        'bloc': 'STRUCTURE',
        'phase': None,
        'task_name': 'STRUCTURE',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Phase 2.1
    data.append({
        'level': 'phase',
        'bloc': 'STRUCTURE',
        'phase': '2.1 - Élévation',
        'task_name': '2.1 - Élévation',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Tâches phase 2.1
    tasks_21 = [
        ('Poteaux RDC', 10, 100, 250000),
        ('Poutres RDC', 8, 100, 180000),
        ('Dalle RDC', 6, 70, 200000),
        ('Poteaux R+1', 10, 40, 250000),
        ('Poutres R+1', 8, 20, 180000)
    ]
    
    for task_name, duration, progress, value in tasks_21:
        data.append({
            'level': 'tache',
            'bloc': 'STRUCTURE',
            'phase': '2.1 - Élévation',
            'task_name': task_name,
            'start_date': current_date,
            'end_date': current_date + timedelta(days=duration),
            'duration': duration,
            'progress': progress,
            'status': 'Achevé' if progress == 100 else 'En cours',
            'value': value
        })
        current_date += timedelta(days=duration)
    
    # BLOC 3: SECOND ŒUVRE
    data.append({
        'level': 'bloc',
        'bloc': 'SECOND ŒUVRE',
        'phase': None,
        'task_name': 'SECOND ŒUVRE',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Phase 3.1
    data.append({
        'level': 'phase',
        'bloc': 'SECOND ŒUVRE',
        'phase': '3.1 - Électricité',
        'task_name': '3.1 - Électricité',
        'start_date': None,
        'end_date': None,
        'duration': None,
        'progress': None,
        'status': None,
        'value': None
    })
    
    # Tâches phase 3.1
    tasks_31 = [
        ('Saignées et gaines', 15, 0, 120000),
        ('Câblage général', 20, 0, 180000),
        ('Tableaux électriques', 5, 0, 80000)
    ]
    
    for task_name, duration, progress, value in tasks_31:
        data.append({
            'level': 'tache',
            'bloc': 'SECOND ŒUVRE',
            'phase': '3.1 - Électricité',
            'task_name': task_name,
            'start_date': current_date,
            'end_date': current_date + timedelta(days=duration),
            'duration': duration,
            'progress': progress,
            'status': 'Non démarré',
            'value': value
        })
        current_date += timedelta(days=duration)
    
    df = pd.DataFrame(data)
    return df
