 # 📘 Game Design Document (GDD) — Square Escape (Simple Edition)

> **Ver. 2.0** | *Geometric Platformer Dash Combat*

---

## 1. Executive Summary & Concept Overview

* **Game Title:** Square Escape: Dash & Edges Edition
* **Genre:** 2D Fast-Paced Platformer Dash Combat
* **Perspective & Controls:** 2D Side-scroller (Keyboard + Mouse Precision Aiming)
* **Technology:** Python 3 (Pygame / Pygame-CE) — Clean Object-Oriented Architecture (OOP)

### 💡 High Concept
In a world ruled by geometric shapes, you are **Square** (a Neon Square), the only sharp-angled shape trapped in the territory of the **Circle Gang** (a greedy syndicate of smooth, angle-less circles). The circles despise sharp corners and strive to grind every shape down into smooth, uniform spheres.

Your objective is to escape through perilous levels by leveraging agile movement, a **360° Dash Attack** that slices enemies in half, and rescuing **Allies with Edges** like **Spike the Triangle** to reclaim your freedom!

---

## 2. Core Gameplay Loop

```
[Start Level] ➔ [Run & Wall Jump] ➔ [Dash Attack Circles / Break Walls]
       ▲                                         │
       │                                         ▼
[Upgrade & Ammo Pickups] ◄── [Rescue Triangle Ally from Cages]
       │
       ▼
[Reach Exit Portal] ➔ [Level Clear / Bottom Progress 100%]
```

1. **Navigation & Platforming:** Traverse platformer terrain with precision jumps, aerial momentum, and *Wall Cling / Wall Jump*.
2. **Dash Combat:** Strike down the *Circle Gang* by dashing through them with a high-speed *Dash Attack* aimed via the mouse cursor.
3. **Ally Rescue:** Free *Triangle Allies* from locked cages to gain automated support fire.
4. **Real-Time Progress:** Monitor the distance bar at the bottom of the screen to track how close Square is to the exit portal.

---

## 3. Player Mechanics (Main Character — Square)

| Feature | Mechanical Description |
|---|---|
| **Basic Movement & Inertia** | Responsive horizontal movement with aerial momentum when jumping. |
| **Omni-Directional Dash** | Rapid burst toward the mouse cursor (360°). Serves as both the primary attack & mobility tool. |
| **Dash Invulnerability (i-Frames)** | Square cannot take enemy damage for the duration of an active dash. |
| **Dash Refill Rules** | • Cooldown automatically resets upon touching the ground.<br>• Instant Refill (+1 Dash) upon eliminating an enemy or collecting a *Dash Crystal*. |
| **Wall Cling & Charge Jump** | Hold `Space` while against a wall to cling and charge up.<br>An arrow indicator displays the launch trajectory directed toward the mouse cursor. |

---

## 4. Allies with Edges System

### 🔺 Triangle Ally ("Spike the Triangle")
* **Rescue Cage System:** Trapped inside steel cages placed throughout the level. Cages must be shattered by Square using a *Dash Attack*.
* **Companion Behavior:** Once liberated, Spike hovers above Square's shoulder (*smooth lerp movement*).
* **Auto-Targeting Needle Darts:** Automatically acquires targets and fires sharp triangular darts at the nearest *Circle Gang* enemies.
* **Ammo System:** Features a limited ammunition pool. Ammo can be replenished by collecting *Dart Ammo Pickups*.

---

## 5. Enemy & Hazard Design

### ⚪ Circle Gang (Primary Enemies)
* **Patrol Circles:** Red circles patrolling platforms. Deal damage upon direct contact with Square.
* **Slice-in-Half Death Visual:** When struck by a *Dash Attack* or triangular dart, circles are sliced in two, releasing half-circle particle fragments that fall and fade away.

### 🧱 Hazards & Interactive Objects
* **Spikes:** Static hazards that reduce player HP on contact.
* **Sawblades:** Dynamic rotating hazards that travel along designated tracks (vertical/horizontal).
* **Breakable Walls:** Wooden/stone barricades blocking the path. Can only be destroyed using a *Dash Attack*.
* **Dash Crystals:** Floating crystals that reset the dash in mid-air and provide a slight upward boost.

---

## 6. HUD & Progress System

### 📊 Bottom Escape Progress Bar
* Permanently fixed at the very bottom of the screen.
* Displays the percentage of distance traveled toward the exit portal:
  $$\text{Progress Ratio} = \frac{\text{Player } X}{\text{Portal } X}$$
* Visualized as a track line with a mini **Square** icon moving from left to right toward the **Green Portal**.

### 🛡️ Additional HUD Overlay
* **Health Bar (HP):** Displays Square's remaining durability (3 HP max).
* **Dash Cooldown Meter:** Visual indicator of *dash attack* availability.
* **Ally Ammo Counter:** Shows remaining triangular dart ammunition.

---

## 7. Technical OOP Architecture

| Python Class | Primary Responsibility |
|---|---|
| `Game` | Main loop, state management (`TITLE`, `PLAYING`, `WIN`, `GAME_OVER`), scrolling camera rendering, and collision orchestration. |
| `Player` | Square physics, keyboard/mouse input, state machine (*Dash*, *Wall Cling*), and hitpoints. |
| `CircleEnemy` | Circle patrol AI, movement, and visual slice-in-half death logic. |
| `TriangleAlly` & `RescueCage` | Cage behavior, rescue mechanics, hovering over the player's shoulder, and dart projectile firing system. |
| `Platform`, `BreakableWall`, `Sawblade` | Static platform logic, breakable barricades, and moving sawblades. |
| `DashCrystal` | Mid-air dash refill crystal respawner. |
| `HUD` | Renders HP bar, ally ammo, and the **Bottom Escape Progress Bar**. |

---

## 8. Visual & Audio Style

* **Visual Style:** Minimalist Neon Geometry (Square = Cyan, Circle Gang = Red, Triangle Ally = Yellow, Exit Portal = Green).
* **VFX:** Line trails during dashes, particle explosions when enemies are sliced in half, wall jump aim indicator arrow pointing toward the mouse cursor.
* **Audio Direction:** 8-bit synthetic sound effects (Dash swoosh, Circle slice, Dart shoot, Wall cling charge, Portal reach victory fanfare).
