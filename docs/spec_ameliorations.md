# Spécification Détaillée : Améliorations RaceSim F1 & Architecture Data-Driven

## 1. Introduction et Contexte

### 1.1 Objectifs du Projet
Cette spécification détaille la refonte complète du simulateur RaceSim F1 vers une **architecture data-driven modulaire**, capable de s'adapter dynamiquement aux évolutions réglementaires (2006, 2014, 2026, etc.) sans modification du code source. Elle intègre les dernières avancées en modélisation physique (splines cubiques, hybride symbolique-ML) et définit un système de base de données centralisé pour gérer règlements, écuries, circuits et configurations.

**Objectifs Clés :**
1.  **Adaptabilité Réglementaire** : Bascule 2024 → 2026 via simple changement de configuration BDD.
2.  **Précision Physique Maximale** : Splines cubiques pour tous les phénomènes non-linéaires (erreur < 2%).
3.  **Modularité Technologique** : Activation/désactivation dynamique de composants (Turbo, MGU-H, X-Mode).
4.  **Centralisation des Données** : SQLite comme source unique de vérité.
5.  **Calibration Automatique** : Rétro-ingénierie via FastF1 pour affiner les modèles.

### 1.2 Périmètre des Améliorations
- **Moteur** : Refonte complète avec gestion ERS avancée, consommation carburant, 5 modes moteur, composants modulaires.
- **Pneus** : Modèle thermique complet, usure dynamique, pression, blistering/graining, surface de réponse spline 3D.
- **Aérodynamique** : GAM (Generalized Additive Models), aéro actif 2026 (X-Mode/Z-Mode), DRS.
- **Boîte de Vitesses** : Temps de passage réalistes, détection shifts par splines.
- **Châssis/Suspensions** : Modélisation flexible, effet de sol paramétrable.
- **Base de Données** : Schéma SQLite complet pour règlements, teams, tracks, configs.
- **Bancs de Test** : Modules de validation isolée par composant.
- **IA Pilote** : Apprentissage automatique pour trajectoires optimales.

---

## 2. Architecture Data-Driven (SQLite)

### 2.1 Schéma de Base de Données

Le cœur du système est une base SQLite (`f1_sim.db`) structurant toutes les connaissances techniques.

```sql
-- Table des Règlements Généraux par Année
CREATE TABLE regulations (
    year INTEGER PRIMARY KEY,
    era_name TEXT, -- ex: 'V6 Turbo Hybrid', 'NA V10', 'V8'
    min_weight_kg REAL, -- kg
    max_fuel_flow_kg_h REAL, -- kg/h
    fuel_capacity_kg REAL, -- kg
    ers_max_deployment_kw REAL, -- kW (120 pour 2024, 350 pour 2026)
    ers_max_energy_per_lap_mj REAL, -- MJ
    has_mgu_h BOOLEAN,
    has_active_aero BOOLEAN,
    drag_reduction_factor REAL, -- Pour DRS ou X-Mode
    active_aero_threshold_speed_kmh REAL, -- km/h (ex: 290 pour X-Mode)
    engine_formula TEXT -- 'V6_TURBO', 'V8_NA', etc.
);

-- Table des Composants Technologiques (Library)
CREATE TABLE tech_components (
    id INTEGER PRIMARY KEY,
    name TEXT, -- 'Turbocharger', 'MGU-H', 'X-Mode Actuator'
    type TEXT, -- 'POWERTRAIN', 'AERO', 'CHASSIS', 'ERS'
    min_year INTEGER,
    max_year INTEGER,
    model_class_path TEXT, -- Chemin vers la classe Python
    is_optional BOOLEAN, -- True si peut être désactivé par règle
    power_contribution_kw REAL, -- kW contribué
    efficiency_factor REAL -- Rendement
);

-- Table des Écuries et Spécificités
CREATE TABLE teams (
    id INTEGER PRIMARY KEY,
    name TEXT, -- 'Red Bull Racing', 'Ferrari', 'Mercedes'
    engine_supplier TEXT,
    chassis_efficiency_factor REAL, -- Correctif aérodynamique spécifique (CxA relatif)
    cog_offset_mm REAL, -- mm
    weight_distribution_front_pct REAL, -- %
    brake_bias_default_pct REAL, -- %
    cooling_efficiency REAL -- Impacte températures moteur/pneus
);

-- Table des Circuits et Configurations
CREATE TABLE tracks (
    id INTEGER PRIMARY KEY,
    name TEXT,
    country TEXT,
    length_m REAL, -- mètres
    track_map_spline_blob BLOB, -- Coordonnées splines de la piste (x, y, z, curvature)
    surface_friction_base REAL, -- μ de référence
    elevation_gain_m REAL, -- mètres
    sectors_data JSON, -- Données sectorielles (vitesse moy, DRS zones)
    corners_data JSON -- Apex, entry/exit speeds de référence
);

-- Table des Configurations Voiture (Lien Règlement + Écurie + Circuit)
CREATE TABLE car_configs (
    id INTEGER PRIMARY KEY,
    team_id INTEGER,
    year INTEGER,
    track_id INTEGER,
    setup_json JSON, -- Setup spécifique (aileron avant/arrière, hauteur caisse, camber, toe)
    tire_compound_start TEXT, -- 'SOFT', 'MEDIUM', 'HARD', 'INTER', 'WET'
    fuel_load_start_kg REAL, -- kg
    ers_strategy TEXT, -- 'AGGRESSIVE', 'DEFENSIVE', 'BALANCED'
    calibration_coeffs_json JSON, -- Coefficients de correction ML issus de FastF1
    FOREIGN KEY(team_id) REFERENCES teams(id),
    FOREIGN KEY(year) REFERENCES regulations(year),
    FOREIGN KEY(track_id) REFERENCES tracks(id)
);

-- Table des Résultats de Simulation et Télémétrie
CREATE TABLE simulation_runs (
    id INTEGER PRIMARY KEY,
    config_id INTEGER,
    timestamp DATETIME,
    driver_name TEXT,
    telemetry_blob BLOB, -- Données brutes compressées (vitesse, rpm, throttle, brake, etc.)
    lap_times_json JSON, -- Liste des temps par tour
    sector_times_json JSON,
    tire_wear_final_json JSON, -- % usure par pneu
    fuel_consumed_kg REAL, -- kg
    ers_usage_stats_json JSON, -- Stats déploiement/récupération
    validity_status TEXT, -- 'VALID', 'INVALIDATED', 'PENDING'
    FOREIGN KEY(config_id) REFERENCES car_configs(id)
);

-- Table des Courbes de Référence (Splines Coefficients)
CREATE TABLE spline_curves (
    id INTEGER PRIMARY KEY,
    component_type TEXT, -- 'ENGINE_TORQUE', 'AERO_CX', 'TIRE_GRIP'
    year INTEGER,
    team_id INTEGER,
    curve_type TEXT, -- 'UNIVARIATE', 'B_SPLINE', 'GAM'
    coefficients_blob BLOB, -- Coefficients scipy pickle
    knots_blob BLOB, -- Nœuds de la spline
    metadata_json JSON -- Conditions de validité (temp, pression, etc.)
);
```

### 2.2 Gestion des "Breaking Changes" Réglementaires

Les changements majeurs sont gérés par des entrées distinctes dans `regulations` :

| Année | Era | Changements Majeurs | Implémentation BDD |
|-------|-----|---------------------|---------------------|
| **2006** | V8 NA | Suppression V10, réduction puissance | `engine_formula='V8_NA'`, `ers_max_deployment_kw=0` |
| **2014** | V6 Turbo Hybrid | Introduction ERS, Turbo | `has_mgu_h=True`, `ers_max_deployment_kw=120` |
| **2022** | Ground Effect | Retour effet de sol | `chassis_efficiency_factor` ajusté, nouveau modèle aero |
| **2026** | Sustainable Fuel | ERS 350kW, X-Mode, suppression MGU-H | `has_mgu_h=False`, `ers_max_deployment_kw=350`, `has_active_aero=True` |

**Mécanisme d'Adaptation :**
Le `VehicleFactory` lit l'année cible, récupère la ligne correspondante, et assemble dynamiquement la voiture :
- Si `has_mgu_h == False` → Le composant MGU-H n'est pas instancié.
- Si `ers_max_deployment_kw == 350` → La batterie et le MGU-K sont dimensionnés pour 350kW.
- Si `has_active_aero == True` → L'aile arrière inclut l'actionneur X-Mode.

Aucune modification de code Python n'est requise pour supporter une nouvelle saison.

---

## 3. Spécifications des Améliorations Physiques

### 3.1 Moteur V2 : Architecture Modulaire & Splines

#### 3.1.1 Décomposition en Composants
Le moteur n'est plus une classe monolithique mais un assemblage de composants :

```python
class PowertrainAssembly:
    def __init__(self, components: List[Component]):
        self.components = {c.name: c for c in components}
    
    def get_total_torque(self, rpm: float, speed: float, soc: float) -> float:
        torque = self.components['ICE'].get_torque(rpm)
        
        # Turbo uniquement si présent (règle année)
        if 'Turbo' in self.components:
            boost = self.components['Turbo'].get_boost(rpm, throttle)
            torque *= boost
        
        # MGU-H uniquement si règle l'autorise
        if 'MGU-H' in self.components:
            mgu_h_power = self.components['MGU-H'].harvest(exhaust_energy)
        
        # MGU-K (toujours présent en ère hybride)
        mguk_power = self.components['MGU-K'].deploy(soc, demand)
        torque += power_to_torque(mguk_power, rpm)
        
        return torque
```

#### 3.1.2 Courbe de Couple par Spline
- **Données** : Points (RPM, Torque) issus du règlement + calibration FastF1.
- **Modèle** : `UnivariateSpline(RPM, Torque, s=0.95)` (lissage optimal).
- **Avantage** : Dérivées continues C² pour stabilité intégrateur, précision ±2%.

#### 3.1.3 Modes Moteur (5 Stratégies)
1.  **Quali Mode** : Puissance max, ignore consommation/ERS limits temporaires.
2.  **Race Mode** : Équilibre conso/ERS.
3.  **Harvest Mode** : Priorité recharge batterie (freinage moteur accru).
4.  **Overtake Mode** : Déploiement ERS maximal sur courte période.
5.  **Save Mode** : Réduction puissance ICE pour économiser carburant.

Chaque mode modifie les paramètres de déploiement ERS et le mapping accélérateur.

### 3.2 Pneus V2 : Modèle Thermique & Usure Avancée

#### 3.2.1 Surface de Réponse Spline 3D
Le grip n'est plus linéaire mais suit une surface complexe :
```python
# μ = f(slip_angle, vertical_load, temperature)
grip_surface = SmoothBivariateSpline(slip_angles, loads, temperatures, mu_values)
mu_peak = grip_surface.ev(optimal_slip, current_load, current_temp)
```

#### 3.2.2 Phénomènes Modélisés
- **Montée en température** : Inertie thermique, conduction carcasse vs surface.
- **Usure** : Fonction non-linéaire de la puissance dissipée (glissement).
- **Blistering** : Seuil température critique → chute brutale de grip (modélisé par spline monotone décroissante post-seuil).
- **Graining** : Accumulation de gomme sur basse température/glissement latéral élevé.
- **Pression Dynamique** : Variation avec température (loi gaz parfait corrigée).

#### 3.2.3 Calibration
Les coefficients de la surface de grip sont calibrés par rétro-ingénierie sur les données FastF1 (différences de temps entre compounds).

### 3.3 Aérodynamique : GAM & Aéro Actif

#### 3.3.1 Generalized Additive Models (GAM)
La traînée et l'appui ne suivent plus une simple loi en v² :
```python
from pygam import LinearGAM, s

# Cx = f(vitesse, angle_yaw, roulis, tangage, DRS, X-Mode)
gam_cx = LinearGAM(s(0) + s(1) + s(2) + s(3) + s(4, by=5))
gam_cx.fit(X=[speed, yaw, roll, pitch, drs_state, xmode_active], y=Cx_measured)
```

#### 3.3.2 Aéro Actif 2026 (X-Mode / Z-Mode)
- **X-Mode** : Au-delà de 290 km/h, réduction Cx de 55% (ailes mobiles).
- **Z-Mode** : En dessous de 290 km/h ou en freinage, configuration appui max.
- **Transition** : Modélisée par une sigmoïde (smoothstep) pour éviter les discontinuités physiques.

### 3.4 Boîte de Vitesses : Détection Spline

#### 3.4.1 Algorithme de Détection de Shifts
Utilisation de `LSQUnivariateSpline` sur la courbe RPM(t) :
1.  Lisser les données RPM avec contraintes de nœuds.
2.  Calculer dérivée première (accélération angulaire).
3.  Détecter pics négatifs dans dérivée seconde → Passage de rapport.
4.  Extraire ΔRPM et durée (<50ms typique).

#### 3.4.2 Temps de Passage Réaliste
- **Couple interrupt** : 3-5 ms (shifts up).
- **Inertie** : Prise en compte inertie arbres pour calculer temps de synchronisation.
- **Impact Performance** : Perte de vitesse modélisée précisément.

### 3.5 Châssis & Suspensions

#### 3.5.1 Effet de Sol Paramétrable
- **Hauteur de caisse** : Impact direct sur Cz (loi spline décroissante).
- **Porpoising** : Oscillation aérodynamique modélisée par ressort-amortisseur non-linéaire couplé à Cz(hauteur).
- **Rigidité** : Facteur configurable par équipe (Red Bull vs Ferrari).

#### 3.5.2 Flexibilité
- **Aileron avant** : Déformation sous charge (impact incidence effective).
- **Plancher** : Flexion en haute vitesse (réduction progressive d'appui).

---

## 4. Système de Calibration Automatique (FastF1)

### 4.1 Pipeline de Rétro-Ingénierie

1.  **Acquisition** : Téléchargement sessions Q1/Q2/Q3/Course via FastF1.
2.  **Segmentation** : Découpage automatique en tours, secteurs, phases (accélération, freinage, cornering).
3.  **Extraction Paramètres** :
    - Puissance moteur : Optimisation non-linéaire sur lignes droites.
    - Rapports boîte : Analyse sauts RPM.
    - Cx/Cz : Balance énergétique (Puissance = Traînée × Vitesse).
    - Grip pneus : Accélération latérale max en virage.
4.  **Ajustement Splines** : Mise à jour des coefficients dans `spline_curves`.
5.  **Validation** : Simulation du tour de référence → Comparaison temps (<0.5% écart).

### 4.2 Correction par Machine Learning
Un modèle léger (Random Forest ou Gradient Boosting) apprend les écarts résiduels entre théorie (règlement) et réalité (télémétrie) :
```python
correction_model = GradientBoostingRegressor()
correction_model.fit(X_theoretical_params, y_real_telemetry_delta)
```
Ce modèle est stocké dans `calibration_coeffs_json` et appliqué en runtime.

---

## 5. Bancs de Test et Validation

### 5.1 Architecture de Testing
Module `test_bench.py` permettant de tester isolément chaque composant :

- **Engine Bench** :
  - Entrée : Cycle RPM/throttle.
  - Sortie : Courbes Couple/Puissance/Conso/Température.
  - Validation : Comparaison avec specs constructeur + FastF1.

- **Aero Bench** :
  - Entrée : Plage vitesses, angles (yaw, pitch, roll), état DRS/X-Mode.
  - Sortie : Cx, Cz, centre de poussée.
  - Validation : Soufflerie virtuelle vs CFD référence.

- **Tire Bench** :
  - Entrée : Slip angle, charge, température initiale.
  - Sortie : Force latérale/longitudinale, usure, évolution température.
  - Validation : Données Pirelli + dégradation observée en course.

- **Full Car Bench** :
  - Simulation tour complet sur circuit de référence.
  - Comparaison télémétrie complète (vitesse, positions, temps secteurs).

### 5.2 Critères d'Acceptation
- **Temps au tour** : Écart < 0.5% vs meilleur tour officiel.
- **Vitesse pointe** : Écart < 3 km/h.
- **Décélération max** : Écart < 0.2G.
- **Usure pneus** : Corrélation qualitative (tendance) validée.
- **Consommation carburant** : Écart < 5% vs données course.

---

## 6. Roadmap d'Implémentation

### Semaine 1-2 : Socle Data-Driven
- [ ] Création schéma SQLite (`f1_sim.db`).
- [ ] Migration données statiques (car.py, engine.py) → BDD.
- [ ] Développement `DBManager` (ORM léger).
- [ ] Implémentation `VehicleFactory` (assemblage dynamique).

### Semaine 3-5 : Moteur Physique Spline
- [ ] Intégration `scipy.interpolate` (UnivariateSpline, LSQUnivariateSpline).
- [ ] Refonte classe `Engine` → `PowertrainAssembly` modulaire.
- [ ] Refonte classe `Tires` → Surface de réponse spline 3D.
- [ ] Refonte classe `Aero` → GAM + gestion X-Mode.
- [ ] Refonte classe `GearBox` → Détection shifts par splines.

### Semaine 6-8 : Calibration & ML
- [ ] Connexion API FastF1.
- [ ] Algorithmes extraction puissance, rapports, aéro.
- [ ] Entraînement modèles de correction (Gradient Boosting).
- [ ] Peuplement automatique table `spline_curves`.
- [ ] Tests validation sur saisons 2022, 2023, 2024.

### Semaine 9-10 : Interfaces & Extensions
- [ ] Prototype GUI (PyQt6) pour édition configs BDD.
- [ ] Bancs de test automatisés (`test_bench.py`).
- [ ] Documentation API complète.
- [ ] Support multi-circuits (10 circuits de référence).
- [ ] Optimisation Cython pour temps réel.

---

## 7. Stack Technologique

```yaml
langage: Python 3.10+
base_de_donnees: SQLite3 (natif)
bibliotheques_physique:
  - scipy>=1.10.0      # UnivariateSpline, LSQUnivariateSpline, splprep
  - numpy>=1.24.0      # Calcul matriciel
  - sympy>=1.11.0      # Équations symboliques, génération code Cython
  - pygam>=0.9.0       # Generalized Additive Models (aéro)
bibliotheques_ml:
  - scikit-learn>=1.2  # GradientBoostingRegressor, cross_val_score
  - pymc>=5.0.0        # Optionnel: calibration bayésienne
donnees_f1:
  - fastf1>=3.8.0      # Télémétrie officielle
interface:
  - PyQt6              # GUI future (édition BDD, visualisation)
  - matplotlib         # Graphiques analyse
performance:
  - cython>=3.0.0      # Accélération boucles critiques
  - numba              # JIT compilation alternative
```

---

## 8. Conclusion

Cette spécification définit la transformation de RaceSim en une plateforme d'ingénierie virtuelle de niveau professionnel. L'approche **data-driven** couplée à la **modularité des composants** garantit une pérennité face aux évolutions réglementaires futures. Les **splines cubiques** et l'**hybridation ML** assurent une précision physique inédite (<0.5% d'erreur sur temps tour). Le système de **base de données centralisée** ouvre la voie à des interfaces graphiques avancées et à une gestion simplifiée des configurations multi-équipes/multi-saisons.

La roadmap sur 10 semaines permet une montée en compétence progressive avec des livrables intermédiaires validés par des bancs de test dédiés. Cette architecture positionne RaceSim comme un outil de référence pour l'analyse de performance F1 open-source.
