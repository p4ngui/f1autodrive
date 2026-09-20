# Dossier d'Architecture Détaillée - RaceSim F1

## 1. Vue d'Ensemble du Système

### 1.1 Description Générale
RaceSim est un simulateur de course automobile inspiré de la Formule 1, développé en Python avec Pygame pour le rendu graphique. Le système implémente un modèle de véhicule cinématique 2D avec une simulation dynamique des pneus, moteur, et boîte de vitesses.

### 1.2 Objectifs Actuels
- Simulation de voitures de course autonomes utilisant des réseaux de neurones (NEAT)
- Modélisation physique simplifiée des véhicules
- Gestion des pneus et dégradation
- Support de multiples circuits (Monza, Mugello, Spa, Portimao, Le Mans)

---

## 2. Architecture Logicielle

### 2.1 Diagramme des Composants

```
┌─────────────────────────────────────────────────────────────────┐
│                         Game Controller                          │
│                        (game.py)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────┐
│    Track      │   │      Car        │   │  NNdraw      │
│  (track.py)   │   │   (car.py)      │   │  (NNdraw.py) │
└───────────────┘   └────────┬────────┘   └──────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌─────────────────┐   ┌──────────────┐
│    Engine     │   │    Gearbox      │   │    Tires     │
│ (engine.py)   │   │  (gearbox.py)   │   │ (tires.py)   │
└───────────────┘   └─────────────────┘   └──────────────┘
```

### 2.2 Hiérarchie des Classes

#### Classe Principale: `Game` (game.py)
- **Responsabilité**: Contrôleur principal du jeu
- **Attributs clés**:
  - `cars`: Liste des objets Car
  - `track`: Objet Track
  - `nets`: Réseaux de neurones NEAT
  - `generation`: Compteur de génération AI
- **Méthodes principales**:
  - `startRace()`: Initialisation de la course
  - `buildTrack()`: Construction du circuit
  - `set_clock()`: Configuration du timing

#### Classe: `Car` (car.py)
- **Responsabilité**: Représentation complète du véhicule
- **Héritage**: `pygame.sprite.Sprite`
- **Composition**:
  - `KinematicBicycleModel`: Modèle cinématique
  - `Engine`: Moteur thermique/hybride
  - `GearBox`: Boîte de vitesses
  - `Tires`: Système de pneus
- **Attributs clés**:
  - Dimensions: `length=5.4m`, `width=2.0m`, `wheel_base≈3.49m`
  - Masse: `total_weight_kg=984kg` (794+110+80)
  - Performance: `max_acceleration=19.61m/s²`, `max_speed=70m/s`
  - Capteurs: 5 capteurs de distance (front, latéraux, diagonaux)
- **État dynamique**:
  - `position`: Vector2(x, y)
  - `velocity`: Vector2
  - `yaw`: Orientation [degrés]
  - `steering`: Angle de braquage [degrés]
  - `actions`: [throttle, steer_left/right, brake]

#### Classe: `KinematicBicycleModel` (car.py)
- **Responsabilité**: Modèle cinématique 2D du véhicule
- **Équations implémentées**:
  ```python
  new_velocity = velocity + (delta_time * acceleration)
  angular_velocity = new_velocity * tan(steering_angle) / wheelbase
  new_x = x + velocity * cos(yaw) * delta_time
  new_y = y + velocity * sin(yaw) * delta_time
  new_yaw = normalize_angle(yaw + angular_velocity * delta_time)
  ```

#### Classe: `Engine` (engine.py)
- **Responsabilité**: Simulation de la puissance moteur
- **Type**: Moteur hybride (combustion + électrique)
- **Spécifications actuelles**:
  - `HP_combustion_max`: 701 kW (~940 HP)
  - `HP_electric_max`: 120 kW (~161 HP)
  - `RPM_max`: 11,400 RPM
  - `RPM_end`: 12,200 RPM
- **Courbe de puissance**: Approximation polynomiale cubique
- **Système hybride**:
  - MGU-K: 120 kW maximum
  - Récupération au freinage: η=0.15
  - Turbo électrique: η=0.10

#### Classe: `GearBox` (gearbox.py)
- **Responsabilité**: Gestion des rapports de transmission
- **Configuration**: 8 rapports + marche arrière
- **Rapports actuels** (`i_trans`):
  ```
  [0.04, 0.070, 0.095, 0.117, 0.143, 0.172, 0.190, 0.206]
  ```
- **Régime de passage**: 10,000-13,000 RPM
- **Efficacité**: 96%

#### Classe: `Tires` (tires.py)
- **Responsabilité**: Dynamique des pneus et dégradation
- **Dimensions F1 2023**:
  - Avant: 305mm/720mm-18"
  - Arrière: 405mm/720mm-18"
- **Modèle de force**:
  - `F_x = μ * (μ_mux + dμx/dFz * (F_z - F_z0)) * F_z`
  - Prise en compte du transfert de charge longitudinal/latéral
  - Downforce aérodynamique intégrée
- **Composés**: A3 (tendre), A4 (medium), A5 (dur)
- **Modèles de dégradation**: Linéaire, quadratique, cubique, logarithmique

#### Classe: `Track` (track.py)
- **Responsabilité**: Représentation du circuit
- **Format de données**: CSV ou GeoJSON
- **Éléments**:
  - Ligne de centre
  - Bordures gauche/droite
  - Ligne de départ/arrivée
  - Stand (pit lane)

---

## 3. Flux de Données

### 3.1 Boucle de Simulation Principale

```
1. Input AI (réseau de neurones)
   ↓
2. Décodage des actions [throttle, steering, brake]
   ↓
3. Mise à jour de l'accélération (engine.py + gearbox.py)
   ↓
4. Mise à jour de l'angle de braquage
   ↓
5. Calcul cinématique (KinematicBicycleModel.update())
   ↓
6. Calcul des forces pneumatiques (tires.py)
   ↓
7. Mise à jour de la position
   ↓
8. Détection de collision
   ↓
9. Mise à jour des capteurs
   ↓
10. Calcul du fitness (IA)
```

### 3.2 Calcul de la Puissance Délivrée

```
Throttle Position (%) 
    ↓
[Engine.calc_torque_distr()]
    ├── Torque ICE (courbe polynomiale)
    └── Torque MGU-K (si conditions remplies)
    ↓
[GearBox.get_gear()] → Rapport sélectionné
    ↓
[Tires.r_driven_tire()] → Rayon effectif
    ↓
Force motrice = (Torque × i_trans × η_g) / r_tire
    ↓
Accélération = Force / Masse
```

---

## 4. Structure des Données

### 4.1 Fichiers de Configuration Voiture

**Format INI** (`cars/MER.ini`, `cars/F1VET.ini`):
```ini
[General]
Weight: 733  # Kg
Center of gravity height: 0.205  # m
Weight distribution: 46:54 (F:R)
Base drag: 0.32

[Engine]
Max. Power: 929 hp @ 13250 rpm
Max. Torque: 510.5 Nm @ 12000 rpm
Rev limit range: [11500, 13000] rpm
```

**Format JSON intégré** (dans car.py):
```python
car_pars = {
    "Mercedes": {
        "drivetype": "combustion",
        "t_car": 0.0,  # temps perdu par tour
        "m_fuel": 110.0,  # kg carburant initial
        "b_fuel_perlap": 1.782,  # kg/tour
        "t_pit_tirechange_add": 0.434,  # secondes standstill
        ...
    }
}
```

### 4.2 Paramètres de Pneus par Pilote

```python
tireset_pars = {
    "HAM": {
        "tire_deg_model": "lin",
        "mult_tiredeg_sc": 0.25,
        "t_add_coldtires": 1.0,
        "A3": {
            "k_0": 0.615,  # offset temps frais
            "k_1_lin": 0.107,  # dégradation linéaire [s/lap]
            ...
        }
    }
}
```

### 4.3 Constantes Globales (`constants.py`)

```python
PPM = 10  # Pixels per meter
MMTOMETERS = 1/1000
STEERING_SPEED = 7.5  # °/s
SENSOR_DISTANCE = 300  # px
INPUT_NEURONS = 6
OUTPUT_NEURONS = 2
SEASON = 2023
```

---

## 5. Interfaces et Couplages

### 5.1 Couplages Forts

| Module | Dépend de | Type de couplage |
|--------|-----------|------------------|
| `Car` | `Engine`, `GearBox`, `Tires` | Composition forte |
| `Car` | `KinematicBicycleModel` | Composition |
| `Game` | `Car`, `Track`, `NNdraw` | Agrégation |
| `Engine` | `GearBox` (via `calc_m_requ`) | Couplage faible |

### 5.2 Points d'Extension Identifiés

1. **Système de carburant**: Non implémenté dans la boucle dynamique
2. **ERS complet**: Seul MGU-K partiellement modélisé
3. **DRS**: Facteur présent mais non dynamique
4. **Usure des freins**: Non modélisée
5. **Conditions météo**: Absentes
6. **Stratégie de course**: Limitée aux pneus

---

## 6. Technologies Utilisées

### 6.1 Bibliothèques Principales
- **Pygame**: Rendu graphique et gestion des événements
- **NumPy**: Calculs vectoriels et matrices
- **Shapely**: Géométrie 2D (collisions, intersections)
- **NEAT-Python**: Réseaux de neurones évolutifs
- **Matplotlib**: Visualisation des courbes (debug)

### 6.2 Formats de Données
- **CSV**: Tracés de circuit
- **GeoJSON**: Données GPS de circuits réels
- **INI**: Configuration véhicules
- **PNG**: Sprites et textures

---

## 7. Limitations Actuelles

### 7.1 Physique
- Modèle cinématique 2D uniquement (pas de suspension)
- Pas de transfert de charge dynamique en temps réel
- Forces pneumatiques simplifiées (modèle linéaire)
- Aérodynamique statique (pas de DRS dynamique, pas de sillage)

### 7.2 Groupe Motopropulseur
- Courbe de puissance fixe (non configurable par saison)
- Pas de gestion de la consommation en temps réel
- ERS simplifié (pas de MGU-H, pas de stratégie de déploiement)
- Pas de modes moteur (Qualif, Course, Économie)

### 7.3 Pneus
- Température des pneus non modélisée
- Pression des pneus statique
- Usure visuelle absente
- Pas de blistering/graining

### 7.4 IA
- Réseaux de neurones feedforward simples
- Pas d'apprentissage par renforcement profond
- Capteurs limités (5 raycasts)
- Pas de mémoire temporelle (LSTM/GRU)

---

## 8. Métriques de Performance

### 8.1 Performances Actuelles (estimées)
- **Vitesse max**: 70 m/s = 252 km/h (sous-estimé vs F1 réelle ~350 km/h)
- **Accélération max**: 19.61 m/s² ≈ 2G (F1 réelle: 5-6G en freinage)
- **Freinage**: 55.9 m/s² ≈ 5.7G (correct)
- **Régime moteur**: 11,400-12,200 RPM (conforme F1 2023)

### 8.2 Écarts vs F1 Réelle 2023
| Paramètre | Simulation | F1 Réelle 2023 | Écart |
|-----------|-----------|----------------|-------|
| Puissance totale | 821 kW | ~740 kW (ICE) + 120 kW (ERS) | +8% |
| Masse minimale | 984 kg | 798 kg (min) + pilote | +10% |
| Vitesse max | 252 km/h | 350+ km/h | -28% |
| Accélération 0-100 | ~2.5s (est.) | <2.6s | OK |
| Downforce | Statique | 5G en virage | Non modélisé |

---

## 9. Sécurité et Robustesse

### 9.1 Gestion des Erreurs
- Vérification des limites de régime moteur
- Clamp des angles de braquage
- Protection contre les divisions par zéro
- Validation des entrées IA (threshold 0.1-0.5)

### 9.2 Problèmes Connus
- IndexError potentiel dans `GearBox.get_gear()` (ligne 41-43)
- Commentaires contradictoires sur les dimensions de voiture
- Variables non initialisées (`cog`, `mass_gravity`)
- Code mort (méthodes `cond()`, `reset()`, `t_to_v()`)

---

## 10. Évolutivité

### 10.1 Points Forts
- Architecture modulaire (classes séparées)
- Configuration externalisée (fichiers INI/JSON)
- Support multi-circuits
- Système de composés de pneus extensible

### 10.2 Points Faibles
- Couplage fort Car↔Engine↔GearBox↔Tires
- Peu de tests unitaires
- Documentation inline limitée
- Hardcoding de nombreuses constantes

---

## 11. Recommandations Architecturales

### 11.1 Court Terme
1. Implémenter un système de configuration unifié (YAML/JSON)
2. Ajouter des tests unitaires pour chaque module physique
3. Documenter les unités de toutes les variables
4. Corriger les incohérences de dimensions véhicule

### 11.2 Moyen Terme
1. Introduire un pattern Observer pour les événements de course
2. Séparer la logique métier du rendu Pygame
3. Implémenter un vrai modèle de suspension
4. Ajouter la gestion de la consommation carburant/ERS

### 11.3 Long Terme
1. Migration vers un moteur physique 3D (optionnel)
2. Intégration de vrais circuits F1 2026
3. Support du multijoueur réseau
4. API de télémétrie pour analyse de données

---

*Document généré: 2024*
*Version: 1.0*
*Auteur: Assistant Ingénieur Mécanique Motorsport & Software Senior*
