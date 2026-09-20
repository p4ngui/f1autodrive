# Spécification Détaillée : Rétro-Ingénierie des Paramètres F1 2026 par Analyse de Télémétrie FastF1

**Version mise à jour** : v1.1 - Intégration analyse réelle des données FastF1 et alternatives

## Résumé Exécutif

Ce document spécifie une méthodologie complète pour extraire les paramètres physiques et techniques des voitures F1 2026 through reverse engineering à partir des données télémétriques officielles récupérées via l'API FastF1. L'approche combine analyse statistique, optimisation numérique et validation croisée pour atteindre une précision maximale.

**Mise à jour v1.1** : Cette version intègre les résultats d'analyse réelle des données FastF1 (session Bahrain 2022 Race) et une évaluation complète des bibliothèques Python alternatives.

**Objectif Principal** : Déterminer avec précision les paramètres suivants :
- Puissance moteur ICE + ERS (kW)
- Rapports de boîte de vitesses (8 rapports)
- Coefficients aérodynamiques (Cx, Cz, DRS effect)
- Performance de freinage (décélération max, bias)
- Points de freinage et trajectoires de référence
- Consommation carburant et gestion ERS
- Caractéristiques pneus (grip, dégradation, pressions)

---

## Table des Matières

1. [Architecture du Système de Rétro-Ingénierie](#1-architecture-du-système-de-rétro-ingénierie)
2. [Analyse Réelle des Données FastF1](#2-analyse-réelle-des-données-fastf1)
3. [Thème 1 : Acquisition et Prétraitement des Données FastF1](#3-thème-1--acquisition-et-prétraitement-des-données-fastf1)
4. [Thème 2 : Estimation de la Puissance Moteur en Ligne Droite](#4-thème-2--estimation-de-la-puissance-moteur-en-ligne-droite)
5. [Thème 3 : Calcul des Rapports de Boîte de Vitesses](#5-thème-3--calcul-des-rapports-de-boîte-de-vitesses)
6. [Thème 4 : Analyse Aérodynamique et Coefficients Cx/Cz](#6-thème-4--analyse-aérodynamique-et-coefficients-cxcz)
7. [Thème 5 : Performance de Freinage et Points de Décélération](#7-thème-5--performance-de-freinage-et-points-de-décélération)
8. [Thème 6 : Trajectoires de Référence et Points de Virage](#8-thème-6--trajectoires-de-référence-et-points-de-virage)
9. [Thème 7 : Gestion ERS et Stratégies Énergétiques](#9-thème-7--gestion-ers-et-stratégies-énergétiques)
10. [Thème 8 : Caractérisation des Pneus](#10-thème-8--caractérisation-des-pneus)
11. [Évaluation des Plateformes de Simulation](#11-évaluation-des-plateformes-de-simulation)
12. [Bibliothèques Python Alternatives](#12-bibliothèques-python-alternatives)
13. [Recommandations d'Implémentation et Roadmap](#13-recommandations-dimplémentation-et-roadmap)

---

## 1. Architecture du Système de Rétro-Ingénierie

### 1.1 Vue d'Ensemble

```
┌──────────────────────────────────────────────────────────────────────┐
│                    COUCHE ACQUISITION DONNÉES                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │  FastF1 API │  │  Cache Local│  │  Validation │                  │
│  │  (Sessions) │──│  (Parquet)  │──│  Qualité    │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   COUCHE PRÉTRAITEMENT & FEATURE ENGINEERING         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Nettoyage   │  │ Interpolation│  │ Segmentation│                  │
│  │ Outliers    │──│ Temporelle  │──│ (Lignes Droites,              │
│  │             │  │             │  │  Virages)   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      COUCHE MODÈLES PHYSIQUES                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Modèle      │  │ Modèle      │  │ Modèle      │  │ Modèle      │ │
│  │ Longitudinal│  │ Aérodynamique│  │ Freinage   │  │ ERS         │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────┬────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    COUCHE OPTIMISATION & CALIBRATION                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                  │
│  │ Optimiseur  │  │ Validation  │  │ Génération  │                  │
│  │ (SciPy/     │──│ Croisée     │──│ Rapport     │                  │
│  │  Cython)    │  │ Q1/Q2/Q3    │  │ JSON/YAML   │                  │
│  └─────────────┘  └─────────────┘  └─────────────┘                  │
└──────────────────────────────────────────────────────────────────────┘
```

### 1.2 Composants Principaux

| Composant | Responsabilité | Technologies |
|-----------|---------------|--------------|
| **DataAcquirer** | Récupération sessions FastF1 | `fastf1`, `asyncio` |
| **DataValidator** | Contrôle qualité données | `pandas`, `numpy` |
| **SegmentIdentifier** | Détection lignes droites/virages | `scipy.signal`, custom algo |
| **PowerEstimator** | Calcul puissance moteur | Modèles physiques + optimisation |
| **GearboxCalculator** | Extraction rapports boîte | Analyse RPM/vitesse |
| **AeroModel** | Estimation Cx, Cz | Régression non-linéaire |
| **BrakeAnalyzer** | Performance freinage | Détection points d'inflexion |
| **ERSOptimizer** | Stratégie énergétique | Programmation dynamique |
| **TireCharacterizer** | Courbes de grip | Modèles empiriques |

### 1.3 Flux de Données

```python
# Pseudo-code du flux principal
class TelemetryReverseEngineering:
    def __init__(self):
        self.acquirer = DataAcquirer()
        self.validator = DataValidator()
        self.segments = SegmentIdentifier()
        self.models = PhysicsModels()
        self.optimizer = Calibrator()
    
    def run_pipeline(self, season, grand_prix, sessions=['Q1', 'Q2', 'Q3']):
        # 1. Acquisition
        raw_data = self.acquirer.fetch(season, grand_prix, sessions)
        
        # 2. Validation
        clean_data = self.validator.process(raw_data)
        
        # 3. Segmentation
        segments = self.segments.identify(clean_data)
        
        # 4. Estimation paramètres
        params = {}
        params['power'] = self.models.estimate_power(segments['straights'])
        params['gearbox'] = self.models.extract_gear_ratios(segments['all'])
        params['aero'] = self.models.fit_aero(segments['straights'])
        params['braking'] = self.models.analyze_braking(segments['braking_zones'])
        
        # 5. Calibration multi-session
        calibrated = self.optimizer.cross_validate(params, sessions=['Q1', 'Q2', 'Q3'])
        
        # 6. Export
        return self.export(calibrated, format='yaml')
```

---

## 2. Analyse Réelle des Données FastF1

### 2.1 Résultats d'Analyse - Bahrain GP 2022 (Course)

**Session analysée** : Bahrain Grand Prix 2022 - Race  
**Pilote** : Charles Leclerc (Ferrari #16)  
**Tour analysé** : Tour 51 (le plus rapide)  
**Données collectées** : 705 points de télémétrie

#### 2.1.1 Structure des Données Disponibles (18 colonnes)

| Colonne | Type | Non-null | Description |
|---------|------|----------|-------------|
| **Date** | datetime64[ns] | 705/705 | Horodatage absolu |
| **SessionTime** | timedelta64[ns] | 705/705 | Temps depuis début session |
| **DriverAhead** | object | 705/705 | Pilote devant |
| **DistanceToDriverAhead** | float64 | 0/705 | Distance au pilote devant (non disponible) |
| **Time** | timedelta64[ns] | 705/705 | Temps dans le tour |
| **RPM** | float64 | 705/705 | Régime moteur |
| **Speed** | float64 | 705/705 | Vitesse (km/h) |
| **nGear** | int64 | 705/705 | Rapport de boîte actuel |
| **Throttle** | float64 | 705/705 | Position accélérateur (0-100%) |
| **Brake** | bool | 705/705 | État du frein (True/False) |
| **DRS** | int64 | 705/705 | État DRS (0=fermé, 1=ouvert) |
| **Source** | object | 705/705 | Source des données |
| **Distance** | float64 | 705/705 | Distance parcourue (m) |
| **RelativeDistance** | float64 | 705/705 | Distance relative (%) |
| **Status** | object | 705/705 | Statut (OnTrack, etc.) |
| **X** | float64 | 705/705 | Position X (m) |
| **Y** | float64 | 705/705 | Position Y (m) |
| **Z** | float64 | 705/705 | Position Z (m) |

#### 2.1.2 Statistiques Clés

**Vitesse :**
- Min : 61 km/h (virage lent)
- Max : 299 km/h (ligne droite)
- Moyenne : 201.7 km/h
- Écart-type : 66.9 km/h

**Régime Moteur :**
- Min : 5,306 RPM
- Max : 12,026 RPM (**limiteur ~12,000 RPM confirmé**)
- Moyenne : 10,188 RPM
- Zone optimale (>10,000 RPM) : 58.4% du temps

**Pédales :**
- Accélérateur à 100% : 48.5% du temps
- Accélérateur partiel : 46.1% du temps
- Accélérateur à 0% : 5.4% du temps
- Freinage actif : 21.7% du temps

**DRS :**
- Sur ce tour : DRS ouvert 100% du temps (ligne droite principale)
- Valeurs uniques : [1] uniquement

#### 2.1.3 Fréquence d'Échantillonnage

- **Intervalle moyen** : 134.33 ms
- **Fréquence** : 7.4 Hz (variable selon les sessions)
- **Observation** : La fréquence est inférieure aux 240 Hz théoriques, probablement due à l'agrégation des données FOM

#### 2.1.4 Calcul d'Accélération (dérivée de la vitesse)

⚠️ **Attention** : Les valeurs calculées brutes sont irréalistes :
- Accélération max brute : 26.04 G
- Décélération max brute : 79.86 G

**Cause** : Le bruit de mesure et la faible fréquence d'échantillonnage créent des artefacts.  
**Solution requise** : Filtrage passe-bas (Butterworth, ordre 4, cutoff 5Hz) avant calcul des dérivées.

#### 2.1.5 Corrélations entre Variables

| | Speed | RPM | Throttle | Brake | Distance |
|---|-------|-----|----------|-------|----------|
| **Speed** | 1.00 | 0.79 | 0.65 | -0.31 | 0.09 |
| **RPM** | 0.79 | 1.00 | 0.70 | -0.38 | 0.22 |
| **Throttle** | 0.65 | 0.70 | 1.00 | **-0.82** | 0.11 |
| **Brake** | -0.31 | -0.38 | **-0.82** | 1.00 | -0.09 |
| **Distance** | 0.09 | 0.22 | 0.11 | -0.09 | 1.00 |

**Observations importantes :**
- Forte corrélation négative Throttle/Brake (-0.82) : les pilotes n'accélèrent et ne freinent jamais simultanément
- Corrélation Speed/RPM (0.79) : permet d'estimer les rapports de boîte
- Faible corrélation avec Distance : normal car circuit fermé

#### 2.1.6 Segments de Vitesse

| Segment | Plage | Points | % du tour |
|---------|-------|--------|-----------|
| Haute vitesse | >280 km/h | 77 pts | 10.9% |
| Vitesse moyenne | 150-280 km/h | 439 pts | 62.3% |
| Basse vitesse | <150 km/h | 189 pts | 26.8% |

#### 2.1.7 Coordonnées GPS (X, Y, Z)

- **X** : -577 m à +7,497 m
- **Y** : -3,500 m à +8,346 m
- **Z** : -159 m à +8 m (dénivelé du circuit Bahrain)

### 2.2 Implications pour la Rétro-Ingénierie

#### 2.2.1 Limitations Identifiées

1. **Fréquence d'échantillonnage limitée (7.4 Hz)**
   - Insuffisant pour capturer des événements transitoires rapides
   - Nécessite interpolation linéaire/cubique pour monter à 100 Hz
   
2. **Données manquantes**
   - `DistanceToDriverAhead` toujours nul (sauf en bataille rapprochée)
   - Pas de données de pression pneu, température, usure
   - Pas de données ERS directes (puissance, SOC)
   - Pas de consommation carburant en temps réel

3. **Bruit de mesure**
   - Les dérivées (accélération) sont très bruitées
   - Filtrage obligatoire avant toute utilisation

4. **DRS binaire**
   - Seulement 0 ou 1, pas de position intermédiaire
   - Limite l'analyse fine de l'impact aérodynamique

#### 2.2.2 Opportunités

1. **nGear disponible** : Permet de calculer directement les rapports de boîte
2. **Positions X/Y/Z précises** : Reconstruction fidèle des trajectoires
3. **Corrélation Throttle/Brake** : Validation des modèles de comportement pilote
4. **RPM max à 12,026** : Confirmation du limiteur à 12,000 RPM (réglementation F1)

---

## 3. Thème 1 : Acquisition et Prétraitement des Données FastF1

### 3.1 Sources de Données Requises

#### 3.1.1 API FastF1 - Sessions Cibles

**Saison 2024-2025** (pour extrapolation 2026) :
- Toutes les séances de qualification (Q1, Q2, Q3)
- Courses complètes (pour données consommation/ERS)
- Essais libres (FP1, FP2, FP3) pour variabilité setup

**Circuits Prioritaires** (caractéristiques variées) :
1. **Monza** : Lignes droites longues → puissance max, aero faible
2. **Spa-Francorchamps** : Variété virages rapides/lents → downforce
3. **Monaco** : Accélérations/freinages fréquents → performance low-speed
4. **Bahrain** : Conditions chaudes → dégradation pneus
5. **Silverstone** : Virages haute vitesse → charge aero
6. **Jeddah** : Vitesses moyennes élevées → efficacité aero

#### 3.1.2 Canaux de Télémétrie Requis

| Canal | Unité | Fréquence | Usage |
|-------|-------|-----------|-------|
| `Speed` | km/h | 240 Hz | Calcul puissance, rapports |
| `RPM` | tr/min | 240 Hz | Calibration moteur, shifts |
| `Throttle` | % | 240 Hz | Identification phases accélération |
| `Brake` | % | 240 Hz | Zones de freinage, décélération |
| `nGear` | - | 240 Hz | Validation rapports boîte |
| `DRS` | bool | 240 Hz | Impact aérodynamique |
| `Source` | - | 240 Hz | Qualité donnée (onboard/offboard) |
| `Time` | datetime | 240 Hz | Synchronisation |
| `SessionTime` | timedelta | 240 Hz | Durée tour |
| `Distance` | m | 240 Hz | Position sur circuit |
| `X`, `Y`, `Z` | m | 240 Hz | Trajectoire 3D |
| `Status` | string | Event | État voiture (track/pit/etc) |

**Données Additionnelles (si disponibles)** :
- `FuelFlow` : kg/h (estimation consommation)
- `ERSMode` : Mode deployment (Overtake, Quali, etc.)
- `ERSDeploy` : % deployment électrique
- `ERSCharge` : Niveau batterie (%)
- `BrakeBias` : Répartition avant/arrière (%)
- `TirePressure_*` : Pressions par pneu (bar)
- `TireTemp_*` : Températures par pneu (°C)

### 2.2 Protocole d'Acquisition

#### 2.2.1 Configuration FastF1

```python
# Configuration recommandée
import fastf1

fastf1.Cache.enable_cache('/path/to/cache', 
                          use_requests_cache=True,
                          ignore_version=True)

# Fonctions d'acquisition
def fetch_qualifying_data(season, gp_name, year=None):
    """
    Récupère toutes les séances de qualification pour un GP
    
    Parameters:
    - season: int (ex: 2024)
    - gp_name: str (ex: 'Italian Grand Prix')
    
    Returns:
    - dict with Q1, Q2, Q3 telemetry per driver
    """
    session = fastf1.get_session(season, gp_name, 'Q')
    session.load(telemetry=True, weather=False)
    
    drivers = session.results['DriverNumber'].unique()
    telemetry_data = {}
    
    for drv in drivers:
        laps = session.laps.pick_driver(drv)
        
        # Extraire meilleurs tours par séance
        for q_segment in ['Q1', 'Q2', 'Q3']:
            segment_laps = laps.pick_segment(q_segment)
            if len(segment_laps) > 0:
                best_lap = segment_laps.pick_fastest()
                tel = best_lap.get_telemetry()
                telemetry_data[f"{drv}_{q_segment}"] = {
                    'telemetry': tel,
                    'lap_time': best_lap['LapTime'],
                    'compound': best_lap['Compound'],
                    'fuel_load_estimate': estimate_fuel_from_segment(q_segment)
                }
    
    return telemetry_data
```

#### 2.2.2 Critères de Sélection des Tours

**Pour analyse puissance max (Q3)** :
- Top 3 drivers (meilleures performances)
- Tours sans erreurs (pas de lock-up, track limits violations)
- Conditions météo stables (Dry, Wind < 15 km/h)
- Piste rubbered-in (Q3 uniquement)
- Fuel load minimum (fin de Q3)

**Pour calibration globale** :
- Inclure Q1, Q2 pour variabilité fuel loads
- Comparer mêmes drivers sur différentes séances
- Identifier tendances dégradation pneus

### 2.3 Prétraitement des Données

#### 2.3.1 Nettoyage et Filtrage

**Algorithmes requis** :

1. **Suppression outliers** :
   ```python
   def remove_outliers(data, column, method='iqr', threshold=1.5):
       Q1 = data[column].quantile(0.25)
       Q3 = data[column].quantile(0.75)
       IQR = Q3 - Q1
       
       if method == 'iqr':
           mask = (data[column] >= Q1 - threshold*IQR) & \
                  (data[column] <= Q3 + threshold*IQR)
       elif method == 'zscore':
           from scipy.stats import zscore
           mask = np.abs(zscore(data[column])) < threshold
       
       return data[mask]
   ```

2. **Interpolation temporelle** :
   - Resample à fréquence constante (240 Hz)
   - Interpolation linéaire pour canaux continus (Speed, RPM)
   - Interpolation forward-fill pour canaux discrets (nGear, DRS)

3. **Synchronisation** :
   - Aligner tous les canaux sur même base temporelle
   - Vérifier cohérence Time vs SessionTime vs Distance

#### 2.3.2 Segmentation Automatique

**Algorithme de détection lignes droites** :

```python
def identify_straight_sections(telemetry, track_data, 
                               min_length=150,  # mètres
                               max_curvature=0.005):  # 1/m
    """
    Identifie les sections de ligne droite exploitables pour analyse puissance
    
    Criteria:
    - Longueur minimale 150m (pour atteindre vitesse max)
    - Courbure maximale très faible
    - Pas d'interruption throttle/brake significative
    """
    # Calcul courbure à partir coordonnées X,Y
    curvature = calculate_curvature(track_data['X'], track_data['Y'])
    
    # Identifier sections faible courbure
    straight_mask = np.abs(curvature) < max_curvature
    
    # Filtrer par longueur minimale
    straight_sections = []
    current_section = []
    
    for i, is_straight in enumerate(straight_mask):
        if is_straight:
            current_section.append(i)
        else:
            if len(current_section) >= min_length_samples:
                straight_sections.append(current_section)
            current_section = []
    
    # Ajouter dernière section si valide
    if len(current_section) >= min_length_samples:
        straight_sections.append(current_section)
    
    # Filtrer sections avec interruptions throttle/brake
    valid_sections = []
    for section in straight_sections:
        tel_section = telemetry.iloc[section]
        
        # Vérifier throttle continu (>95% du temps)
        throttle_ratio = (tel_section['Throttle'] > 95).mean()
        
        # Vérifier absence de freinage significatif
        brake_events = (tel_section['Brake'] > 10).sum()
        
        if throttle_ratio > 0.95 and brake_events < 5:
            valid_sections.append(section)
    
    return valid_sections
```

**Algorithme de détection zones de freinage** :

```python
def identify_braking_zones(telemetry, 
                           min_decel=-5.0,  # m/s²
                           min_duration=0.3):  # secondes
    """
    Identifie les zones de freinage pour analyse performance
    
    Criteria:
    - Décélération < -5 m/s²
    - Durée minimale 0.3s
    - Transition claire throttle -> brake
    """
    # Calcul décélération instantanée
    acceleration = np.gradient(telemetry['Speed'], 
                               telemetry['Time'].dt.total_seconds())
    
    # Identifier phases de décélération forte
    braking_mask = acceleration < min_decel
    
    # Détecter transitions
    brake_starts = np.where(np.diff(braking_mask.astype(int)) == 1)[0] + 1
    brake_ends = np.where(np.diff(braking_mask.astype(int)) == -1)[0] + 1
    
    # Construire zones
    braking_zones = []
    for start, end in zip(brake_starts, brake_ends):
        duration = telemetry['Time'].iloc[end] - telemetry['Time'].iloc[start]
        
        if duration.total_seconds() >= min_duration:
            braking_zones.append({
                'start_idx': start,
                'end_idx': end,
                'duration': duration.total_seconds(),
                'entry_speed': telemetry['Speed'].iloc[start],
                'exit_speed': telemetry['Speed'].iloc[end],
                'max_decel': acceleration[start:end].min(),
                'avg_decel': acceleration[start:end].mean()
            })
    
    return braking_zones
```

### 2.4 Métriques de Qualité des Données

| Métrique | Seuil Acceptable | Action si Non-Conforme |
|----------|------------------|------------------------|
| Taux échantillonnage | ≥ 200 Hz | Rejeter session |
| Données manquantes (Speed) | < 1% | Interpolation |
| Données manquantes (RPM) | < 2% | Interpolation |
| Incohérences nGear/Speed | < 0.5% | Correction manuelle |
| Drift temporel | < 10 ms/tour | Recalibration |
| Positions GPS aberrantes | < 0.1% | Suppression points |

---

## 3. Thème 2 : Estimation de la Puissance Moteur en Ligne Droite

### 3.1 Modèle Physique de Base

#### 3.1.1 Équation Fondamentale du Mouvement Longitudinal

La puissance totale requise pour accélérer une F1 s'exprime comme :

$$P_{total}(v) = P_{accel}(v) + P_{drag}(v) + P_{rolling}(v) + P_{grade}(v)$$

Où :
- $P_{accel} = m \cdot a(v) \cdot v$ (puissance d'accélération)
- $P_{drag} = \frac{1}{2} \rho \cdot C_x A \cdot v^3$ (résistance aérodynamique)
- $P_{rolling} = C_{rr} \cdot m \cdot g \cdot v$ (résistance au roulement)
- $P_{grade} = m \cdot g \cdot \sin(\theta) \cdot v$ (pente, négligeable sur circuits plats)

**Puissance disponible aux roues** :

$$P_{wheel}(v) = P_{ICE}(v) + P_{ERS}(v) - P_{losses}(v)$$

Avec :
- $P_{ICE}$ : Puissance moteur thermique (fonction de RPM)
- $P_{ERS}$ : Puissance électrique MGU-K (max 120 kW en 2024, 350 kW en 2026)
- $P_{losses}$ : Pertes transmission (~3-5%)

#### 3.1.2 Hypothèses pour Ligne Droite de Qualification

**Conditions Q3 optimales** :
1. **Fuel load minimal** : ~20-30 kg restants (vs 110 kg départ course)
2. **ERS deployment max** : Mode Qualification (100% disponible)
3. **DRS ouvert** : Réduction Cx de 15-20%
4. **Pistes sèches** : Grip optimal, pas de pertes patinage
5. **Température air** : ρ ≈ 1.15 kg/m³ (conditions standards)

**Paramètres connus/approximés** :
- Masse totale : $m = 798 \text{ kg (min)} + m_{fuel} + m_{driver} \approx 880-900 \text{ kg}$
- $C_{rr} \approx 0.015-0.020$ (pneus F1 haute pression)
- $\rho_{air} \approx 1.15 \text{ kg/m}^3$ (niveau mer, 20°C)
- Efficacité transmission : $\eta_{trans} \approx 0.95-0.97$

### 3.2 Méthodologie d'Extraction de Puissance

#### 3.2.1 Approche par Optimisation Non-Linéaire

**Formulation du problème** :

Soit $v_{measured}(t)$ la vitesse mesurée sur une ligne droite.

On cherche les paramètres $\theta = \{P_{ICE\_max}, P_{ERS}, C_xA\}$ qui minimisent :

$$J(\theta) = \sum_{i=1}^{N} \left( v_{model}(t_i, \theta) - v_{measured}(t_i) \right)^2$$

Sous contraintes :
- $P_{ICE\_min} \leq P_{ICE\_max} \leq P_{ICE\_max\_bound}$
- $0 \leq P_{ERS} \leq P_{ERS\_limit}$
- $C_xA_{min} \leq C_xA \leq C_xA_{max}$

**Algorithme d'optimisation** :

```python
from scipy.optimize import minimize, differential_evolution

def estimate_engine_power(straight_data, track_elevation=None):
    """
    Estime puissance ICE + ERS à partir données ligne droite
    
    Parameters:
    - straight_data: DataFrame with Speed, Time, Distance, RPM, DRS
    - track_elevation: optional elevation profile
    
    Returns:
    - dict with power estimates and confidence intervals
    """
    
    # 1. Calculer accélération instantanée
    speed = straight_data['Speed'].values / 3.6  # Convert to m/s
    time = straight_data['Time'].values
    distance = straight_data['Distance'].values
    
    # Filtrage passe-bas pour réduire bruit
    from scipy.signal import savgol_filter
    speed_smooth = savgol_filter(speed, window_length=11, polyorder=3)
    
    # Gradient pour accélération
    acceleration = np.gradient(speed_smooth, time)
    
    # 2. Définir modèle physique
    def longitudinal_model(t, P_ICE_max, P_ERS, CxA, mass):
        """
        Simulation mouvement longitudinal
        
        Returns predicted velocity at time t
        """
        v = np.zeros_like(t)
        a = np.zeros_like(t)
        
        v[0] = speed_smooth[0]  # Condition initiale
        
        for i in range(1, len(t)):
            dt = t[i] - t[i-1]
            
            # Puissance totale disponible (fonction de RPM via gear ratio)
            rpm = interpolate_rpm_at_time(t[i])
            P_ICE = engine_curve(rpm, P_ICE_max)  # Courbe caractéristique
            P_electric = P_ERS if rpm > 10000/60 else 0  # Seuil activation
            
            P_total = (P_ICE + P_electric) * eta_transmission
            
            # Résistances
            P_drag = 0.5 * rho_air * CxA * v[i-1]**3
            P_rolling = C_rr * mass * g * v[i-1]
            P_grade = mass * g * sin(elevation_gradient[i]) if track_elevation else 0
            
            # Accélération résultante
            P_accel = P_total - P_drag - P_rolling - P_grade
            a[i] = P_accel / (mass * v[i-1]) if v[i-1] > 0.1 else 0
            
            # Intégration vitesse
            v[i] = v[i-1] + a[i] * dt
        
        return v
    
    # 3. Fonction objectif
    def objective(params):
        P_ICE_max, P_ERS, CxA, mass = params
        
        v_pred = longitudinal_model(time, P_ICE_max, P_ERS, CxA, mass)
        
        # Erreur quadratique moyenne
        mse = np.mean((v_pred - speed_smooth)**2)
        
        # Pénalités pour violations contraintes physiques
        penalty = 0
        if P_ICE_max < 600e3 or P_ICE_max > 1100e3:
            penalty += 1e6 * (P_ICE_max - 850e3)**2
        if P_ERS < 0 or P_ERS > 400e3:
            penalty += 1e6 * (P_ERS - 120e3)**2
        
        return mse + penalty
    
    # 4. Bornes paramètres
    bounds = [
        (600e3, 1100e3),    # P_ICE_max [W]
        (0, 400e3),         # P_ERS [W]
        (0.8, 1.8),         # CxA [m²] (DRS open)
        (850, 950)          # mass [kg]
    ]
    
    # 5. Optimisation globale (éviter minima locaux)
    result = differential_evolution(objective, bounds, 
                                    seed=42, 
                                    maxiter=500,
                                    tol=1e-6,
                                    workers=-1)  # Parallélisation
    
    # 6. Raffinement avec méthode locale
    result_refined = minimize(objective, 
                             result.x,
                             method='L-BFGS-B',
                             bounds=bounds)
    
    # 7. Calcul intervalles confiance (bootstrap)
    ci_lower, ci_upper = calculate_confidence_intervals(
        straight_data, result_refined.x, n_bootstrap=1000
    )
    
    return {
        'P_ICE_max': result_refined.x[0],
        'P_ERS': result_refined.x[1],
        'CxA_DRS_open': result_refined.x[2],
        'mass_estimate': result_refined.x[3],
        'confidence_intervals': {
            'P_ICE': ci_lower[0], ci_upper[0],
            'P_ERS': ci_lower[1], ci_upper[1]
        },
        'rmse': np.sqrt(result_refined.fun),
        'convergence': result_refined.success
    }
```

#### 3.2.2 Correction Multi-Sessions (Q1/Q2/Q3)

**Problématique** : La puissance estimée varie selon :
- Fuel load (différent par session)
- Deployment ERS (stratégie variable)
- Usure pneus (grip disponible)
- Conditions piste (température, rubber)

**Méthode de correction** :

```python
def cross_session_calibration(estimates_q1, estimates_q2, estimates_q3):
    """
    Combine estimations Q1/Q2/Q3 pour extraire puissance intrinsèque
    
    Utilise différences fuel loads pour découpler puissances
    """
    
    # Fuel loads typiques par session (estimations)
    fuel_loads = {
        'Q1': 110.0,  # Plein réservoir
        'Q2': 80.0,   # Consommation Q1 + marge
        'Q3': 25.0    # Minimum pour tour rapide
    }
    
    # Masses correspondantes
    masses = {
        session: 798 + fuel + 80  # Car + fuel + driver
        for session, fuel in fuel_loads.items()
    }
    
    # Système d'équations : P_total = P_ICE + P_ERS - f(mass)
    # On résout pour P_ICE et P_ERS séparément
    
    from scipy.optimize import least_squares
    
    def system_equations(params):
        P_ICE_base, P_ERS_max, alpha_mass = params
        
        residuals = []
        
        for session, est in [('Q1', estimates_q1), 
                             ('Q2', estimates_q2), 
                             ('Q3', estimates_q3)]:
            
            # Puissance totale mesurée
            P_total_measured = est['P_total']
            
            # Modèle : P_total = P_ICE + P_ERS - alpha * (mass - mass_ref)
            mass_penalty = alpha_mass * (masses[session] - masses['Q3'])
            P_total_model = P_ICE_base + P_ERS_max - mass_penalty
            
            residuals.append(P_total_measured - P_total_model)
        
        return residuals
    
    # Résolution
    initial_guess = [850e3, 120e3, 0.5]  # P_ICE, P_ERS, sensibilité masse
    result = least_squares(system_equations, initial_guess)
    
    return {
        'P_ICE_intrinsic': result.x[0],
        'P_ERS_deployed': result.x[1],
        'mass_sensitivity': result.x[2],
        'goodness_of_fit': np.sum(result.fun**2)
    }
```

### 3.3 Validation et Précision

#### 3.3.1 Métriques de Validation

| Métrique | Formule | Objectif |
|----------|---------|----------|
| RMSE Vitesse | $\sqrt{\frac{1}{N}\sum(v_{pred} - v_{meas})^2}$ | < 0.5 km/h |
| RMSE Accélération | $\sqrt{\frac{1}{N}\sum(a_{pred} - a_{meas})^2}$ | < 0.2 m/s² |
| R² Ajustement | $1 - \frac{SS_{res}}{SS_{tot}}$ | > 0.995 |
| Biais Systématique | $\frac{1}{N}\sum(v_{pred} - v_{meas})$ | < 0.1 km/h |

#### 3.3.2 Tests de Robustesse

1. **Analyse de sensibilité** :
   - Varier ρ_air ± 5% → impact sur P_ICE estimé ?
   - Varier C_rr ± 20% → stabilité estimation ?
   - Varier η_trans ± 2% → robustesse ?

2. **Validation croisée circuits** :
   - Monza (low downforce) vs Spa (medium) vs Monaco (high)
   - Cohérence P_ICE entre circuits ?
   - Variations CxA expliquées par setups ?

3. **Comparaison données constructeurs** :
   - Mercedes : ~1050 HP claimed (2024)
   - Ferrari : ~1080 HP claimed
   - Red Bull/Honda : ~1060 HP claimed
   
   → Notre estimation doit être dans ± 3% de ces valeurs

### 3.4 Résultats Attendus (Ordres de Grandeur)

**Pour saison 2024** :
- P_ICE_max : 780-820 kW (1050-1100 HP)
- P_ERS_max : 120 kW (161 HP) réglementaire
- P_total_combined : 900-940 kW (1200-1260 HP)
- CxA_DRS_open : 0.9-1.1 m²
- CxA_DRS_closed : 1.1-1.3 m²

**Extrapolation 2026** (à valider) :
- P_ICE_max : 650-700 kW (réduction réglementaire)
- P_ERS_max : 350 kW (augmentation ×3)
- P_total_combined : 1000-1050 kW (léger increase)
- CxA : Réduction attendue -10% (règles aero)

---

## 4. Thème 3 : Calcul des Rapports de Boîte de Vitesses

### 4.1 Principe Physique

La relation entre vitesse véhicule, régime moteur et rapport de transmission :

$$v = \frac{RPM}{60} \cdot i_{total} \cdot C_{tire}$$

Où :
- $v$ : Vitesse véhicule [m/s]
- $RPM$ : Régime moteur [tr/min]
- $i_{total} = i_{gear} \cdot i_{final} \cdot \eta_{slip}$ : Rapport total
- $C_{tire}$ : Circonférence pneu [m]
- $\eta_{slip} \approx 0.95-0.98$ : Facteur de glissement

**Inversion pour extraction rapport** :

$$i_{gear} = \frac{v \cdot 60}{RPM \cdot i_{final} \cdot C_{tire}}$$

### 4.2 Méthodologie d'Extraction

#### 4.2.1 Détection des Changements de Rapport

**Algorithme de segmentation par RPM** :

```python
def detect_gear_shifts(telemetry, 
                       rpm_threshold=11500,  # RPM de shift typique
                       min_gear_duration=0.4):  # secondes
    """
    Détecte automatiquement les changements de rapport
    
    Méthode : Recherche chutes brutales de RPM à throttle constant
    """
    rpm = telemetry['RPM'].values
    throttle = telemetry['Throttle'].values
    time = telemetry['Time'].values
    speed = telemetry['Speed'].values
    
    # Calcul dérivée RPM
    rpm_derivative = np.gradient(rpm, time)
    
    # Identifier chutes RPM (> 2000 RPM/s descendante)
    shift_candidates = np.where(
        (rpm_derivative < -2000) & 
        (throttle > 80)  # Shift sous charge
    )[0]
    
    # Regrouper candidats proches (même événement)
    shifts = []
    if len(shift_candidates) > 0:
        current_group = [shift_candidates[0]]
        
        for i in range(1, len(shift_candidates)):
            if shift_candidates[i] - shift_candidates[i-1] < 5:  # < 5 samples
                current_group.append(shift_candidates[i])
            else:
                shifts.append(int(np.mean(current_group)))
                current_group = [shift_candidates[i]]
        
        shifts.append(int(np.mean(current_group)))
    
    # Filtrer par durée minimale entre shifts
    filtered_shifts = []
    if len(shifts) > 0:
        filtered_shifts.append(shifts[0])
        
        for i in range(1, len(shifts)):
            time_diff = time[shifts[i]] - time[shifts[i-1]]
            if time_diff.total_seconds() > min_gear_duration:
                filtered_shifts.append(shifts[i])
    
    return filtered_shifts
```

#### 4.2.2 Calcul des Rapports par Segment

```python
def extract_gear_ratios(telemetry, shift_indices, tire_circumference=2.262):
    """
    Calcule les rapports de boîte à partir segments entre shifts
    
    Parameters:
    - telemetry: DataFrame complet
    - shift_indices: indices des changements de rapport
    - tire_circumference: circonférence pneu chargée [m]
    
    Returns:
    - dict with gear ratios (1st to 8th)
    """
    
    final_drive_ratio = 3.5  # À raffiner, typique F1
    
    gear_segments = []
    
    # Créer segments entre shifts
    boundaries = [0] + shift_indices + [len(telemetry)]
    
    for i in range(len(boundaries) - 1):
        start_idx = boundaries[i]
        end_idx = boundaries[i+1]
        
        segment = telemetry.iloc[start_idx:end_idx]
        
        # Statistiques segment
        avg_rpm = segment['RPM'].mean()
        avg_speed = segment['Speed'].mean() / 3.6  # Convert to m/s
        max_rpm = segment['RPM'].max()
        max_speed = segment['Speed'].max() / 3.6
        
        # Estimer rapport théorique
        # i_total = (v * 60) / (RPM * tire_circ)
        i_total_estimate = (avg_speed * 60) / (avg_rpm * tire_circumference)
        
        # Extraire rapport boîte (en assumant final drive connu)
        gear_ratio_estimate = i_total_estimate / final_drive_ratio
        
        gear_segments.append({
            'gear_number': i + 1,
            'avg_rpm': avg_rpm,
            'avg_speed_kmh': segment['Speed'].mean(),
            'i_total': i_total_estimate,
            'i_gear_estimate': gear_ratio_estimate,
            'samples': len(segment),
            'confidence': 'high' if len(segment) > 50 else 'medium'
        })
    
    return gear_segments
```

#### 4.2.3 Raffinement par Optimisation Globale

**Approche bayésienne pour incertitudes** :

```python
def Bayesian_gear_ratio_estimation(all_laps_data, prior_bounds):
    """
    Estime rapports de boîte avec intervalles crédibles
    
    Utilise approche MCMC pour quantifier incertitudes
    """
    import pymc as pm
    
    with pm.Model() as model:
        # Priors pour chaque rapport (8 gears)
        gear_ratios = pm.Uniform('gear_ratios', 
                                 lower=prior_bounds['min'], 
                                 upper=prior_bounds['max'],
                                 shape=8)
        
        final_drive = pm.Normal('final_drive', mu=3.5, sigma=0.2)
        tire_circ = pm.Normal('tire_circ', mu=2.262, sigma=0.01)
        
        # Likelihood : modèle physique
        predicted_speeds = []
        observed_speeds = []
        
        for lap in all_laps_data:
            for gear_idx in range(8):
                mask = (lap['nGear'] == gear_idx + 1)
                
                if mask.sum() > 10:
                    v_pred = (lap['RPM'][mask].mean() / 60 * 
                             gear_ratios[gear_idx] * 
                             final_drive * 
                             tire_circ)
                    
                    predicted_speeds.append(v_pred * 3.6)  # Convert to km/h
                    observed_speeds.append(lap['Speed'][mask].mean())
        
        #Erreur observation
        sigma = pm.HalfNormal('sigma', sigma=2.0)  # km/h
        
        likelihood = pm.Normal('likelihood', 
                              mu=predicted_speeds, 
                              sigma=sigma,
                              observed=observed_speeds)
        
        # Sampling MCMC
        trace = pm.sample(2000, tune=1000, chains=4, target_accept=0.95)
    
    # Extraire statistiques
    results = {}
    for i in range(8):
        samples = trace['gear_ratios'][:, i]
        results[f'gear_{i+1}'] = {
            'mean': np.mean(samples),
            'std': np.std(samples),
            'ci_95': np.percentile(samples, [2.5, 97.5]),
            'mode': np.argmax(np.histogram(samples, bins=50)[0])
        }
    
    results['final_drive'] = {
        'mean': np.mean(trace['final_drive']),
        'ci_95': np.percentile(trace['final_drive'], [2.5, 97.5])
    }
    
    return results
```

### 4.3 Validation des Rapports Estimés

#### 4.3.1 Contrôles de Cohérence

| Test | Critère | Action si Échec |
|------|---------|-----------------|
| Progression monotone | $i_1 > i_2 > ... > i_8$ | Réviser détection shifts |
| Ratios consécutifs | $1.1 < i_n/i_{n+1} < 1.3$ | Vérifier données RPM |
| Vitesse max par rapport | Cohérente avec courbe puissance | Ajuster final drive |
| RPM à shift | 11000-12500 RPM typique | Corriger seuils détection |

#### 4.3.2 Comparaison avec Données Connues

**Rapports typiques F1 (référence)** :

| Rapport | Valeur Typique | Plage Acceptable |
|---------|----------------|------------------|
| 1ère | 3.8-4.2 | 3.5-4.5 |
| 2ème | 2.8-3.1 | 2.6-3.3 |
| 3ème | 2.2-2.5 | 2.0-2.7 |
| 4ème | 1.8-2.0 | 1.6-2.2 |
| 5ème | 1.5-1.7 | 1.3-1.9 |
| 6ème | 1.25-1.4 | 1.1-1.5 |
| 7ème | 1.05-1.2 | 0.95-1.3 |
| 8ème | 0.90-1.0 | 0.85-1.1 |

### 4.4 Output Format

```yaml
# gearbox_parameters.yaml
gearbox:
  manufacturer: "Red Bull Powertrains"  # Inféré depuis équipe
  num_gears: 8
  final_drive_ratio: 3.52  # ± 0.05
  
  gear_ratios:
    1: { value: 4.05, ci_95: [3.98, 4.12], confidence: high }
    2: { value: 2.95, ci_95: [2.89, 3.01], confidence: high }
    3: { value: 2.35, ci_95: [2.30, 2.40], confidence: high }
    4: { value: 1.92, ci_95: [1.88, 1.96], confidence: high }
    5: { value: 1.62, ci_95: [1.58, 1.66], confidence: medium }
    6: { value: 1.35, ci_95: [1.31, 1.39], confidence: medium }
    7: { value: 1.15, ci_95: [1.11, 1.19], confidence: medium }
    8: { value: 0.95, ci_95: [0.92, 0.98], confidence: low }
  
  shift_points_rpm:
    upshift: { nominal: 11800, max: 12200 }
    downshift: { nominal: 9500, min: 8000 }
  
  shift_times_ms:
    upshift: { mean: 45, std: 8 }
    downshift: { mean: 55, std: 10 }
  
  tire_circumference_m: { value: 2.262, condition: "loaded_60kmh" }
  
  validation:
    monotonic_progression: true
    ratio_spread_valid: true
    max_speed_consistent: true
    data_quality_score: 0.94
```

---

## 5. Thème 4 : Analyse Aérodynamique et Coefficients Cx/Cz

### 5.1 Modèle Aérodynamique F1

#### 5.1.1 Équations Fondamentales

**Force de traînée (Drag)** :
$$F_{drag} = \frac{1}{2} \rho v^2 C_x A$$

**Force d'appui (Downforce)** :
$$F_{downforce} = \frac{1}{2} \rho v^2 C_z A$$

**Puissance dissipée par traînée** :
$$P_{drag} = F_{drag} \cdot v = \frac{1}{2} \rho C_x A v^3$$

**Impact DRS** :
- Réduction $C_x$ : 15-20% (DRS ouvert)
- Réduction $C_z$ : 10-15% (perte downforce associée)

#### 5.1.2 Séparation des Effets

Sur ligne droite à vitesse stabilisée ($a = 0$) :

$$P_{wheel} = P_{drag} + P_{rolling}$$

$$P_{ICE} + P_{ERS} = \frac{1}{2} \rho C_x A v_{max}^3 + C_{rr} m g v_{max}$$

Donc :

$$C_x A = \frac{2(P_{wheel} - C_{rr} m g v_{max})}{\rho v_{max}^3}$$

### 5.2 Méthodologie d'Extraction CxA

#### 5.2.1 Mesure Vitesse Maximale par Circuit

```python
def extract_CxA_from_top_speed(telemetry_data, power_estimate):
    """
    Extrait CxA à partir de vitesse maximale atteinte
    
    Parameters:
    - telemetry_data: dict with circuits as keys
    - power_estimate: P_wheel total estimé (section 3)
    
    Returns:
    - CxA estimates per circuit
    """
    results = {}
    
    for circuit, data in telemetry_data.items():
        # Identifier vitesse max sur lignes droites principales
        straights = identify_straight_sections(data['telemetry'], 
                                               data['track'])
        
        top_speeds = []
        for straight in straights:
            tel_section = data['telemetry'].iloc[straight]
            max_v = tel_section['Speed'].max()
            
            # Vérifier conditions de validité
            if (tel_section['Throttle'] > 98).mean() > 0.9 and \
               (tel_section['Brake'] < 5).mean() > 0.95 and \
               tel_section['DRS'].mean() > 0.8:  # DRS ouvert
                top_speeds.append(max_v)
        
        if len(top_speeds) > 0:
            v_max = np.mean(top_speeds) / 3.6  # Convert to m/s
            
            # Calcul CxA
            # P_wheel = 0.5 * rho * CxA * v³ + Crr * m * g * v
            rho = 1.15  # kg/m³ (conditions standards)
            Crr = 0.018
            m = 880  # kg (Q3 fuel load minimal)
            g = 9.81
            
            P_wheel = power_estimate['P_total']  # Watts
            
            P_rolling = Crr * m * g * v_max
            P_drag = P_wheel - P_rolling
            
            CxA = (2 * P_drag) / (rho * v_max**3)
            
            results[circuit] = {
                'v_max_kmh': v_max * 3.6,
                'CxA_DRS_open': CxA,
                'power_used_kw': P_wheel / 1000,
                'valid_samples': len(top_speeds)
            }
    
    return results
```

#### 5.2.2 Extraction CzA depuis les Virages Rapides

**Principe** : Dans un virage à vitesse constante, l'accélération latérale est limitée par le grip disponible, lui-même proportionnel à la charge verticale (poids + downforce).

$$a_y^{max} = \mu \cdot \frac{F_z^{total}}{m} = \mu \cdot \left(g + \frac{\frac{1}{2}\rho v^2 C_z A}{m}\right)$$

Donc :

$$C_z A = \frac{2m}{\rho v^2} \left(\frac{a_y^{max}}{\mu} - g\right)$$

```python
def extract_CzA_from_corners(telemetry_data, mu_estimate=1.8):
    """
    Extrait CzA à partir des vitesses en virage
    
    Parameters:
    - telemetry_data: données complètes
    - mu_estimate: coefficient de friction pneu/piste
    
    Returns:
    - CzA estimate avec incertitudes
    """
    from scipy.optimize import minimize
    
    # Identifier virages rapides (> 150 km/h)
    corner_data = extract_high_speed_corners(telemetry_data, min_speed=150)
    
    def aero_model(params, observed_ay, v_squared):
        CzA = params[0]
        
        # Modèle : ay = mu * (g + 0.5*rho*CzA*v² / m)
        rho = 1.15
        m = 880
        g = 9.81
        
        ay_predicted = mu_estimate * (g + 0.5 * rho * CzA * v_squared / m)
        
        return np.sum((observed_ay - ay_predicted)**2)
    
    # Collecter données virages
    v_squared_list = []
    ay_observed_list = []
    
    for corner in corner_data:
        tel = corner['telemetry']
        
        # Vitesse moyenne au apex
        v_apex = tel['Speed'].iloc[len(tel)//2] / 3.6  # m/s
        
        # Accélération latérale estimée (depuis courbure)
        curvature = corner['curvature']  # 1/m
        ay = v_apex**2 * curvature  # m/s²
        
        v_squared_list.append(v_apex**2)
        ay_observed_list.append(ay)
    
    v_squared = np.array(v_squared_list)
    ay_observed = np.array(ay_observed_list)
    
    # Optimisation
    result = minimize(aero_model, 
                     x0=[2.5],  # Initial guess CzA
                     args=(ay_observed, v_squared),
                     bounds=[(1.5, 4.0)],  # Bornes réalistes
                     method='L-BFGS-B')
    
    CzA_estimated = result.x[0]
    
    return {
        'CzA': CzA_estimated,
        'confidence': 'medium',  # À améliorer avec plus de données
        'num_corners_analyzed': len(corner_data),
        'rmse': np.sqrt(result.fun / len(corner_data))
    }
```

### 5.3 Ratio Cz/Cx (Efficacité Aérodynamique)

Le ratio $C_z/C_x$ indique l'efficacité du package aérodynamique :

- **Monza** (low downforce) : ~2.5-3.0
- **Spa** (medium) : ~3.5-4.0
- **Monaco** (high) : ~4.5-5.0
- **Barcelone** (référence) : ~4.0

```python
def calculate_aero_efficiency(CxA, CzA):
    """Calcule le ratio d'efficacité aérodynamique"""
    return CzA / CxA

# Exemple d'analyse multi-circuits
def analyze_aero_packages(all_circuits_data):
    """
    Analyse les différents setups aero par circuit
    
    Returns:
    - DataFrame avec CxA, CzA, efficiency par circuit
    """
    results = []
    
    for circuit, data in all_circuits_data.items():
        CxA = extract_CxA_from_top_speed(data, power_estimate)
        CzA = extract_CzA_from_corners(data)
        
        efficiency = CzA['CzA'] / CxA[circuit]['CxA_DRS_open']
        
        results.append({
            'circuit': circuit,
            'CxA_DRS_open': CxA[circuit]['CxA_DRS_open'],
            'CzA': CzA['CzA'],
            'efficiency_Cz_Cx': efficiency,
            'setup_category': categorize_setup(efficiency)
        })
    
    return pd.DataFrame(results)

def categorize_setup(efficiency):
    if efficiency < 3.0:
        return "Low Downforce (Monza-style)"
    elif efficiency < 4.0:
        return "Medium Downforce"
    else:
        return "High Downforce"
```

### 5.4 Validation et Incertitudes

| Source d'Incertitude | Impact sur CxA | Mitigation |
|---------------------|----------------|------------|
| ρ_air (altitude, temp) | ± 3% | Utiliser données météo FastF1 |
| P_ERS deployment | ± 2% | Analyser plusieurs tours |
| C_rr estimation | ± 1% | Sensitivity analysis |
| Vitesse mesurée | ± 0.5% | Moyenne sur 10+ samples |
| Pertes transmission | ± 1.5% | Littérature technique F1 |

**Précision attendue** :
- CxA : ± 5% (intervalle confiance 95%)
- CzA : ± 8% (plus variable selon conditions)
- Ratio Cz/Cx : ± 7%

---

## 6. Thème 5 : Performance de Freinage et Points de Décélération

### 6.1 Modèle de Freinage F1

#### 6.1.1 Dynamique de Décélération

La décélération maximale est limitée par :
1. **Grip pneu** : $\mu \cdot g$ (typiquement 4.5-5.5G pour F1)
2. **Capacité étriers** : Couple de freinage max (avant/arrière)
3. **Transfert de charge** : $\Delta F_z = \frac{m \cdot a_x \cdot h_{CoG}}{L}$

**Équation fondamentale** :

$$a_x^{max} = \mu \cdot g \cdot \frac{L_r + \frac{h_{CoG}}{L} \cdot \mu \cdot g}{L - \mu \cdot h_{CoG}}$$

Où :
- $L_r$ : Distance CoG vers essieu arrière
- $h_{CoG}$ : Hauteur centre de gravité
- $L$ : Empattement

#### 6.1.2 Brake Bias Optimal

Répartition idéale avant/arrière :

$$bias_{front} = \frac{L_r + \frac{h_{CoG}}{L} \cdot a_x/g}{L} \times 100\%$$

Typiquement : 55-60% avant (selon décélération)

### 6.2 Extraction Performance Freinage

#### 6.2.1 Identification Zones de Freinage

```python
def analyze_braking_performance(telemetry, track_data):
    """
    Analyse complète des performances de freinage
    
    Returns:
    - dict with braking metrics per corner
    """
    braking_zones = identify_braking_zones(telemetry)
    
    results = []
    
    for zone in braking_zones:
        tel_zone = telemetry.iloc[zone['start_idx']:zone['end_idx']]
        
        # Métriques clés
        entry_speed = tel_zone['Speed'].iloc[0]
        exit_speed = tel_zone['Speed'].iloc[-1]
        delta_v = entry_speed - exit_speed
        
        duration = zone['duration']
        distance = tel_zone['Distance'].iloc[-1] - tel_zone['Distance'].iloc[0]
        
        # Décélérations
        accel_long = np.gradient(tel_zone['Speed']/3.6, 
                                tel_zone['Time'].dt.total_seconds())
        
        max_decel = accel_long.min()  # Plus négatif
        avg_decel = np.mean(accel_long[accel_long < -1])  # Seulement phases freinage
        
        # Pic de freinage (% brake pedal)
        peak_brake = tel_zone['Brake'].max()
        avg_brake = tel_zone[tel_zone['Brake'] > 10]['Brake'].mean()
        
        # Estimation décélération en G
        decel_g = abs(avg_decel) / 9.81
        
        results.append({
            'zone_id': len(results) + 1,
            'corner_name': get_corner_name(track_data, zone),
            'entry_speed_kmh': entry_speed,
            'exit_speed_kmh': exit_speed,
            'delta_v_kmh': delta_v,
            'braking_distance_m': distance,
            'braking_duration_s': duration,
            'max_decel_ms2': max_decel,
            'avg_decel_ms2': avg_decel,
            'decel_G': decel_g,
            'peak_brake_percent': peak_brake,
            'avg_brake_percent': avg_brake,
            'initial_gear': tel_zone['nGear'].iloc[0],
            'final_gear': tel_zone['nGear'].iloc[-1]
        })
    
    return results
```

#### 6.2.2 Détection Points de Freinage de Référence

```python
def extract_reference_braking_points(all_laps_data, track_data):
    """
    Identifie les points de freinage optimaux (reference lap)
    
    Méthode : Trouve le point de freinage le plus tardif parmi tous les tours
             qui permet encore de réussir le virage
    """
    braking_points = {}
    
    for corner_id in range(num_corners(track_data)):
        corner_entry = get_corner_entry_location(track_data, corner_id)
        
        # Collecter tous les points de freinage pour ce virage
        all_brake_starts = []
        
        for lap in all_laps_data:
            # Trouver début de freinage avant ce virage
            brake_zone = find_braking_before_corner(lap, corner_entry)
            
            if brake_zone is not None:
                # Vérifier que le virage est réussi (pas de sortie large)
                if corner_exit_within_limits(lap, corner_id):
                    all_brake_starts.append({
                        'location': brake_zone['start_location'],
                        'speed_entry': brake_zone['entry_speed'],
                        'lap_time': lap['lap_time'],
                        'driver': lap['driver']
                    })
        
        # Sélectionner point de référence (le plus tardif valide)
        if len(all_brake_starts) > 0:
            # Trier par location (plus tardif = plus grande distance)
            all_brake_starts.sort(key=lambda x: x['location'], reverse=True)
            
            # Prendre top 5% le plus tardifs
            top_percentile = int(len(all_brake_starts) * 0.05)
            latest_brakes = all_brake_starts[:top_percentile]
            
            braking_points[corner_id] = {
                'reference_location': np.mean([b['location'] for b in latest_brakes]),
                'reference_speed': np.mean([b['speed_entry'] for b in latest_brakes]),
                'variability_std': np.std([b['location'] for b in latest_brakes]),
                'num_samples': len(latest_brakes),
                'drivers_using': list(set([b['driver'] for b in latest_brakes]))
            }
    
    return braking_points
```

### 6.3 Métriques de Performance de Freinage

| Métrique | Valeur Typique F1 | Méthode de Mesure |
|----------|------------------|-------------------|
| Décélération max | -5.5 à -6.0 G | Minimum local acceleration |
| Décélération moyenne | -4.5 à -5.0 G | Moyenne zone freinage |
| Distance freinage (300→100 km/h) | 80-95 m | Distance Δv spécifique |
| Durée freinage typique | 1.5-2.5 s | Temps entrée→sortie |
| Pression pédale max | 150-180 bar | Inféré depuis % Brake |
| Température disques | 600-900°C | Non mesurable directement |

### 6.4 Calibration pour Simulation

```yaml
# braking_parameters.yaml
braking:
  max_deceleration_ms2: -55.0  # ~5.6G
  avg_deceleration_ms2: -48.0  # ~4.9G
  
  brake_bias:
    nominal_front_percent: 57.5
    adjustable_range: [52, 62]
    speed_dependent: true
    
  brake_pressure_characteristics:
    pedal_travel_to_pressure: linear  # Simplification
    max_pressure_bar: 170
    threshold_for_detection_percent: 10
  
  temperature_model:
    optimal_range_C: [300, 900]
    fade_threshold_C: 950
    warmup_target_C: 400
  
  reference_braking_points:
    # Par exemple, Monaco Turn 10 (Nouvelle Chicane)
    monaco_t10:
      location_m: 2847.5
      entry_speed_kmh: 285
      exit_speed_kmh: 65
      distance_m: 87
      duration_s: 1.82
      decel_G: 5.2
  
  validation:
    data_quality_score: 0.91
    num_braking_zones_analyzed: 156
    consistency_across_drivers: high
```

---

## 7. Thème 6 : Trajectoires de Référence et Points de Virage

### 7.1 Extraction de la Racing Line Optimale

#### 7.1.1 Méthodologie de Construction

**Principe** : La trajectoire de référence est extraite en aggregant les meilleures portions de tours de tous les drivers sur une session (typiquement Q3).

```python
def extract_reference_racing_line(all_laps_q3, track_data):
    """
    Construit la trajectoire optimale depuis les meilleurs segments de tous les tours
    
    Returns:
    - reference_line: array of (x, y) coordinates
    - speed_profile: optimal speed at each point
    - curvature_profile: track curvature at each point
    """
    from scipy.interpolate import interp1d, splprep, splev
    
    # 1. Normaliser tous les tours sur même distance (0 à L_circuit)
    normalized_laps = []
    
    for lap in all_laps_q3:
        tel = lap['telemetry']
        
        # Interpoler sur grille de distance uniforme (1 point tous les mètres)
        circuit_length = track_data['length_m']
        distance_grid = np.arange(0, circuit_length, 1.0)
        
        # Interpolation position X, Y
        interp_x = interp1d(tel['Distance'], tel['X'], 
                           kind='cubic', fill_value='extrapolate')
        interp_y = interp1d(tel['Distance'], tel['Y'], 
                           kind='cubic', fill_value='extrapolate')
        interp_speed = interp1d(tel['Distance'], tel['Speed'],
                               kind='linear', fill_value='extrapolate')
        
        normalized_lap = {
            'driver': lap['driver'],
            'lap_time': lap['lap_time'],
            'distance': distance_grid,
            'X': interp_x(distance_grid),
            'Y': interp_y(distance_grid),
            'speed': interp_speed(distance_grid)
        }
        
        normalized_laps.append(normalized_lap)
    
    # 2. Pour chaque point du circuit, prendre la position médiane (robuste aux outliers)
    reference_X = np.median([lap['X'] for lap in normalized_laps], axis=0)
    reference_Y = np.median([lap['Y'] for lap in normalized_laps], axis=0)
    
    # Prendre le max de vitesse (représente le potentiel optimal)
    reference_speed = np.percentile([lap['speed'] for lap in normalized_laps], 
                                    q=95, axis=0)  # 95ème percentile
    
    # 3. Lisser la trajectoire (B-spline)
    tck, u = splprep([reference_X, reference_Y], s=50, k=3)  # s=lissage
    smooth_reference = splev(np.linspace(0, 1, len(reference_X)), tck)
    
    return {
        'X': smooth_reference[0],
        'Y': smooth_reference[1],
        'speed_profile': reference_speed,
        'num_samples': len(normalized_laps),
        'circuits_covered': list(set([lap['driver'] for lap in normalized_laps]))
    }
```

#### 7.1.2 Détection Automatique des Points de Virage

```python
def detect_corner_apexes(reference_line, track_data):
    """
    Identifie automatiquement les apex des virages depuis la courbure
    
    Returns:
    - corners: list of dict with corner characteristics
    """
    from scipy.signal import find_peaks
    
    X = reference_line['X']
    Y = reference_line['Y']
    
    # Calcul courbure le long de la trajectoire
    dx = np.gradient(X)
    dy = np.gradient(Y)
    ddx = np.gradient(dx)
    ddy = np.gradient(dy)
    
    # Courbure κ = |x'y'' - y'x''| / (x'² + y'²)^(3/2)
    curvature = np.abs(dx * ddy - dy * ddx) / (dx**2 + dy**2)**1.5
    
    # Détecter pics de courbure (apex des virages)
    apex_indices, properties = find_peaks(curvature, 
                                          height=0.02,  # Seuil minimum
                                          distance=50)   # Distance min entre virages (mètres)
    
    corners = []
    for i, apex_idx in enumerate(apex_indices):
        # Caractérisation du virage
        apex_location = apex_idx  # En mètres depuis start
        
        # Vitesse au apex
        apex_speed = reference_line['speed_profile'][apex_idx]
        
        # Courbure max
        max_curvature = curvature[apex_idx]
        radius_at_apex = 1.0 / max_curvature if max_curvature > 0 else np.inf
        
        # Identifier entrée et sortie de virage
        # (points où courbure dépasse 50% du max)
        threshold = 0.5 * max_curvature
        before_apex = curvature[:apex_idx]
        after_apex = curvature[apex_idx:]
        
        entry_idx = np.where(before_apex < threshold)[0]
        exit_idx = apex_idx + np.where(after_apex < threshold)[0]
        
        corner_entry = entry_idx[-1] if len(entry_idx) > 0 else 0
        corner_exit = exit_idx[0] + apex_idx if len(exit_idx) > 0 else len(curvature)
        
        # Type de virage
        corner_type = classify_corner_type(radius_at_apex, apex_speed, 
                                          corner_exit - corner_entry)
        
        corners.append({
            'corner_id': i + 1,
            'apex_location_m': apex_location,
            'apex_speed_kmh': apex_speed,
            'radius_m': radius_at_apex,
            'max_curvature': max_curvature,
            'entry_location_m': corner_entry,
            'exit_location_m': corner_exit,
            'corner_length_m': corner_exit - corner_entry,
            'corner_type': corner_type,
            'recommended_gear': estimate_gear_for_corner(apex_speed),
            'throttle_point_m': corner_exit + 10  # Estimation
        })
    
    return corners

def classify_corner_type(radius, speed, length):
    """Catégorise le virage selon ses caractéristiques"""
    if radius > 200:
        return "Fast Corner"
    elif radius > 80:
        return "Medium Corner"
    elif speed < 80:
        return "Hairpin"
    else:
        return "Slow Corner"
```

### 7.2 Profils de Vitesse de Référence

#### 7.2.1 Vitesse Cible par Segment

```yaml
# reference_speed_profile.yaml
track: "Monza"
session: "Q3 2024"

sectors:
  sector_1:
    start_m: 0
    end_m: 1850
    characteristics: "Technical first sector with chicanes"
    
    speed_targets:
      - location_m: 0
        speed_kmh: 0
        action: "Start"
      - location_m: 120
        speed_kmh: 285
        action: "Full throttle"
      - location_m: 207
        speed_kmh: 72
        action: "Braking for T1"
      - location_m: 285
        speed_kmh: 95
        action: "T1 apex"
      # ... continuer pour tout le circuit
  
  sector_2:
    # ... idem
  
  sector_3:
    # ... idem

validation:
  lap_time_target_s: 81.450
  top_speed_kmh: 352
  avg_speed_kmh: 245
```

---

## 8. Thème 7 : Gestion ERS et Stratégies Énergétiques

### 8.1 Modélisation du Système ERS F1

#### 8.1.1 Architecture Power Unit Hybride

**Composants** :
- **MGU-K** (Motor Generator Unit - Kinetic) : Récupération sur freinage, deployment sur accélération
  - Max power : 120 kW (2024), 350 kW (2026)
  - Max deployment : 33% du tour (2024), illimité (2026 avec limite energy flow)
  - Max recuperation : 2 MJ/tour (2024)
  
- **MGU-H** (Motor Generator Unit - Heat) : Récupération sur turbo (supprimé en 2026)
  - Unlimited energy flow (2024)
  - Supprimé règlement 2026
  
- **Battery (ES)** : Stockage énergie électrique
  - Capacity : ~20 MJ (2024), ~30+ MJ (2026 estimé)
  - Voltage : ~1000V
  - Min SoC : Variable selon stratégie

#### 8.1.2 Modes de Deployment

| Mode | Usage | Power Output | Duration |
|------|-------|--------------|----------|
| **Quali** | Tour chrono max | 120 kW (2024) / 350 kW (2026) | Full lap |
| **Overtake** | Dépassement | 120 kW | 10-15 sec |
| **Balance** | Course normale | 60-80 kW | Distribué |
| **Harvest** | Recharge batterie | -50 kW (regen) | Lignes droites |
| **None** | Préservation | 0 kW | - |

### 8.2 Extraction Stratégie ERS depuis Télémétrie

#### 8.2.1 Estimation Deployment par Segment

**Problématique** : FastF1 ne fournit pas directement le deployment ERS. Il faut l'inférer depuis :
- Différence puissance totale vs puissance ICE attendue
- Patterns d'accélération spécifiques
- Données RPM/speed incohérentes avec moteur thermique seul

```python
def estimate_ers_deployment(telemetry, power_estimate, engine_model):
    """
    Estime le deployment ERS à partir du surplus de puissance observé
    
    Parameters:
    - telemetry: données complètes (Speed, RPM, Throttle, etc.)
    - power_estimate: P_total estimé depuis section 3
    - engine_model: courbe puissance ICE(RPM)
    
    Returns:
    - ers_deploy_timeline: série temporelle du deployment ERS
    """
    
    # 1. Calculer puissance requise pour mouvement longitudinal
    speed_ms = telemetry['Speed'].values / 3.6
    accel = np.gradient(speed_ms, telemetry['Time'].dt.total_seconds())
    
    mass = 880  # kg
    rho = 1.15
    CxA = 1.0  # m² (estimé section 5)
    Crr = 0.018
    
    # Puissance aux roues requise
    P_accel = mass * accel * speed_ms
    P_drag = 0.5 * rho * CxA * speed_ms**3
    P_rolling = Crr * mass * 9.81 * speed_ms
    
    P_required = P_accel + P_drag + P_rolling
    
    # 2. Estimer puissance ICE disponible (fonction de RPM)
    rpm = telemetry['RPM'].values
    P_ICE_available = engine_model.power_curve(rpm) * eta_transmission
    
    # 3. Le surplus est attribué à l'ERS
    P_ERS_inferred = P_required - P_ICE_available
    
    # Contraintes physiques
    P_ERS_inferred = np.clip(P_ERS_inferred, 0, 120e3)  # Max 120 kW (2024)
    
    # Seuillage : considérer ERS actif seulement si > 10 kW
    P_ERS_inferred[P_ERS_inferred < 10e3] = 0
    
    # 4. Calcul énergie déployée
    dt = np.mean(np.diff(telemetry['Time'].dt.total_seconds()))
    energy_deployed_J = np.sum(P_ERS_inferred) * dt
    energy_deployed_MJ = energy_deployed_J / 1e6
    
    return {
        'P_ERS_timeline_W': P_ERS_inferred,
        'energy_deployed_MJ': energy_deployed_MJ,
        'deployment_duration_s': np.sum(P_ERS_inferred > 10e3) * dt,
        'avg_power_when_active_kW': np.mean(P_ERS_inferred[P_ERS_inferred > 10e3]) / 1e3,
        'compliance_2MJ_limit': energy_deployed_MJ <= 2.0
    }
```

#### 8.2.2 Inférence Stratégie de Recharge

```python
def analyze_harvesting_strategy(telemetry, ers_estimate):
    """
    Identifie les phases de recharge batterie (harvest)
    
    Indices :
    - Throttle < 100% sur ligne droite (sauf DRS)
    - Décélération légère sans freinage
    - Patterns RPM inhabituels
    """
    
    straights = identify_straight_sections(telemetry, track_data)
    
    harvest_events = []
    
    for straight in straights:
        tel_section = telemetry.iloc[straight]
        
        # Chercher sections où throttle < 100% mais pas de brake
        partial_throttle_mask = (tel_section['Throttle'] < 98) & \
                               (tel_section['Throttle'] > 50) & \
                               (tel_section['Brake'] < 5)
        
        if partial_throttle_mask.sum() > 10:  # > 10 samples
            # Probable phase de harvest
            harvest_events.append({
                'location': tel_section['Distance'].iloc[0],
                'duration_s': partial_throttle_mask.sum() * dt,
                'avg_throttle': tel_section.loc[partial_throttle_mask, 'Throttle'].mean(),
                'estimated_harvest_kW': 40  # Typique
            })
    
    total_harvest_MJ = sum([e['duration_s'] * e['estimated_harvest_kW'] 
                           for e in harvest_events]) / 1000
    
    return {
        'harvest_events': harvest_events,
        'total_harvest_MJ': total_harvest_MJ,
        'net_energy_balance_MJ': ers_estimate['energy_deployed_MJ'] - total_harvest_MJ,
        'strategy_type': classify_ers_strategy(ers_estimate, harvest_events)
    }

def classify_ers_strategy(deploy, harvest):
    if deploy['energy_deployed_MJ'] > 1.8 and harvest['total_harvest_MJ'] > 1.5:
        return "Aggressive (Quali-style)"
    elif deploy['energy_deployed_MJ'] < 1.0:
        return "Conservative (Fuel save)"
    else:
        return "Balanced"
```

### 8.3 Spécifications ERS pour Simulation 2026

```yaml
# ers_parameters_2026.yaml
ers_system:
  regulation_year: 2026
  
  mgu_k:
    max_power_kw: 350  # Augmentation ×3 vs 2024
    max_torque_Nm: 350
    efficiency_motor: 0.92
    efficiency_generator: 0.88
    max_rpm: 50000
    activation_threshold_kmh: 20
    
  mgu_h:
    present: false  # Supprimé en 2026
    
  energy_store:
    capacity_MJ: 33  # Estimé (vs ~20 MJ en 2024)
    voltage_V: 1000
    max_charge_rate_kW: 500
    max_discharge_rate_kW: 500
    min_soc_percent: 10
    target_soc_end_lap_percent: 15
  
  energy_flow_limits:
    max_deploy_per_lap_MJ: null  # Illimité (mais limité par battery capacity)
    max_harvest_per_lap_MJ: null
    max_power_deploy_kw: 350
    max_power_harvest_kw: 250
  
  deployment_modes:
    quali:
      power_kw: 350
      duration: full_lap
      priority: performance
    
    race_overtake:
      power_kw: 350
      duration_s: 15
      cooldown_s: 30
    
    race_defend:
      power_kw: 250
      duration_s: 20
      cooldown_s: 25
    
    balanced:
      power_kw: 175
      strategy: distribute_evenly
    
    harvest:
      power_kw: -200  # Negative = charging
      locations: [straights_with_DRS]
  
  inferred_from_telemetry:
    avg_deploy_per_lap_MJ: 2.8  # À calibrer depuis données 2024-25
    typical_harvest_MJ: 2.5
    net_energy_consumption_MJ: 0.3
    preferred_harvest_zones: ["main_straight", "back_straight"]
```

---

## 9. Thème 8 : Caractérisation des Pneus

### 9.1 Modèle de Grip et Dégradation

#### 9.1.1 Paramètres à Extraire

| Paramètre | Description | Méthode d'Estimation |
|-----------|-------------|---------------------|
| μ_peak | Coefficient friction max | Accélération latérale max virages |
| μ_sliding | Friction pneu glissant | Analyse lock-ups |
| k_load_sensitivity | Sensibilité charge verticale | Comparaison vitesses virages |
| optimal_temp_C | Température fenêtre optimale | Littérature + inference |
| degradation_rate | Perte grip par tour | Δlap time sur stint |
| warmup_laps | Tours pour température | Premiers tours de sortie pit |

#### 9.1.2 Extraction du Coefficient de Friction

```python
def estimate_mu_from_corners(telemetry, track_data, aero_params):
    """
    Estime μ peak à partir des accélérations latérales maximales
    
    Formule : a_y_max = μ * (g + downforce/m)
    Donc : μ = a_y_max / (g + downforce/m)
    """
    
    # Identifier virages rapides (où downforce est significative)
    fast_corners = extract_high_speed_corners(telemetry, min_speed=150)
    
    ay_max_observed = []
    downforce_terms = []
    
    for corner in fast_corners:
        tel = corner['telemetry']
        
        # Vitesse au apex
        v_apex = tel['Speed'].iloc[len(tel)//2] / 3.6  # m/s
        
        # Courbure → accélération latérale
        curvature = corner['curvature']
        ay = v_apex**2 * curvature  # m/s²
        
        # Downforce au apex
        CzA = aero_params['CzA']
        rho = 1.15
        m = 880
        
        downforce = 0.5 * rho * CzA * v_apex**2
        downforce_accel = downforce / m  # m/s²
        
        ay_max_observed.append(ay)
        downforce_terms.append(g + downforce_accel)
    
    # Régression linéaire : ay = μ * (g + downforce_accel)
    ay_max_observed = np.array(ay_max_observed)
    downforce_terms = np.array(downforce_terms)
    
    # μ = mean(ay / (g + downforce))
    mu_estimates = ay_max_observed / downforce_terms
    mu_peak = np.percentile(mu_estimates, 95)  # Prendre les valeurs max (peak grip)
    
    return {
        'mu_peak': mu_peak,
        'mu_std': np.std(mu_estimates),
        'num_corners_analyzed': len(fast_corners),
        'confidence': 'high' if len(fast_corners) > 20 else 'medium'
    }
```

#### 9.1.3 Estimation Dégradation par Compound

```python
def estimate_tire_degradation(all_laps_by_stint, compound):
    """
    Estime la dégradation du pneu en fonction de l'âge
    
    Méthode : Régression lap_time vs lap_number dans un stint
    """
    
    # Collecter données par stint
    stint_data = []
    
    for stint in all_laps_by_stint:
        if stint['compound'] != compound:
            continue
        
        laps = stint['laps']
        
        # Nettoyer : exclure premiers tours (warmup) et outliers
        clean_laps = laps[2:-1]  # Exclure tour 1-2 et dernier
        
        if len(clean_laps) < 3:
            continue
        
        # Régression linéaire : lap_time = a + b * lap_age
        lap_numbers = np.arange(len(clean_laps))
        lap_times = [lap['lap_time'].total_seconds() for lap in clean_laps]
        
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, std_err = linregress(lap_numbers, lap_times)
        
        stint_data.append({
            'stint_id': stint['id'],
            'degradation_per_lap_s': slope,
            'r_squared': r_value**2,
            'stint_length': len(laps),
            'initial_delta_s': intercept
        })
    
    # Agréger sur tous les stints
    if len(stint_data) > 0:
        avg_degradation = np.mean([s['degradation_per_lap_s'] for s in stint_data])
        std_degradation = np.std([s['degradation_per_lap_s'] for s in stint_data])
        
        # Convertir en modèle paramétrique
        # t_tire = k_0 + k_1 * age (modèle linéaire)
        k_0 = np.mean([s['initial_delta_s'] for s in stint_data])
        k_1 = avg_degradation
        
        return {
            'compound': compound,
            'tire_deg_model': 'lin',
            'k_0': k_0,
            'k_1_lin': k_1,
            'avg_degradation_per_lap_ms': avg_degradation * 1000,
            'variability_std_ms': std_degradation * 1000,
            'num_stints_analyzed': len(stint_data),
            'model_confidence': r_value**2
        }
    else:
        return None
```

### 9.2 Spécifications Pneus pour Simulation

```yaml
# tire_parameters_2026.yaml
tires:
  supplier: "Pirelli"  # Jusqu'en 2027 minimum
  
  compounds:
    C1:  # Hardest
      name: "Hard"
      color: "White"
      operating_range_C: [90, 110]
      peak_grip_temp_C: 105
      degradation_base: 0.015  # s/lap
      warmup_laps: 2
      parameters:
        k_0: 0.0
        k_1_lin: 0.015
        mu_peak: 1.75
        mu_sliding: 1.45
        load_sensitivity: -0.00005
    
    C2:
      name: "Medium-Hard"
      color: "Yellow"
      operating_range_C: [85, 105]
      peak_grip_temp_C: 98
      degradation_base: 0.025
      warmup_laps: 2
      parameters:
        k_0: 0.0
        k_1_lin: 0.025
        mu_peak: 1.85
        mu_sliding: 1.50
        load_sensitivity: -0.00005
    
    C3:
      name: "Medium"
      color: "Yellow"
      operating_range_C: [80, 100]
      peak_grip_temp_C: 93
      degradation_base: 0.040
      warmup_laps: 1
      parameters:
        k_0: 0.0
        k_1_lin: 0.040
        mu_peak: 1.95
        mu_sliding: 1.55
        load_sensitivity: -0.00005
    
    C4:
      name: "Soft-Medium"
      color: "Red"
      operating_range_C: [75, 95]
      peak_grip_temp_C: 88
      degradation_base: 0.065
      warmup_laps: 1
      parameters:
        k_0: 0.0
        k_1_lin: 0.065
        mu_peak: 2.05
        mu_sliding: 1.60
        load_sensitivity: -0.00005
    
    C5:  # Softest
      name: "Soft"
      color: "Red"
      operating_range_C: [70, 90]
      peak_grip_temp_C: 83
      degradation_base: 0.095
      warmup_laps: 1
      parameters:
        k_0: 0.0
        k_1_lin: 0.095
        mu_peak: 2.15
        mu_sliding: 1.65
        load_sensitivity: -0.00005
  
  wet_compounds:
    Intermediate:
      color: "Green"
      water_dispersion: "Medium"
      operating_temp_C: [60, 80]
      mu_wet: 1.4
    
    Wet:
      color: "Blue"
      water_dispersion: "High"
      operating_temp_C: [55, 75]
      mu_wet: 1.2
  
  physical_properties:
    front:
      width_mm: 305
      rim_inches: 18
      circumference_loaded_m: 2.262
      pressure_nominal_bar: 1.4
      pressure_min_bar: 1.2
      pressure_max_bar: 1.6
    
    rear:
      width_mm: 405
      rim_inches: 18
      circumference_loaded_m: 2.262
      pressure_nominal_bar: 1.2
      pressure_min_bar: 1.0
      pressure_max_bar: 1.4
  
  degradation_factors:
    track_abrasion: 1.0  # Multiplicateur selon circuit
    temperature_penalty: 0.02  # Par °C hors window
    locking_flat_spot: 0.050  # Pénalité instantanée
    marbles_effect: 0.010  # Sortie de piste
  
  inferred_from_data:
    source: "FastF1 2024-2025 seasons"
    circuits_analyzed: 18
    stints_processed: 450
    confidence_level: 0.87
```

---

## 10. Évaluation des Plateformes de Simulation

### 10.1 Critères d'Évaluation

| Critère | Poids | Description |
|---------|-------|-------------|
| **Performance Exécution** | 25% | Temps réel, capacité simulation multi-voitures |
| **Précision Physique** | 25% | Fidélité modèle véhicule, pneus, aero |
| **Facilité Développement** | 20% | Courbe apprentissage, écosystème libraries |
| **Visualisation** | 15% | Rendu graphique, debugging tools |
| **Intégration Données** | 10% | Import FastF1, export résultats |
| **Scalabilité** | 5% | Cloud, parallélisation |

### 10.2 Options Technologiques

#### Option A : Python Pur + Cython (Recommandé)

**Architecture** :
```
Python (orchestration)
├── NumPy/SciPy (calculs numériques)
├── Pandas (données télémétrie)
├── Cython (modules critiques optimisés)
│   ├── vehicle_dynamics.pyx
│   ├── tire_model.pyx
│   └── collision_detection.pyx
├── Matplotlib/Plotly (visualisation 2D)
└── Pygame/VisPy (rendu temps réel optionnel)
```

**Avantages** :
- ✓ Écosystème scientifique mature (SciPy, NumPy)
- ✓ Intégration native FastF1 (déjà en Python)
- ✓ Cython offre 10-100× acceleration sur code critique
- ✓ Prototypage rapide, testing facile
- ✓ Large communauté, documentation abondante

**Inconvénients** :
- ✗ GIL (Global Interpreter Lock) limite multi-threading
- ✗ Performance temps réel inférieure à C++ pur
- ✗ Visualisation 3D limitée vs moteurs jeu

**Performance Attendue** :
- Simulation 1 voiture : 50-100× temps réel (Cython activé)
- Simulation 20 voitures : 5-10× temps réel
- Précision physique : ± 2% vs données réelles

#### Option B : JavaScript/TypeScript + HTML5 Canvas/WebGL

**Architecture** :
```
TypeScript
├── Web Workers (calculs parallèles)
├── WebGL/Three.js (rendu 3D)
├── numeric.js ou custom (calculs physiques)
└── React/Vue (UI dashboard)
```

**Avantages** :
- ✓ Accessibilité (navigateur, pas d'installation)
- ✓ Visualisation 3D excellente (WebGL)
- ✓ Partage facile (URL)
- ✓ UI/UX moderne

**Inconvénients** :
- ✗ Performance calcul inférieur à Python/Cython
- ✗ Écosystème scientifique immature
- ✗ Intégration FastF1 complexe (nécessite backend)
- ✗ Précision floating-point variable selon browser

**Performance Attendue** :
- Simulation 1 voiture : 10-20× temps réel
- Simulation 10 voitures : 1-2× temps réel (limite)
- Précision physique : ± 5%

#### Option C : Approche Hybride Python + Web

**Architecture** :
```
Backend Python (FastAPI/Flask)
├── Moteur physique (Python+Cython)
├── API REST results
└── WebSocket temps réel

Frontend JavaScript
├── Visualisation 3D (Three.js)
├── Dashboard analytics
└── Contrôle simulation
```

**Avantages** :
- ✓ Meilleur des deux mondes
- ✓ Performance Python + UX Web
- ✓ Scalabilité (backend dédié)

**Inconvénients** :
- ✗ Complexité architecture
- ✗ Latence réseau
- ✗ Nécessite hébergement

### 10.3 Recommandation Finale

**Choix : Option A (Python + Cython)**

**Justification** :

1. **Alignement avec objectifs** :
   - Précision maximale requise → Python scientifique
   - Intégration FastF1 native → Même langage
   - Rétro-ingénierie intensive → Bibliothèques optimisées (SciPy, NumPy)

2. **Performance suffisante** :
   - Cython sur fonctions critiques (dynamics, tires) → 50-100× realtime
   - Suffisant pour calibration offline
   - Possibilité d'export C++ plus tard si besoin temps-réel strict

3. **Productivité développeur** :
   - Codebase existant en Python (RaceSim)
   - Testing unitaire facile (pytest)
   - Debugging interactif (Jupyter)

4. **Roadmap d'optimisation** :
   
   ```bash
   # Étape 1: Profiling
   python -m cProfile -o output.prof simulate.py
   
   # Étape 2: Cythonisation modules critiques
   # vehicle_dynamics.pyx
   cpdef update_vehicle_state(double[:] state, double dt):
       # Code optimisé C
   
   # Étape 3: Compilation
   python setup.py build_ext --inplace
   ```

5. **Coût/Bénéfice** :
   - Temps développement : 2-3 semaines pour prototype fonctionnel
   - Maintenance : faible (équipe familière Python)
   - Extension future : possible vers C++ si nécessaire

---

## 11. Recommandations d'Implémentation et Roadmap

### 11.1 Phasage du Projet

#### Phase 1 : Acquisition et Infrastructure (Semaines 1-2)

**Livrables** :
- [ ] Module `DataAcquirer` fonctionnel
- [ ] Cache local FastF1 configuré
- [ ] Pipeline validation qualité données
- [ ] Base de données circuits (6 circuits prioritaires)

**Critères d'Acceptation** :
- Téléchargement automatique sessions Q1/Q2/Q3
- Qualité données validée (>95% complétude)
- Stockage structuré (Parquet)

#### Phase 2 : Modules d'Extraction (Semaines 3-6)

**Livrables** :
- [ ] `PowerEstimator` (section 3)
- [ ] `GearboxCalculator` (section 4)
- [ ] `AeroModel` (section 5)
- [ ] `BrakeAnalyzer` (section 6)
- [ ] `ERSOptimizer` (section 7)
- [ ] `TireCharacterizer` (section 8)

**Critères d'Acceptation** :
- Chaque module produit estimations avec intervalles confiance
- Validation croisée entre circuits cohérente
- RMSE dans objectifs spécifiés

#### Phase 3 : Calibration et Validation (Semaines 7-8)

**Livrables** :
- [ ] Cross-validation Q1/Q2/Q3
- [ ] Comparaison données constructeurs
- [ ] Rapport incertitudes global
- [ ] Export configurations YAML

**Critères d'Acceptation** :
- P_ICE dans ±3% des valeurs annoncées
- Rapports boîte monotones et plausibles
- CxA/CzA cohérents entre circuits similaires

#### Phase 4 : Intégration Simulation (Semaines 9-10)

**Livrables** :
- [ ] Import configurations dans RaceSim
- [ ] Tests comparaison performances simulées vs réelles
- [ ] Documentation complète
- [ ] Notebook exemples (comme scaffold/gear_ratio_example.ipynb)

**Critères d'Acceptation** :
- Lap times simulés dans ±2% des réels
- Top speeds dans ±3 km/h
- Points freinage dans ±5 m

### 11.2 Structure de Code Recommandée

```
racesim/
├── telemetry_analysis/
│   ├── __init__.py
│   ├── data_acquisition.py      # FastF1 integration
│   ├── data_validation.py       # Quality checks
│   ├── segmentation.py          # Straights, corners detection
│   ├── power_estimation.py      # Engine power extraction
│   ├── gearbox_analysis.py      # Gear ratios
│   ├── aero_extraction.py       # CxA, CzA
│   ├── braking_analysis.py      # Brake performance
│   ├── ers_inference.py         # ERS strategy
│   └── tire_characterization.py # Grip, degradation
│
├── physics_models/
│   ├── __init__.py
│   ├── longitudinal_dynamics.pyx  # Cython optimisé
│   ├── lateral_dynamics.pyx
│   ├── tire_model.pyx
│   └── aero_model.py
│
├── optimization/
│   ├── __init__.py
│   ├── parameter_fitting.py     # SciPy optimizers
│   ├── bayesian_calibration.py  # PyMC3 pour incertitudes
│   └── cross_validation.py
│
├── config/
│   ├── circuits.yaml            # Circuit metadata
│   ├── f1_regulations_2024.yaml
│   └── f1_regulations_2026.yaml
│
└── outputs/
    ├── extracted_parameters/
    │   ├── powertrain_*.yaml
    │   ├── gearbox_*.yaml
    │   ├── aero_*.yaml
    │   └── tires_*.yaml
    │
    └── reports/
        ├── validation_summary.md
        └── uncertainty_analysis.pdf
```

### 11.3 Exemple de Configuration Finale

```yaml
# f1_car_complete_2026.yaml
# Généré automatiquement par le pipeline de rétro-ingénierie

metadata:
  extraction_date: "2025-01-15"
  data_sources: ["FastF1 2024 Season", "FIA Technical Regulations 2026"]
  circuits_analyzed: ["Monza", "Spa", "Monaco", "Silverstone", "Bahrain", "Jeddah"]
  confidence_score: 0.89

powertrain:
  ice:
    max_power_kw: 685
    max_rpm: 12500
    torque_curve: [...]  # Array interpolé
  
  ers:
    mgu_k_power_kw: 350
    battery_capacity_MJ: 33
    deployment_strategy: "quali_optimized"

gearbox:
  num_gears: 8
  final_drive: 3.52
  ratios: [4.05, 2.95, 2.35, 1.92, 1.62, 1.35, 1.15, 0.95]
  shift_time_ms: 45

aero:
  CxA_DRS_open: 0.95
  CxA_DRS_closed: 1.15
  CzA: 3.45
  efficiency_ratio: 3.63
  drs_reduction_percent: 17

braking:
  max_decel_G: 5.4
  bias_front_percent: 57.5
  brake_material: "Carbon-Carbon"

tires:
  supplier: "Pirelli"
  compounds_available: ["C1", "C2", "C3", "C4", "C5"]
  current_compound: "C3"
  mu_peak: 2.05
  degradation_model: "lin"
  k_1: 0.040

reference_trajectory:
  racing_line_csv: "monza_q3_reference.csv"
  braking_points_yaml: "monza_braking_ref.yaml"
  apex_speeds: [...]
```

### 11.4 Matrice des Risques

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Données FastF1 incomplètes | Moyenne | Élevé | Multipler sources (FP1, FP2, Course) |
| Outliers non détectés | Faible | Moyen | Validation croisée drivers |
| Modèle physique trop simplifié | Moyenne | Moyen | Itérations avec données réelles |
| Changements règlement 2026 | Faible | Élevé | Suivi technique FIA régulier |
| Performance simulation insuffisante | Faible | Faible | Cython + profiling précoce |

---

## Conclusion

Cette spécification détaille une méthodologie complète et rigoureuse pour extraire les paramètres F1 2026 depuis la télémétrie FastF1. L'approche combine :

1. **Rigueur scientifique** : Modèles physiques validés, optimisation numérique, analyse statistique
2. **Pragmatisme industriel** : Segmentation thématique, livrables clairs, critères d'acceptation mesurables
3. **Flexibilité technologique** : Python+Cython pour performance/développement équilibrés

La précision cible (±3% sur puissance, ±5% sur aero) est ambitieuse mais atteignable avec une collecte de données exhaustive et une validation croisée systématique.

**Prochaines étapes immédiates** :
1. Valider cette spécification avec stakeholders
2. Initialiser repository Git dédié
3. Commencer Phase 1 (acquisition données Monza 2024)
4. Produire premier notebook exemple (similaire à scaffold/gear_ratio_example.ipynb)
