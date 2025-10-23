# F1 Race Prediction - Feature Engineering Research & Improvements

## Current Model Analysis

### Strengths:
- ✅ Grid position is highly predictive (35.6% importance)
- ✅ Championship position captures momentum (13.2%)
- ✅ Recent form works well (7.4%)
- ✅ Good at predicting points finishes (92.5%)

### Weaknesses:
- ❌ **Cannot predict DNFs**: Model predicts P3 for drivers who DNF from P2 (16+ position error)
- ❌ **Winner prediction**: 0% accuracy (too rare event, imbalanced)
- ❌ **Underutilizes team strength**: Team Elo only 3.9% importance
- ❌ **Missing race dynamics**: Doesn't consider overtaking difficulty, tire strategy, etc.

---

## Research: Advanced Feature Engineering

### 1. **Competitive Context Features**

#### A. Relative Grid Position to Competitors
**Concept**: Your starting position relative to faster/slower drivers matters

**New Features**:
```python
# Drivers ahead with better Elo (threats from behind)
drivers_ahead_better_elo = count(grid_pos < mine & elo > mine)

# Drivers behind with better Elo (likely to overtake)
drivers_behind_better_elo = count(grid_pos > mine & elo > mine)

# Average Elo of drivers starting ahead
avg_elo_ahead = mean(elo[grid_pos < mine])

# Average Elo of drivers starting behind
avg_elo_behind = mean(elo[grid_pos > mine])

# Gap to leader's Elo
elo_gap_to_p1 = leader_elo - my_elo

# Gap to teammate's Elo
elo_gap_to_teammate = teammate_elo - my_elo
```

**Why it helps**: 
- Starting P10 with slow cars ahead is easier than P10 with fast cars ahead
- Predicts overtaking likelihood


#### B. Team Strength in Race Context
**Current issue**: Team Elo exists but not used effectively

**New Features**:
```python
# Team rank in this race (by average grid position)
team_grid_rank = rank(mean(grid_pos) per team)

# Best teammate grid position
best_teammate_grid = min(grid_pos) of teammates

# Team consistency (grid position variance)
team_grid_variance = var(grid_pos) of teammates

# Team's historical performance at this circuit
team_circuit_win_rate = wins / races at circuit
team_circuit_avg_finish = mean(position) at circuit
```

**Why it helps**:
- Mercedes starting P1+P3 is stronger than P1+P15
- Team strategy depends on both drivers' positions


### 2. **DNF Prediction Features**

#### Current Problem: 
Model cannot predict crashes/mechanical failures (12.6% of large errors)

#### Solution: Separate DNF Classifier

**Approach**:
1. **Binary DNF predictor** (yes/no) trained separately
2. **DNF probability** as feature in position model
3. **DNF type prediction** (mechanical vs driver error)

**DNF Risk Features**:
```python
# Driver reliability
driver_dnf_rate_season = dnfs / races this season
driver_dnf_rate_career = dnfs / total races
driver_dnf_rate_circuit = dnfs / races at this circuit

# Team reliability
team_dnf_rate_season = dnfs / (races * 2) this season
team_mechanical_dnf_rate = mechanical_dnfs / races

# Race context
is_street_circuit = 1 if Monaco/Singapore/Baku else 0
is_high_speed_circuit = 1 if Monza/Spa else 0
is_wet_race = 1 if rain predicted else 0

# Starting position risk
grid_position_dnf_risk = historical_dnf_rate[grid_pos]
# (front-runners crash less, mid-pack has more incidents)
```

**Implementation**:
```python
# Two-stage model
dnf_prob = dnf_classifier.predict_proba(X)[:, 1]
X['dnf_probability'] = dnf_prob

# Position model adjusts based on DNF risk
position_pred = position_model.predict(X)
# High DNF prob → predict lower finish
```


### 3. **Overtaking Difficulty Features**

#### Concept: Some circuits make overtaking hard (Monaco) vs easy (Bahrain)

**Circuit Characteristics**:
```python
# Historical overtaking rate at circuit
avg_position_changes = mean(|grid_pos - finish_pos|) at circuit

# DRS zones effectiveness
drs_overtakes_per_race = historical count at circuit

# Circuit type
is_street_circuit = 1/0
is_high_downforce = 1/0  # Monaco, Hungary
is_power_circuit = 1/0   # Monza, Spa

# Weather impact
expected_weather_impact = 0-1 (rain probability)
```

**Why it helps**:
- Monaco: Grid position is destiny (low overtaking)
- Bahrain: Many position changes (high overtaking)
- Model should weight grid_pos more heavily at Monaco


### 4. **Tire Strategy & Pit Stop Features**

**Problem**: Model doesn't know about race strategy

**New Features**:
```python
# Tire choice for qualifying (soft/medium/hard)
quali_tire_compound = 0/1/2

# Expected pit stop strategy (1-stop vs 2-stop circuit)
circuit_avg_pit_stops = mean(pit_stops) at circuit

# Tire degradation rate at circuit
circuit_tire_deg_high = 1 if high-deg circuit else 0

# Team pit stop performance
team_avg_pit_time = mean(pit_stop_duration) this season
team_pit_reliability = 1 - (failed_stops / total_stops)
```

**Why it helps**:
- Wrong tire choice → worse race pace
- Slow pit stops → lose positions


### 5. **Race Pace vs Qualifying Pace**

**Concept**: Some drivers/teams are better at qualifying than racing

**New Features**:
```python
# Driver's qualifying vs race Elo difference
driver_pace_diff = driver_quali_elo - driver_race_elo
# Positive = better qualifier than racer (Leclerc, Russell)
# Negative = better racer than qualifier (Alonso, Pérez)

# Team's qualifying vs race Elo difference  
team_pace_diff = team_quali_elo - team_race_elo

# Recent qualifying vs race delta
recent_quali_race_delta = mean(quali_pos - race_pos) last 5 races
# Positive = usually gains positions in race
# Negative = usually loses positions in race

# Circuit-specific pace differential
circuit_quali_race_correlation = corr(quali_pos, race_pos) at circuit
```

**Why it helps**:
- Leclerc often qualifies P1 but finishes P3-P5
- Alonso often qualifies P8 but finishes P5-P6


### 6. **Championship Battle Features**

**Current**: Championship position included (13.2% importance) ✅

**Enhancements**:
```python
# Points gap to leader
points_gap_to_leader = leader_points - my_points

# Points gap to next position
points_gap_to_next = my_points - (position_below_points)

# Must-win pressure (fighting for championship)
championship_pressure = 1 if within 50 points of leader else 0

# Team orders likelihood
teammate_ahead_in_championship = 1/0
points_gap_to_teammate = my_points - teammate_points
```


### 7. **Historical Head-to-Head**

**New Features**:
```python
# Career head-to-head vs each opponent
h2h_win_rate = wins / (wins + losses) vs specific driver

# Recent head-to-head (last 5 encounters)
recent_h2h_record = recent wins vs specific driver

# Team head-to-head vs each opponent team
team_h2h_win_rate = wins / races vs specific team
```


### 8. **Weather & Track Conditions**

**Problem**: Model doesn't know about weather

**New Features**:
```python
# Weather forecast (if available)
rain_probability = 0-1
temperature_high = 1 if > 30°C else 0

# Driver wet weather skill
driver_wet_weather_rating = wet_race_performance / dry_race_performance

# Team wet weather performance
team_wet_weather_rating = similar calculation
```


---

## Proposed Implementation Strategy

### Phase 1: Quick Wins (Immediate Impact)
1. ✅ **Relative competitor features** (drivers ahead/behind with better Elo)
2. ✅ **Team context features** (team grid rank, best teammate position)
3. ✅ **Overtaking difficulty** (circuit characteristics)
4. ✅ **Pace differential** (quali vs race Elo difference)

**Expected improvement**: +0.3-0.5 MAE reduction

### Phase 2: DNF Prediction (Major Impact)
5. ✅ **Separate DNF classifier** (predict crash/mechanical probability)
6. ✅ **DNF risk features** (reliability rates, circuit danger)
7. ✅ **Integrate DNF probability** into position model

**Expected improvement**: -5% large errors (>5 positions)

### Phase 3: Advanced Features (Diminishing Returns)
8. ⚠️ Tire strategy (requires pit stop data)
9. ⚠️ Weather data (external API needed)
10. ⚠️ Historical head-to-head (complex joins)

---

## Feature Importance Predictions

### Current Top 5:
1. Grid position (35.6%)
2. Championship position (13.2%)
3. Recent form (7.4%)
4. Season year (4.1%)
5. Team quali Elo (3.9%)

### After Improvements (Predicted):
1. **Grid position** (30%) - still #1 but less dominant
2. **Drivers ahead with better Elo** (12%) - NEW, high impact
3. **Championship position** (10%) - remains important
4. **DNF probability** (8%) - NEW, explains outliers
5. **Team grid rank** (7%) - NEW, team context
6. **Overtaking difficulty** (6%) - NEW, circuit-specific
7. **Recent form** (5%)
8. **Pace differential** (4%) - NEW, quali vs race
9. **Drivers behind with better Elo** (3%) - NEW
10. **Team quali Elo** (3%)

---

## Expected Performance After Improvements

### Current Performance (Test Set 2024):
- MAE: 2.534 positions
- Within ±2: 51.98%
- Winner: 0%
- Podium: 40.11%
- Points: 92.51%

### Target Performance:
- **MAE: 2.0-2.2 positions** (-15% error)
- **Within ±2: 60-65%** (+10-15%)
- **Winner: 15-25%** (vs 5% random)
- **Podium: 50-55%** (+10%)
- **Points: 94-96%** (+2%)

---

## Next Steps

### Option 1: Implement Phase 1 (Quick Wins)
- Add 8-10 new features
- Retrain XGBoost
- Evaluate improvement
- **Time**: 30-60 minutes

### Option 2: Full Feature Engineering
- Implement all Phase 1 + Phase 2 features
- Create DNF classifier
- Ensemble model
- **Time**: 2-3 hours

### Option 3: Research Other Models
- Try LightGBM (might be faster)
- Try Neural Network with embeddings
- Try ensemble (XGBoost + LightGBM + NN)

## Recommendation

**Start with Phase 1 (Quick Wins)** - Most impact for least effort
- Focus on competitive context features
- Easy to implement with existing data
- Should reduce MAE by 0.3-0.5 positions

Ready to implement?
