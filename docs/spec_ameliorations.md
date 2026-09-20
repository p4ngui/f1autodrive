# Spécification Détaillée des Améliorations - RaceSim F1

## 1. Introduction

### 1.1 Objectif du Document
Ce document spécifie les améliorations à apporter au simulateur RaceSim pour:
1. Corriger les limitations identifiées dans l'architecture actuelle
2. Améliorer la fidélité de simulation physique
3. Optimiser les performances et la maintenabilité du code
4. Préparer la base pour la mise à jour F1 2026

### 1.2 Périmètre
- Modules concernés: `car.py`, `engine.py`, `gearbox.py`, `tires.py`, `game.py`
- Nouveaux modules: configuration, physique avancée, gestion de course
- Exclusions: Rendu graphique 3D, réseau multijoueur

---

## 2. Améliorations Prioritaires (P0)

### 2.1 Système de Configuration Unifié

#### 2.1.1 Problème Actuel
- Configurations éparpillées (INI, JSON inline, constantes hardcodées)
- Incohérences entre fichiers (`MER.ini` vs `car.py`)
- Difficile maintenance et ajout de nouvelles voitures

#### 2.1.2 Solution Proposée

**Nouveau module**: `config_manager.py`

```python
# racesim/src/config/config_manager.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml
import json

@dataclass
class EngineConfig:
    """Configuration du groupe motopropulseur"""
    topology: str  # "RWD", "AWD", "FWD"
    power_ice_max: float  # [W] Puissance max moteur thermique
    power_ers_max: float  # [W] Puissance max MGU-K
    rpm_min: float  # [1/min] Régime minimum
    rpm_max: float  # [1/min] Régime maximum
    rpm_redline: float  # [1/min] Limite rouge
    torque_curve: List[float]  # Courbe de couple [Nm] par palier RPM
    fuel_flow_max: float  # [kg/h] Débit carburant max (F1: 100 kg/h)
    ers_deployment_rate: float  # [W/s] Taux de déploiement ERS
    ers_recovery_rate: float  # [W/s] Taux de récupération ERS
    ers_capacity_mj: float  # [MJ] Capacité de batterie (F1: 4 MJ/lap)
    
@dataclass
class GearboxConfig:
    """Configuration de la boîte de vitesses"""
    gears_count: int  # Nombre de rapports (F1: 8)
    ratios: List[float]  # Rapports de transmission
    shift_time: float  # [s] Temps de passage de rapport
    efficiency: float  # [-] Efficacité mécanique
    shift_rpm: List[float]  # [1/min] Régime de passage par rapport
    
@dataclass
class TireConfig:
    """Configuration des pneus"""
    compound_name: str  # Nom du composé (C1-C5, A3-A5)
    circ_ref: float  # [m] Circonférence de référence
    fz_0: float  # [N] Charge nominale
    mu_x: float  # [-] Coefficient de friction longitudinal
    mu_y: float  # [-] Coefficient de friction latéral
    dmux_dfz: float  # [-] Variation μ avec charge
    degradation_model: str  # "lin", "quad", "cub", "ln"
    degradation_coeffs: Dict[str, float]  # k_0, k_1, etc.
    optimal_temp: float  # [°C] Température optimale
    pressure_nominal: float  # [bar] Pression nominale
    
@dataclass
class CarConfig:
    """Configuration complète d'une voiture"""
    team_name: str
    driver_name: str
    car_number: int
    mass_empty: float  # [kg] Masse à vide (min F1: 798kg incluant pilote)
    mass_fuel_start: float  # [kg] Carburant initial
    cog_height: float  # [m] Hauteur centre de gravité
    wheelbase: float  # [m] Empattement
    track_front: float  # [m] Voie avant
    track_rear: float  # [m] Voie arrière
    length: float  # [m] Longueur totale
    width: float  # [m] Largeur
    aero_drag: float  # [-] Cx * A (traînée)
    aero_downforce_front: float  # [m²] Cz * A avant
    aero_downforce_rear: float  # [m²] Cz * A arrière
    drs_reduction: float  # [-] Réduction traînée DRS (~17%)
    engine: EngineConfig
    gearbox: GearboxConfig
    tires: Dict[str, TireConfig]  # Par composé
    
class ConfigManager:
    """Gestionnaire central de configuration"""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.cars: Dict[str, CarConfig] = {}
        self.tracks: Dict[str, dict] = {}
        self.global_settings: dict = {}
        
    def load_all(self) -> None:
        """Charge toutes les configurations"""
        # Implémentation YAML/JSON
        pass
        
    def get_car_config(self, team: str, driver: str) -> CarConfig:
        """Récupère configuration voiture/pilote"""
        pass
        
    def validate_config(self, config: CarConfig) -> bool:
        """Valide la conformité réglementaire"""
        pass
```

**Format de fichier**: `config/cars/mercedes_2024.yaml`

```yaml
team_name: Mercedes-AMG Petronas
driver_name: Lewis Hamilton
car_number: 44
mass_empty: 798.0  # kg (minimum FIA 2024)
mass_fuel_start: 110.0  # kg (max 110kg en course)
cog_height: 0.205  # m
wheelbase: 3.685  # m (estimé)
track_front: 1.600  # m
track_rear: 1.600  # m
length: 5.500  # m
width: 2.000  # m
aero_drag: 1.56  # m²
aero_downforce_front: 2.20  # m²
aero_downforce_rear: 2.68  # m²
drs_reduction: 0.17

engine:
  topology: RWD
  power_ice_max: 740000  # W (~1000 HP)
  power_ers_max: 120000  # W (~161 HP)
  rpm_min: 1000
  rpm_max: 11400
  rpm_redline: 12200
  fuel_flow_max: 100.0  # kg/h (limite FIA)
  ers_deployment_rate: 120000  # W
  ers_recovery_rate: 200000  # W (freinage)
  ers_capacity_mj: 4.0  # MJ par tour (limite FIA)
  
gearbox:
  gears_count: 8
  ratios: [0.040, 0.070, 0.095, 0.117, 0.143, 0.172, 0.190, 0.206]
  shift_time: 0.050  # s (50ms typique F1)
  efficiency: 0.96
  shift_rpm: [10000, 11800, 11800, 11800, 11800, 11800, 11800, 13000]
  
tires:
  C3:  # Soft
    compound_name: C3
    circ_ref: 2.073
    fz_0: 3000.0
    mu_x: 1.65
    mu_y: 1.85
    dmux_dfz: -0.00005
    degradation_model: lin
    degradation_coeffs:
      k_0: 0.615
      k_1_lin: 0.107
    optimal_temp: 99.85
    pressure_nominal: 1.4
    
  C4:  # Medium
    compound_name: C4
    circ_ref: 2.073
    fz_0: 3000.0
    mu_x: 1.55
    mu_y: 1.75
    dmux_dfz: -0.00005
    degradation_model: lin
    degradation_coeffs:
      k_0: 0.175
      k_1_lin: 0.251
    optimal_temp: 105.0
    pressure_nominal: 1.4
    
  C5:  # Hard
    compound_name: C5
    circ_ref: 2.073
    fz_0: 3000.0
    mu_x: 1.45
    mu_y: 1.65
    dmux_dfz: -0.00005
    degradation_model: lin
    degradation_coeffs:
      k_0: 0.0
      k_1_lin: 0.055
    optimal_temp: 110.0
    pressure_nominal: 1.4
```

#### 2.1.3 Critères d'Acceptation
- [ ] Toutes les configurations chargées depuis fichiers externes
- [ ] Validation automatique des limites réglementaires F1
- [ ] Support de multiples saisons (2023, 2024, 2026+)
- [ ] Tests unitaires couvrant 100% du parsing YAML
- [ ] Documentation complète des paramètres

---

### 2.2 Correction des Dimensions Véhicule

#### 2.2.1 Problème Actuel
- Incohérences dans `car.py`: `total_length=5.4` vs commentaires 5.5m
- Positions des essieux non conformes F1
- Masse incorrecte (984kg vs 798kg minimum FIA)

#### 2.2.2 Spécifications F1 2024

```python
# Dimensions officielles F1 2024 (en mètres)
F1_2024_SPECS = {
    "length_max": 5.500,  # Maximum autorisé
    "width_max": 2.000,   # Hors rétroviseurs
    "height_max": 0.950,  # Hauteur totale
    "wheelbase_typical": 3.685,  # Estimé (non官方)
    "front_overhang": 1.161,  # Nez à essieu avant
    "rear_overhang": 0.749,   # Essieu arrière à diffuseur
    "mass_min": 798.0,  # Avec pilote, sans carburant
    "fuel_capacity": 110.0,  # kg maximum en course
    "weight_distribution_front": 0.46,  # ~46% avant
    "weight_distribution_rear": 0.54,   # ~54% arrière
}

# Positionnement correct dans Car.__init__()
class Car:
    def __init__(self, config: CarConfig):
        # Dimensions depuis config
        self.length = config.length  # 5.500 m
        self.width = config.width    # 2.000 m
        self.wheelbase = config.wheelbase  # 3.685 m
        
        # Positions relatives (depuis le centre de gravité)
        self.cog_x = 0.0  # Origine au CoG
        self.front_axle_x = config.wheelbase * config.weight_distribution_rear
        self.rear_axle_x = -config.wheelbase * config.weight_distribution_front
        
        # Masses
        self.mass_empty = config.mass_empty  # 798 kg
        self.mass_fuel = config.mass_fuel_start  # 110 kg max
        self.mass_total = self.mass_empty + self.mass_fuel
        
        # Inertie (estimation)
        self.inertia_yaw = self.mass_total * (self.wheelbase ** 2) * 0.15
```

#### 2.2.3 Critères d'Acceptation
- [ ] Dimensions conformes réglementation F1 2024
- [ ] Masse totale vérifiable dynamiquement
- [ ] Centre de gravité positionné correctement
- [ ] Tests de validation des dimensions

---

### 2.3 Refonte du Modèle Moteur

#### 2.3.1 Problème Actuel
- Courbe de puissance simplifiée (polynôme cubique fixe)
- Pas de gestion de consommation carburant
- ERS partiel (pas de limite MJ/tour)
- Pas de modes moteur

#### 2.3.2 Nouvelle Architecture Engine

```python
# racesim/src/powertrain/engine_v2.py
from enum import Enum
from typing import Tuple
import numpy as np

class EngineMode(Enum):
    """Modes de fonctionnement moteur"""
    QUALIFY = 0  # Puissance max, consommation libre
    RACE = 1     # Gestion carburant
    OVERTAKE = 2 # Boost ERS temporaire
    SAVE_FUEL = 3  # Économie carburant
    SAVE_ERS = 4   # Recharge batterie prioritaire

class EnergyStore:
    """Gestion de la batterie ERS"""
    
    def __init__(self, capacity_mj: float = 4.0):
        self.capacity_mj = capacity_mj  # Limite FIA: 4 MJ/tour
        self.current_energy_j = 0.0  # [J] Énergie actuelle
        self.max_deploy_power_w = 120000  # 120 kW max
        self.max_recover_power_w = 200000  # 200 kW max (freinage)
        
    def deploy(self, power_w: float, duration_s: float) -> float:
        """Déploie de l'énergie, retourne l'énergie fournie [J]"""
        energy_available = min(power_w * duration_s, self.current_energy_j)
        self.current_energy_j -= energy_available
        return energy_available
        
    def recover(self, power_w: float, duration_s: float) -> float:
        """Récupère de l'énergie au freinage"""
        energy_to_store = min(
            power_w * duration_s,
            self.max_recover_power_w * duration_s,
            self.capacity_mj * 1e6 - self.current_energy_j
        )
        self.current_energy_j += energy_to_store
        return energy_to_store
        
    def reset_for_lap(self):
        """Réinitialise pour un nouveau tour (règle FIA)"""
        # En F1, limite de 4MJ par tour, pas de stockage inter-tour
        self.current_energy_j = min(
            self.current_energy_j,
            self.capacity_mj * 1e6
        )

class EngineV2:
    """Moteur F1 hybride V2"""
    
    def __init__(self, config: EngineConfig):
        self.config = config
        self.mode = EngineMode.RACE
        self.energy_store = EnergyStore(config.ers_capacity_mj)
        self.rpm = 0.0
        self.throttle_position = 0.0  # 0-1
        self.fuel_consumed_kg = 0.0
        self.temp_internal = 200.0  # °C
        self.temp_water = 50.0  # °C
        self.health = 100.0  # %
        
        # Courbes de performance (données réelles)
        self._load_torque_curve()
        
    def _load_torque_curve(self):
        """Charge la courbe de couple depuis config"""
        # Données typiques F1 V6 Turbo
        self.rpm_points = np.array([8000, 9000, 10000, 11000, 11400, 12200])
        self.torque_points = np.array([380, 420, 480, 510, 500, 450])  # Nm
        
    def get_ice_torque(self, rpm: float) -> float:
        """Retourne le couple ICE disponible à un régime donné"""
        return float(np.interp(rpm, self.rpm_points, self.torque_points))
        
    def get_ice_power(self, rpm: float) -> float:
        """Puissance ICE [W] = Couple × Vitesse angulaire"""
        torque = self.get_ice_torque(rpm)
        omega = 2 * np.pi * rpm / 60  # rad/s
        return torque * omega
        
    def calc_fuel_consumption(self, torque: float, rpm: float, dt: float) -> float:
        """Calcule la consommation carburant [kg]"""
        # BSFC typique F1: ~250 g/kWh à meilleur point
        power_kw = (torque * 2 * np.pi * rpm / 60) / 1000
        bsfc_kg_per_kwh = 0.250  # Valeur optimisée
        fuel_kg = power_kw * bsfc_kg_per_kwh * (dt / 3600)
        return fuel_kg
        
    def get_total_torque(
        self,
        rpm: float,
        throttle: float,
        required_torque: float,
        dt: float
    ) -> Tuple[float, float, float]:
        """
        Calcule la distribution de couple ICE/ERS
        
        Returns:
            (torque_ice, torque_ers, fuel_consumed)
        """
        # Couple ICE disponible
        ice_torque_max = self.get_ice_torque(rpm)
        ice_torque = throttle * ice_torque_max
        
        # Couple ERS disponible
        ers_power_avail = min(
            self.config.power_ers_max,
            self.energy_store.current_energy_j / dt if dt > 0 else 0
        )
        omega = 2 * np.pi * rpm / 60
        ers_torque_max = ers_power_avail / omega if omega > 0 else 0
        
        # Stratégie selon mode
        if self.mode == EngineMode.OVERTAKE:
            # Deployment max ERS
            ers_torque = min(ers_torque_max, required_torque - ice_torque)
        elif self.mode == EngineMode.SAVE_FUEL:
            # Priorité ERS, réduction ICE
            ice_torque *= 0.8
            ers_torque = min(ers_torque_max, required_torque - ice_torque)
        elif self.mode == EngineMode.SAVE_ERS:
            # Recharge priorité, pas de deployment
            ers_torque = 0
        else:  # RACE normal
            # Distribution optimisée
            torque_deficit = required_torque - ice_torque
            ers_torque = min(ers_torque_max, max(0, torque_deficit))
            
        # Consommation carburant
        fuel_consumed = self.calc_fuel_consumption(ice_torque, rpm, dt)
        self.fuel_consumed_kg += fuel_consumed
        
        return ice_torque, ers_torque, fuel_consumed
        
    def update_temperatures(self, ambient_temp: float, dt: float):
        """Met à jour les températures moteur"""
        # Modèle thermique simplifié
        heat_gen = self.rpm * 0.01  # Production chaleur ~ RPM
        cooling = (self.temp_internal - ambient_temp) * 0.1
        self.temp_internal += (heat_gen - cooling) * dt
        
        # Water temp suit internal with delay
        self.temp_water += (self.temp_internal - self.temp_water) * 0.05 * dt
        
    def set_mode(self, mode: EngineMode):
        """Change le mode moteur (appelable par stratégie)"""
        self.mode = mode
```

#### 2.3.3 Critères d'Acceptation
- [ ] Limite de 4 MJ/tour respectée
- [ ] Débit carburant max 100 kg/h implémenté
- [ ] 5 modes moteur fonctionnels
- [ ] Températures influencent la performance
- [ ] Tests de consommation sur tour complet

---

### 2.4 Système de Pneus Avancé

#### 2.4.1 Problème Actuel
- Température des pneus absente
- Pression statique
- Pas de dégradation visuelle
- Modèle de force trop simple

#### 2.4.2 Nouvelle Classe Tire

```python
# racesim/src/tires/tire_v2.py
from enum import Enum
from dataclasses import dataclass
import numpy as np

class TireCompound(Enum):
    C1 = "Hardest"
    C2 = "Hard"
    C3 = "Medium-Hard"
    C4 = "Medium-Soft"
    C5 = "Softest"
    INTER = "Intermediate"
    WET = "Full Wet"

@dataclass
class TireState:
    """État instantané d'un pneu"""
    temperature_core: float  # [°C] Température coeur
    temperature_surface: float  # [°C] Température surface
    pressure: float  # [bar] Pression interne
    wear: float  # [%] Usure (0=neuf, 1=HS)
    grip_level: float  # [%] Niveau d'adhérence actuel
    blistering: float  # [%] Sévérité blistering
    graining: float  # [%] Sévérité graining
    flat_spot: bool  # Présence de méplat

class TireV2:
    """Pneu F1 avec modèle thermique et d'usure"""
    
    def __init__(self, compound: TireCompound, config: TireConfig):
        self.compound = compound
        self.config = config
        self.state = TireState(
            temperature_core=90.0,  # Temp départ (pré-chauffé)
            temperature_surface=90.0,
            pressure=config.pressure_nominal,
            wear=0.0,
            grip_level=1.0,
            blistering=0.0,
            graining=0.0,
            flat_spot=False
        )
        self.laps_completed = 0
        
        # Paramètres thermiques spécifiques au composé
        self.thermal_mass = self._get_thermal_mass()  # [J/°C]
        self.optimal_temp_range = (config.optimal_temp - 10, config.optimal_temp + 10)
        
    def _get_thermal_mass(self) -> float:
        """Masse thermique dépend du composé"""
        thermal_masses = {
            TireCompound.C1: 15000,
            TireCompound.C2: 14000,
            TireCompound.C3: 13000,
            TireCompound.C4: 12000,
            TireCompound.C5: 11000,
        }
        return thermal_masses.get(self.compound, 12000)
        
    def update_temperature(
        self,
        slip_angle: float,  # [rad] Angle de dérive
        slip_ratio: float,  # [-] Taux de glissement
        vertical_load: float,  # [N] Charge verticale
        velocity: float,  # [m/s] Vitesse
        ambient_temp: float,  # [°C] Temp ambiante
        track_temp: float,  # [°C] Temp piste
        dt: float  # [s] Pas de temps
    ):
        """Met à jour la température du pneu"""
        
        # Génération de chaleur par hystérésis
        # Q = f(slip, load, velocity)
        heat_slip = abs(slip_angle) * vertical_load * velocity * 0.001
        heat_longitudinal = abs(slip_ratio) * vertical_load * velocity * 0.001
        heat_total = heat_slip + heat_longitudinal
        
        # Refroidissement (convection + rayonnement)
        cooling_convection = (self.state.temperature_surface - ambient_temp) * 5.0
        cooling_radiation = 0.0001 * (self.state.temperature_surface**4 - ambient_temp**4)
        cooling_conduction = (self.state.temperature_surface - track_temp) * 2.0
        cooling_total = cooling_convection + cooling_radiation + cooling_conduction
        
        # Équilibre thermique
        net_heat = heat_total - cooling_total
        delta_temp = net_heat * dt / self.thermal_mass
        
        # Mise à jour températures
        self.state.temperature_surface += delta_temp
        # Le coeur suit avec inertie
        self.state.temperature_core += delta_temp * 0.3
        
        # Clamp aux limites physiques
        self.state.temperature_surface = np.clip(
            self.state.temperature_surface, ambient_temp, 200.0
        )
        self.state.temperature_core = np.clip(
            self.state.temperature_core, ambient_temp, 150.0
        )
        
    def update_pressure(self):
        """Met à jour la pression selon température (loi des gaz parfaits)"""
        # P/T = constante (volume constant)
        T_ref = 20 + 273.15  # Temp référence [K]
        T_current = self.state.temperature_core + 273.15
        self.state.pressure = self.config.pressure_nominal * (T_current / T_ref)
        
    def update_wear(
        self,
        vertical_load: float,
        slip_angle: float,
        slip_ratio: float,
        distance_m: float
    ):
        """Met à jour l'usure du pneu"""
        
        # Taux d'usure de base (dépend du composé)
        base_wear_rate = self._get_base_wear_rate()
        
        # Facteurs aggravants
        load_factor = vertical_load / self.config.fz_0
        slip_factor = 1.0 + abs(slip_angle) * 2.0 + abs(slip_ratio) * 3.0
        temp_factor = self._get_temperature_wear_factor()
        
        # Calcul usure
        wear_increment = (
            base_wear_rate * 
            load_factor * 
            slip_factor * 
            temp_factor * 
            (distance_m / 1000)  # Normalisé par km
        )
        
        self.state.wear = min(1.0, self.state.wear + wear_increment)
        
        # Grip réduit avec l'usure
        self.state.grip_level = max(0.5, 1.0 - self.state.wear * 0.5)
        
    def _get_base_wear_rate(self) -> float:
        """Taux d'usure de base par km"""
        rates = {
            TireCompound.C1: 0.002,  # Très durable
            TireCompound.C2: 0.003,
            TireCompound.C3: 0.004,
            TireCompound.C4: 0.006,
            TireCompound.C5: 0.008,  # Très tendre
        }
        return rates.get(self.compound, 0.004)
        
    def _get_temperature_wear_factor(self) -> float:
        """Facteur multiplicateur selon température"""
        temp = self.state.temperature_surface
        optimal = self.config.optimal_temp
        
        if temp < optimal - 20:
            return 1.5  # Graining accru si trop froid
        elif temp > optimal + 30:
            return 2.0  # Blistering accru si trop chaud
        else:
            return 1.0  # Zone optimale
            
    def check_degradations(self, slip_angle: float, velocity: float):
        """Détecte blistering, graining, flat spots"""
        
        # Blistering (surchauffe locale)
        if self.state.temperature_surface > self.config.optimal_temp + 40:
            self.state.blistering = min(1.0, self.state.blistering + 0.01)
            self.state.grip_level *= (1 - self.state.blistering * 0.3)
            
        # Graining (pneus froids + fort slip)
        if (self.state.temperature_surface < self.config.optimal_temp - 15 and
            abs(slip_angle) > 0.1):  # ~6 degrés
            self.state.graining = min(1.0, self.state.graining + 0.005)
            self.state.grip_level *= (1 - self.state.graining * 0.2)
            
        # Flat spot (blocage de roue)
        # À appeler lors de freinages bloqués
            
    def get_friction_coefficient(self) -> Tuple[float, float]:
        """
        Retourne les coefficients de friction actuels
        
        Returns:
            (mu_x, mu_y) coefficients longitudinal et latéral
        """
        # Facteur température (fenêtre optimale)
        temp = self.state.temperature_surface
        optimal = self.config.optimal_temp
        temp_factor = np.exp(-((temp - optimal) ** 2) / (2 * 15 ** 2))
        
        # Facteur usure
        wear_factor = 1.0 - self.state.wear * 0.4
        
        # Facteur dégradations
        deg_factor = (1 - self.state.blistering * 0.3) * (1 - self.state.graining * 0.2)
        
        # Calcul final
        mu_x = self.config.mu_x * temp_factor * wear_factor * deg_factor
        mu_y = self.config.mu_y * temp_factor * wear_factor * deg_factor
        
        return mu_x, mu_y
```

#### 2.4.3 Critères d'Acceptation
- [ ] Température évolue selon conditions de piste
- [ ] Pression varie avec température
- [ ] Usure visible après plusieurs tours
- [ ] Blistering/graining impactent performance
- [ ] Fenêtre de température optimale respectée

---

## 3. Améliorations Secondaires (P1)

### 3.1 Boîte de Vitesses Réaliste

```python
# racesim/src/powertrain/gearbox_v2.py
class GearboxV2:
    """Boîte de vitesses F1 semi-automatique"""
    
    def __init__(self, config: GearboxConfig):
        self.config = config
        self.current_gear = 1  # Neutral = 0
        self.clutch_engaged = False
        self.shift_request = None
        self.shift_timer = 0.0
        self.neutral = True
        
    def request_shift(self, upshift: bool):
        """Demande de passage de rapport"""
        if self.shift_timer > 0:
            return  # Shift déjà en cours
            
        target_gear = self.current_gear + (1 if upshift else -1)
        target_gear = max(1, min(self.config.gears_count, target_gear))
        
        if target_gear != self.current_gear:
            self.shift_request = target_gear
            self._execute_shift()
            
    def _execute_shift(self):
        """Exécute le passage de rapport (temps mort)"""
        # Phase 1: Coupure des gaz (5-10 ms)
        # Phase 2: Passage neutre (10-20 ms)
        # Phase 3: Engagement nouveau rapport (20-40 ms)
        # Total: 50-80 ms typique F1
        
        self.neutral = True
        self.shift_timer = self.config.shift_time
        
    def update(self, rpm: float, dt: float) -> float:
        """
        Met à jour l'état de la boîte
        
        Returns:
            ratio de transmission actuel
        """
        if self.shift_timer > 0:
            self.shift_timer -= dt
            
            if self.shift_timer <= 0:
                # Shift terminé
                self.current_gear = self.shift_request
                self.shift_request = None
                self.neutral = False
                
        if self.neutral:
            return 0.0
            
        return self.config.ratios[self.current_gear - 1]
        
    def get_engine_braking_torque(self, wheel_torque: float) -> float:
        """Retourne le couple de frein moteur"""
        # Frein moteur = pertes internes + compression
        base_engine_braking = 50.0  # Nm (typique)
        gear_ratio = self.config.ratios[self.current_gear - 1]
        return base_engine_braking * gear_ratio * self.config.efficiency
```

### 3.2 Capteurs Améliorés

```python
# racesim/src/sensors/sensor_array.py
class SensorArray:
    """Système de capteurs pour IA"""
    
    def __init__(self, car):
        self.car = car
        self.sensors = []
        self._setup_sensors()
        
    def _setup_sensors(self):
        """Configure les capteurs"""
        # 5 capteurs actuels (à garder)
        self.sensors.extend([
            RaycastSensor(angle=-90, distance=50),   # Gauche
            RaycastSensor(angle=-45, distance=75),   # Diag gauche
            RaycastSensor(angle=0, distance=120),    # Avant
            RaycastSensor(angle=45, distance=75),    # Diag droite
            RaycastSensor(angle=90, distance=50),    # Droite
        ])
        
        # NOUVEAUX capteurs proposés
        self.sensors.extend([
            # Vitesse relative aux bordures
            BorderProximitySensor(side="left"),
            BorderProximitySensor(side="right"),
            
            # Angle par rapport à la ligne idéale
            RacingLineAngleSensor(),
            
            # Distance au prochain virage
            NextCornerDistanceSensor(),
            
            # Adhérence disponible estimée
            AvailableGripSensor(),
            
            # Télemetry pour analyse
            TelemetryChannel("speed"),
            TelemetryChannel("throttle"),
            TelemetryChannel("brake"),
            TelemetryChannel("steer"),
            TelemetryChannel("gear"),
            TelemetryChannel("rpm"),
        ])
        
    def get_inputs(self) -> np.ndarray:
        """Retourne le vecteur d'entrée pour le réseau de neurones"""
        inputs = []
        for sensor in self.sensors:
            inputs.append(sensor.read())
        return np.array(inputs, dtype=np.float32)
```

### 3.3 Tests Unitaires

```python
# tests/test_engine_v2.py
import unittest
import numpy as np
from racesim.src.powertrain.engine_v2 import EngineV2, EngineMode

class TestEngineV2(unittest.TestCase):
    
    def setUp(self):
        self.engine = EngineV2(test_config)
        
    def test_ers_capacity_limit(self):
        """Test que la limite de 4MJ/tour est respectée"""
        # Déploiement max pendant 1 tour (~90s à 200km/h)
        lap_duration = 90.0
        deployed = self.engine.energy_store.deploy(120000, lap_duration)
        
        # Ne doit pas dépasser 4 MJ
        self.assertLessEqual(deployed, 4.0e6)
        
    def test_fuel_flow_limit(self):
        """Test la limite de 100 kg/h"""
        dt = 1.0  # 1 seconde
        max_fuel = self.engine.calc_fuel_consumption(500, 11000, dt)
        
        # 100 kg/h = 0.0278 kg/s
        self.assertLessEqual(max_fuel / dt, 100 / 3600)
        
    def test_engine_modes(self):
        """Test les différents modes moteur"""
        modes = [EngineMode.QUALIFY, EngineMode.RACE, EngineMode.OVERTAKE]
        
        for mode in modes:
            self.engine.set_mode(mode)
            torque_ice, torque_ers, fuel = self.engine.get_total_torque(
                11000, 1.0, 600, 0.016
            )
            
            # Vérifier que chaque mode produit un comportement différent
            self.assertIsNotNone(torque_ice)
            self.assertIsNotNone(torque_ers)
            
if __name__ == '__main__':
    unittest.main()
```

---

## 4. Planning de Mise en Oeuvre

### Phase 1: Fondation (Semaines 1-2)
- [ ] Créer structure de dossiers `config/`, `tests/`
- [ ] Implémenter `ConfigManager` avec support YAML
- [ ] Migrer toutes les configurations existantes
- [ ] Écrire tests unitaires de base

### Phase 2: Physique (Semaines 3-5)
- [ ] Refonte complète `EngineV2` avec ERS
- [ ] Implémenter `TireV2` avec thermique
- [ ] Mettre à jour `GearboxV2`
- [ ] Intégrer dans `CarV2`

### Phase 3: Validation (Semaines 6-7)
- [ ] Tests de performance sur circuits connus
- [ ] Calibration des paramètres avec données F1 réelles
- [ ] Correction des bugs identifiés
- [ ] Documentation complète

### Phase 4: Optimisation (Semaine 8)
- [ ] Profiling des performances
- [ ] Optimisation des calculs critiques
- [ ] Nettoyage du code legacy
- [ ] Préparation pour F1 2026

---

## 5. Métriques de Succès

| Métrique | Actuel | Cible | Mesure |
|----------|--------|-------|--------|
| Vitesse max | 252 km/h | 330+ km/h | Chrono sur Monza |
| Accélération 0-100 | ~2.5s | <2.6s | Benchmark |
| Consommation carburant | N/A | ~100 kg/h | Telemetry |
| Dégradation pneus | Linéaire simple | Thermique+Usure | Visual inspection |
| Couverture tests | <10% | >80% | pytest-cov |
| Temps de chargement config | N/A | <100ms | Benchmark |

---

*Document version: 1.0*
*Date: 2024*
*Statut: En attente de validation*
