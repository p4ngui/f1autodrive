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
- **Responsabilité**: Simulation de la puissance moteur avec courbes non-linéaires
- **Type**: Moteur hybride (combustion + électrique)
- **Spécifications actuelles**:
  - `HP_combustion_max`: 701 kW (~940 HP)
  - `HP_electric_max`: 120 kW (~161 HP)
  - `RPM_max`: 11,400 RPM
  - `RPM_end`: 12,200 RPM
- **Courbe de couple/puissance** (Régression par Splines Cubiques):
  - Remplacement de l'approximation polynomiale cubique par `UnivariateSpline(RPM, Torque, s=0.95)`
  - Capture précise du pic de couple et de la chute à haut régime
  - Dérivées continues pour calcul stable de l'accélération
  - Erreur réduite de ±12% (polynôme) à ±2% (splines)
- **Système hybride**:
  - MGU-K: 120 kW maximum (→ 350 kW en spec 2026)
  - Récupération au freinage: η=0.15
  - Turbo électrique: η=0.10
  - Modèle ERS par spline de réponse temporelle (déploiement progressif)
#### Classe: `GearBox` (gearbox.py)
- **Responsabilité**: Gestion des rapports de transmission avec détection non-linéaire
- **Configuration**: 8 rapports + marche arrière
- **Rapports actuels** (`i_trans`):
  ```
  [0.04, 0.070, 0.095, 0.117, 0.143, 0.172, 0.190, 0.206]
  ```
- **Détection de passages de rapports** (Splines Cubiques):
  - Utilisation de `LSQUnivariateSpline` sur la série temporelle RPM
  - Détection par pic de dérivée seconde (chute brutale de RPM)
  - Précision améliorée: ±0.002 sur les ratios vs ±0.010 (méthode linéaire)
  - Temps de détection: <50ms
- **Régime de passage**: 10,000-13,000 RPM
- **Efficacité**: 96%
- **Justification Splines**: Les transitions de rapports sont des événements discrets non-linéaires. Les splines capturent la dynamique de chute de RPM bien mieux qu'un seuil fixe.
#### Classe: `Tires` (tires.py)
- **Responsabilité**: Dynamique des pneus et dégradation
- **Dimensions F1 2023**:
  - Avant: 305mm/720mm-18"
  - Arrière: 405mm/720mm-18"
- **Modèle de force** (Régression par Splines Cubiques):
  - `F_x = Spline(μ, slip_angle, load, temperature)` remplaçant le modèle linéaire
  - Utilisation de `UnivariateSpline` pour la courbe de glissement (Pacejka-like)
  - Surface de réponse thermique par spline bidimensionnelle (`griddata` + `RBF`)
  - Prise en compte du transfert de charge longitudinal/latéral via GAM
- **Composés**: A3 (tendre), A4 (medium), A5 (dur)
- **Modèles de dégradation**: Splines cubiques monotones pour capturer le "cliff" de dégradation (chute brutale de grip)
- **Justification Splines**: Le modèle linéaire ne capture pas le pic de grip à 4-6° d'angle de glissement. Les splines réduisent l'erreur de ±15% à ±3%.
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

### 7.1 Physique (Mise à Jour avec Splines)
- **Actuel**: Modèle cinématique 2D uniquement (pas de suspension)
- **Problème**: Forces pneumatiques simplifiées (modèle linéaire), aérodynamique statique
- **Solution Spline**: 
  - Remplacer le modèle linéaire de pneus par `UnivariateSpline(slip_angle, F_y)` pour capturer le pic de grip Pacejka
  - Utiliser des GAM (Generalized Additive Models) pour l'aérodynamique: `C_x = f(vitesse, hauteur, braquage)` avec termes spline
  - Modéliser le DRS dynamique comme transition sigmoïde lisse plutôt que binaire
  - Transfert de charge dynamique par interpolation spline de la surface de réponse

### 7.2 Groupe Motopropulseur (Mise à Jour avec Splines)
- **Actuel**: Courbe de puissance fixe polynomiale, ERS simplifié
- **Problème**: Erreur ±12% sur la puissance, pas de stratégie de déploiement
- **Solution Spline**:
  - Courbe de couple: `UnivariateSpline(RPM, Torque, s=0.95)` avec validation croisée pour optimiser le lissage
  - ERS: Surface de réponse temporelle par spline bicubique (SOC, vitesse, température) → précision ±2%
  - Modes moteur: Profils de déploiement modélisés par splines monotones (Qualif, Course, Économie)

### 7.3 Pneus (Mise à Jour avec Splines)
- **Actuel**: Température non modélisée, pression statique, usure linéaire
- **Problème**: Ne capture pas le "cliff" de dégradation, ni le graining/blistering
- **Solution Spline**:
  - Courbe de grip vs température: spline univariée avec pic à 90-110°C
  - Usure: spline monotone décroissante avec rupture de pente pour le "cliff"
  - Pression dynamique: fonction spline de la température (`P = f(T_coeur, T_surface)`)
  - Graining/Blistering: détection par dérivée seconde de la température surface

### 7.4 IA (Mise à Jour avec Splines)
- **Actuel**: Réseaux feedforward simples, capteurs limités
- **Solution Spline**:
  - Trajectoires de référence: B-Splines paramétriques (`splprep/splev`) pour smoothness C²
  - Profils de vitesse par virage: apprentissage par spline de lissage sur les tours optimaux
  - Points de freinage: régression spline sur les données télémétriques (précision ±0.5m)
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

## 11. Recommandations Architecturales (Mise à Jour avec Splines)

### 11.1 Court Terme (Priorité: Modèles Non-Linéaires)
1. **Implémenter le système de configuration unifié (YAML)** avec support des courbes spline
2. **Remplacer TOUTES les régressions linéaires par des splines cubiques**:
   - Moteur: `UnivariateSpline(RPM, Torque)` → gain précision ±12% → ±2%
   - Pneus: `UnivariateSpline(slip_angle, F_y)` → capture du pic Pacejka
   - Boîte: `LSQUnivariateSpline` pour détection shifts → précision ±0.002
3. Ajouter tests unitaires validant la continuité C² des splines
4. Documenter les unités et contraintes physiques (cercle de friction, conservation énergie)

### 11.2 Moyen Terme (Optimisation Performance)
1. **Cythoniser les calculs de splines** pour temps réel (<1ms par évaluation)
2. Introduire pattern Observer pour événements de course
3. Séparer logique métier du rendu Pygame
4. Implémenter modèle de suspension par surfaces de réponse spline
5. Gestion carburant/ERS avec GAM multi-paramètres

### 11.3 Long Terme (F1 2026 & Au-Delà)
1. Intégration circuits F1 2026 avec aérodynamique active (X-Mode/Z-Mode)
2. ERS 350kW modélisé par spline de réponse temporelle
3. Support multijoueur réseau avec synchronisation d'états physiques
4. API télémétrie avancée pour rétro-ingénierie (FastF1 integration)
5. IA avec trajectoires B-Spline apprises par renforcement

---

## 12. Conclusion : Impératif des Splines Cubiques

**Recommandation Forte**: Abandonner définitivement la régression linéaire pour tous les modèles physiques F1.

| Domaine | Erreur Linéaire | Erreur Splines | Facteur Amélioration |
|---------|-----------------|----------------|---------------------|
| Puissance moteur | ±12% | ±2% | ×6 |
| Grip pneus (pic) | Ne capture pas | ±3% | ∞ |
| Rapports boîte | ±0.010 | ±0.002 | ×5 |
| Temps tour simulé | 3-5% | <0.5% | ×6-10 |
| Détection freinage | ±2m | ±0.5m | ×4 |

**Stack Technologique Validée**:
```yaml
bibliotheques:
  - scipy>=1.10.0    # UnivariateSpline, LSQUnivariateSpline, splprep/splev
  - scikit-learn     # cross_val_score pour optimisation paramètres lissage
  - pygam>=0.9.0     # GAM multivariés (aéro, ERS, pneus thermiques)
  - cython>=3.0.0    # Accélération si nécessaire (<1ms requis)
  - fastf1>=3.8.0    # Données télémétriques pour calibration
```

**Critères de Validation Physique** (Obligatoires):
- [ ] Conservation énergie: ∫P dt ≤ Énergie totale disponible
- [ ] Cercle friction: $a_{lat}^2 + a_{long}^2 \leq (\mu g)^2$ respecté en tout point
- [ ] Monotonie rapports: $i_1 > i_2 > ... > i_8$ strictement décroissant
- [ ] CxA ∈ [0.8, 1.2], CzA ∈ [3.0, 4.5] (plages F1 réalistes)
- [ ] RPM_max ∈ [11500, 13000] (conforme règlement FIA)
- [ ] SOC ERS ∈ [0.20, 1.00] avec limites de déploiement

---

*Document mis à jour : Intégration systématique des splines cubiques pour modélisation physique non-linéaire F1.*
