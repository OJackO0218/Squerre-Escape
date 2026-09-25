"""
level_editor.py - Interactive In-Game Level Editor for Square Escape
Press [B] in-game to toggle Build Mode, or run this file directly!
"""
import pygame
import sys
import json
import math

class LevelEditor:
    TOOLS = [
        {"id": "PLATFORM", "name": "[1] Plat", "key": pygame.K_1, "color": (120, 120, 120)},
        {"id": "WOOD", "name": "[2] Wood", "key": pygame.K_2, "color": (150, 90, 45)},
        {"id": "METAL", "name": "[3] Metal", "key": pygame.K_3, "color": (100, 110, 125)},
        {"id": "ROPE", "name": "[4] Rope", "key": pygame.K_4, "color": (235, 235, 245)},
        {"id": "ENEMY", "name": "[5] Enemy", "key": pygame.K_5, "color": (220, 45, 45)},
        {"id": "TURRET", "name": "[6] Turret", "key": pygame.K_6, "color": (130, 130, 150)},
        {"id": "SPIKE", "name": "[7] Spike", "key": pygame.K_7, "color": (255, 60, 60)},
        {"id": "ALLY", "name": "[8] Ally", "key": pygame.K_8, "color": (255, 170, 30)},
        {"id": "GRAPPLE", "name": "[9] Grapple", "key": pygame.K_9, "color": (0, 200, 255)},
        {"id": "GOAL", "name": "[0] Goal", "key": pygame.K_0, "color": (50, 220, 80)},
        {"id": "SPAWN", "name": "[-] Spawn", "key": pygame.K_MINUS, "color": (0, 180, 255)},
    ]

    def __init__(self, game):
        self.game = game
        self.active = False
        self.cam_x = 0
        self.current_tool_idx = 0
        self.grid_size = 20
        self.grid_enabled = True

        # Mouse interaction state
        self.drag_start_world = None
        self.undo_stack = []
        self.message = "Press [B] to return to Game | [1-9, 0, -] Tools | [R-Click] Delete"
        self.message_timer = 0

        # UI Fonts
        self.font = pygame.font.SysFont("arial", 13, bold=True)
        self.font_small = pygame.font.SysFont("arial", 11)
        self.font_btn = pygame.font.SysFont("arial", 11, bold=True)

    def toggle(self):
        """Toggles between Build Mode and Playtest Mode."""
        self.active = not self.active
        if self.active:
            # Sync editor camera to current game camera
            self.cam_x = self.game.camera_x
            self.drag_start_world = None
            self.show_message("BUILD MODE ACTIVE - Edit freely!")
        else:
            # When exiting to play mode, ensure camera and entities are synced
            self.game.camera_x = max(0, self.cam_x)
            # Reset player to current spawn location and restore health
            self.game.player.rect.x = self.game.start_x
            self.game.player.rect.y = 352
            self.game.player.vx = 0
            self.game.player.vy = 0
            self.game.player.health = 100
            self.game.player.killed_by_boss = False
            self.game.player.has_grapple = False
            if hasattr(self.game.player, 'release_grapple'):
                self.game.player.release_grapple()
            self.game.state = 'PLAYING'
            self.game.bullets = []
            self.game.hanging_ropes = []
            for pickup in getattr(self.game, 'grapple_pickups', []):
                pickup.collected = False
            for e in self.game.enemies:
                e.is_dead = False
                e.health = 3
                e.x = e.start_x
                e.rect.centerx = int(e.x)
            for t in self.game.turrets:
                t.is_dead = False
                t.health = 3
            for m in getattr(self.game, 'metal_obstacles', []):
                m.is_broken = False
                m.is_dead = False
                m.health = 3
                m.particles = []
            for a in self.game.allies:
                a.x = a.start_x
                a.y = a.start_y
                a.rect.center = (int(a.x), int(a.y))
                a.cage_rect.center = (int(a.x), int(a.y))
                a.is_caged = True
                a.shooting_enabled = True
                a.target = None
                a.cage_particles = []

    def show_message(self, text, duration=150):
        self.message = text
        self.message_timer = duration

    def snap(self, val):
        """Snaps coordinate to grid if enabled."""
        if self.grid_enabled:
            return round(val / self.grid_size) * self.grid_size
        return int(val)

    def screen_to_world(self, sx, sy):
        return self.snap(sx + self.cam_x), self.snap(sy)

    def handle_event(self, event):
        """Processes editor keyboard and mouse input."""
        if event.type == pygame.KEYDOWN:
            # Tool switching with numbers 1-9, 0, minus
            for i, tool in enumerate(self.TOOLS):
                if event.key == tool["key"] or (tool["id"] == "SPAWN" and event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_EQUALS)):
                    self.current_tool_idx = i
                    self.show_message(f"Selected: {tool['name']}")
                    return

            # Toggle grid
            if event.key == pygame.K_g:
                self.grid_enabled = not self.grid_enabled
                self.show_message(f"Grid Snapping: {'ON (20px)' if self.grid_enabled else 'OFF'}")

            # Undo
            elif event.key == pygame.K_z:
                self.undo()

            # Export / Save Level
            elif event.key == pygame.K_s:
                self.export_level()

            # Toggle Fullscreen
            elif event.key == pygame.K_F11:
                self.game.toggle_fullscreen()

        # Mouse Clicks
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = getattr(event, 'pos', pygame.mouse.get_pos())
            # Ignore clicks on top UI bar
            if my < 45:
                # Check tool click
                self.handle_ui_click(mx, my)
                return

            wx, wy = self.screen_to_world(mx, my)

            # Left Click: Place or start dragging
            if event.button == 1:
                cur_tool = self.TOOLS[self.current_tool_idx]["id"]
                if cur_tool in ("PLATFORM", "WOOD", "METAL", "ROPE"):
                    self.drag_start_world = (wx, wy)
                elif cur_tool == "ENEMY":
                    self.place_enemy(wx, wy)
                elif cur_tool == "GOAL":
                    self.set_goal(wx, wy)
                elif cur_tool == "SPAWN":
                    self.set_spawn(wx, wy)
                elif cur_tool == "SPIKE":
                    self.place_spike(wx, wy)
                elif cur_tool == "ALLY":
                    self.place_ally(wx, wy)
                elif cur_tool == "TURRET":
                    self.place_turret(wx, wy)
                elif cur_tool == "GRAPPLE":
                    self.place_grapple(wx, wy)

            # Right Click: Delete element under cursor
            elif event.button == 3:
                self.delete_at(wx, wy)

        # Mouse Release (Finish drag placement)
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.drag_start_world:
                mx, my = getattr(event, 'pos', pygame.mouse.get_pos())
                wx, wy = self.screen_to_world(mx, my)
                sx, sy = self.drag_start_world
                self.drag_start_world = None

                cur_tool = self.TOOLS[self.current_tool_idx]["id"]
                rx = min(sx, wx)
                ry = min(sy, wy)
                rw = max(20, abs(wx - sx))
                rh = max(20, abs(wy - sy))

                # If it was a single click without drag, use sensible defaults
                if rw < 25 and rh < 25:
                    if cur_tool == "PLATFORM":
                        rw, rh = 120, 30
                    elif cur_tool == "WOOD":
                        rw, rh = 28, 70
                    elif cur_tool == "METAL":
                        rw, rh = 32, 70
                    elif cur_tool == "ROPE":
                        rw, rh = 80, 24

                if cur_tool == "PLATFORM":
                    self.place_platform(rx, ry, rw, rh)
                elif cur_tool == "WOOD":
                    self.place_wood(rx, ry, rw, rh)
                elif cur_tool == "METAL":
                    self.place_metal(rx, ry, rw, rh)
                elif cur_tool == "ROPE":
                    self.place_rope(rx, ry, rw, rh)

    def handle_ui_click(self, mx, my):
        """Allows clicking directly on tool buttons in the header."""
        btn_w = 68
        gap = 4
        start_x = 4
        for i in range(len(self.TOOLS)):
            bx = start_x + i * (btn_w + gap)
            if bx <= mx <= bx + btn_w and 6 <= my <= 34:
                self.current_tool_idx = i
                self.show_message(f"Selected: {self.TOOLS[i]['name']}")
                return

    def place_platform(self, x, y, w, h):
        import main
        plat = main.Platform(x, y, w, h)
        self.game.platforms.append(plat)
        self.undo_stack.append(('ADD_PLATFORM', plat))
        self.show_message(f"Added Platform at ({x}, {y}) [{w}x{h}]")

    def place_wood(self, x, y, w, h):
        import main
        wood = main.BreakableWood(x, y, w, h)
        self.game.breakable_woods.append(wood)
        self.undo_stack.append(('ADD_WOOD', wood))
        self.show_message(f"Added Breakable Wood at ({x}, {y})")

    def place_metal(self, x, y, w, h):
        import main
        metal = main.MetalObstacle(x, y, w, h)
        if not hasattr(self.game, 'metal_obstacles'):
            self.game.metal_obstacles = []
        self.game.metal_obstacles.append(metal)
        self.undo_stack.append(('ADD_METAL', metal))
        self.show_message(f"Added Metal Obstacle at ({x}, {y})")

    def place_rope(self, x, y, w, h):
        import main
        rope = main.RopeBlock(x, y, w, h)
        if not hasattr(self.game, 'rope_blocks'):
            self.game.rope_blocks = []
        self.game.rope_blocks.append(rope)
        self.undo_stack.append(('ADD_ROPE', rope))
        self.show_message(f"Added Rope Block at ({x}, {y}) [{w}x{h}]")

    def place_grapple(self, x, y):
        import main
        grapple = main.GrapplePickup(x, y)
        if not hasattr(self.game, 'grapple_pickups'):
            self.game.grapple_pickups = []
        self.game.grapple_pickups.append(grapple)
        self.undo_stack.append(('ADD_GRAPPLE', grapple))
        self.show_message(f"Added Grapple Pickup at ({x}, {y})")

    def place_enemy(self, x, y):
        import main
        enemy = main.CircleEnemy(x, y, patrol_range=60, speed=1.0)
        self.game.enemies.append(enemy)
        self.undo_stack.append(('ADD_ENEMY', enemy))
        self.show_message(f"Added Circle Enemy at ({x}, {y})")

    def place_spike(self, x, y):
        import main
        spike = main.Spike(x - 12, y - 24, 24, 24)
        self.game.spikes.append(spike)
        self.undo_stack.append(('ADD_SPIKE', spike))
        self.show_message(f"Added Spike at ({x}, {y})")

    def place_ally(self, x, y):
        import main
        ally = main.TriAnger(x, y)
        self.game.allies.append(ally)
        self.undo_stack.append(('ADD_ALLY', ally))
        self.show_message(f"Added Tri-Anger Ally at ({x}, {y}) [Caged - Dash to free, Q toggles shooting]")

    def place_turret(self, x, y):
        import main
        turret = main.EnemyTurret(x, y)
        self.game.turrets.append(turret)
        self.undo_stack.append(('ADD_TURRET', turret))
        self.show_message(f"Added Enemy Turret at ({x}, {y})")

    def set_goal(self, x, y):
        old_pos = (self.game.portal.rect.x, self.game.portal.rect.y)
        self.game.portal.rect.x = x
        self.game.portal.rect.y = y
        self.undo_stack.append(('SET_GOAL', old_pos))
        self.show_message(f"Goal Portal moved to ({x}, {y})")

    def set_spawn(self, x, y):
        old_spawn = (self.game.start_x, self.game.pole_rect.x, self.game.pole_rect.y)
        self.game.start_x = x
        self.game.pole_rect.x = x - 30
        self.game.pole_rect.y = y
        self.game.player.rect.x = x
        self.game.player.rect.y = y
        self.undo_stack.append(('SET_SPAWN', old_spawn))
        self.show_message(f"Spawn moved to ({x}, {y})")

    def delete_at(self, wx, wy):
        # 1. Delete Spikes
        for spike in list(self.game.spikes):
            if spike.rect.collidepoint(wx, wy):
                self.game.spikes.remove(spike)
                self.undo_stack.append(('DEL_SPIKE', spike))
                self.show_message("Deleted Spike")
                return

        # 2. Delete Grapple Pickups
        for gp in list(getattr(self.game, 'grapple_pickups', [])):
            if math.hypot(gp.x - wx, gp.y - wy) <= 18 or gp.rect.collidepoint(wx, wy):
                self.game.grapple_pickups.remove(gp)
                self.undo_stack.append(('DEL_GRAPPLE', gp))
                self.show_message("Deleted Grapple Pickup")
                return

        # 3. Delete Allies
        for ally in list(self.game.allies):
            if ally.cage_rect.collidepoint(wx, wy) or ally.rect.collidepoint(wx, wy) or math.hypot(ally.x - wx, ally.y - wy) <= 20:
                self.game.allies.remove(ally)
                self.undo_stack.append(('DEL_ALLY', ally))
                self.show_message("Deleted Tri-Anger Ally")
                return

        # 4. Delete Turrets
        for turret in list(self.game.turrets):
            if math.hypot(turret.x - wx, turret.y - wy) <= 20 or turret.rect.collidepoint(wx, wy):
                self.game.turrets.remove(turret)
                self.undo_stack.append(('DEL_TURRET', turret))
                self.show_message("Deleted Enemy Turret")
                return

        # 5. Delete Enemies
        for enemy in list(self.game.enemies):
            if enemy.rect.collidepoint(wx, wy):
                self.game.enemies.remove(enemy)
                self.undo_stack.append(('DEL_ENEMY', enemy))
                self.show_message("Deleted Enemy")
                return

        # 6. Delete Metal Obstacles
        for metal in list(getattr(self.game, 'metal_obstacles', [])):
            if metal.rect.collidepoint(wx, wy):
                self.game.metal_obstacles.remove(metal)
                self.undo_stack.append(('DEL_METAL', metal))
                self.show_message("Deleted Metal Obstacle")
                return

        # 7. Delete Rope Blocks
        for rope in list(getattr(self.game, 'rope_blocks', [])):
            if rope.rect.collidepoint(wx, wy):
                self.game.rope_blocks.remove(rope)
                self.undo_stack.append(('DEL_ROPE', rope))
                self.show_message("Deleted Rope Block")
                return

        # 8. Delete Breakable Wood
        for wood in list(self.game.breakable_woods):
            if wood.rect.collidepoint(wx, wy):
                self.game.breakable_woods.remove(wood)
                self.undo_stack.append(('DEL_WOOD', wood))
                self.show_message("Deleted Breakable Wood")
                return

        # 9. Delete Platforms
        for plat in list(self.game.platforms):
            if plat.rect.collidepoint(wx, wy):
                self.game.platforms.remove(plat)
                self.undo_stack.append(('DEL_PLATFORM', plat))
                self.show_message("Deleted Platform")
                return

    def undo(self):
        if not self.undo_stack:
            self.show_message("Nothing to undo!")
            return
        action, item = self.undo_stack.pop()
        if action == 'ADD_PLATFORM' and item in self.game.platforms:
            self.game.platforms.remove(item)
        elif action == 'DEL_PLATFORM':
            self.game.platforms.append(item)
        elif action == 'ADD_WOOD' and item in self.game.breakable_woods:
            self.game.breakable_woods.remove(item)
        elif action == 'DEL_WOOD':
            self.game.breakable_woods.append(item)
        elif action == 'ADD_METAL' and item in getattr(self.game, 'metal_obstacles', []):
            self.game.metal_obstacles.remove(item)
        elif action == 'DEL_METAL':
            self.game.metal_obstacles.append(item)
        elif action == 'ADD_ROPE' and item in getattr(self.game, 'rope_blocks', []):
            self.game.rope_blocks.remove(item)
        elif action == 'DEL_ROPE':
            self.game.rope_blocks.append(item)
        elif action == 'ADD_GRAPPLE' and item in getattr(self.game, 'grapple_pickups', []):
            self.game.grapple_pickups.remove(item)
        elif action == 'DEL_GRAPPLE':
            self.game.grapple_pickups.append(item)
        elif action == 'ADD_ENEMY' and item in self.game.enemies:
            self.game.enemies.remove(item)
        elif action == 'DEL_ENEMY':
            self.game.enemies.append(item)
        elif action == 'ADD_SPIKE' and item in self.game.spikes:
            self.game.spikes.remove(item)
        elif action == 'DEL_SPIKE':
            self.game.spikes.append(item)
        elif action == 'ADD_ALLY' and item in self.game.allies:
            self.game.allies.remove(item)
        elif action == 'DEL_ALLY':
            self.game.allies.append(item)
        elif action == 'ADD_TURRET' and item in self.game.turrets:
            self.game.turrets.remove(item)
        elif action == 'DEL_TURRET':
            self.game.turrets.append(item)
        elif action == 'SET_GOAL':
            self.game.portal.rect.x, self.game.portal.rect.y = item
        elif action == 'SET_SPAWN':
            self.game.start_x, self.game.pole_rect.x, self.game.pole_rect.y = item
            self.game.player.rect.x = self.game.start_x
        self.show_message(f"Undid {action}")

    def export_level(self):
        """Prints exact python code to terminal and saves a JSON file."""
        code_lines = ["        self.platforms = ["]
        for p in self.game.platforms:
            code_lines.append(f"            Platform({p.rect.x}, {p.rect.y}, {p.rect.w}, {p.rect.h}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.breakable_woods = [")
        for w in self.game.breakable_woods:
            code_lines.append(f"            BreakableWood({w.rect.x}, {w.rect.y}, {w.rect.w}, {w.rect.h}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.metal_obstacles = [")
        for m in getattr(self.game, 'metal_obstacles', []):
            code_lines.append(f"            MetalObstacle({m.rect.x}, {m.rect.y}, {m.rect.w}, {m.rect.h}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.rope_blocks = [")
        for r in getattr(self.game, 'rope_blocks', []):
            code_lines.append(f"            RopeBlock({r.rect.x}, {r.rect.y}, {r.rect.w}, {r.rect.h}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.grapple_pickups = [")
        for g in getattr(self.game, 'grapple_pickups', []):
            code_lines.append(f"            GrapplePickup({int(g.start_x)}, {int(g.start_y)}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.hanging_ropes = []\n")

        code_lines.append("        self.enemies = [")
        for e in self.game.enemies:
            code_lines.append(f"            CircleEnemy({int(e.start_x)}, {int(e.y)}, patrol_range={e.patrol_range}, speed={e.speed}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.spikes = [")
        for s in self.game.spikes:
            code_lines.append(f"            Spike({s.rect.x}, {s.rect.y}, {s.rect.w}, {s.rect.h}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.allies = [")
        for a in self.game.allies:
            code_lines.append(f"            TriAnger({int(a.x)}, {int(a.y)}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.turrets = [")
        for t in self.game.turrets:
            code_lines.append(f"            EnemyTurret({int(t.x)}, {int(t.y)}),")
        code_lines.append("        ]\n")

        code_lines.append("        self.bullets = []\n")

        export_text = "\n".join(code_lines)
        print("\n" + "=" * 60)
        print("EXPORTED LEVEL CODE (Copy & paste into Game.reset()):")
        print("=" * 60)
        print(export_text)
        print("=" * 60 + "\n")

        # Save JSON file
        try:
            data = {
                "platforms": [[p.rect.x, p.rect.y, p.rect.w, p.rect.h] for p in self.game.platforms],
                "breakable_woods": [[w.rect.x, w.rect.y, w.rect.w, w.rect.h] for w in self.game.breakable_woods],
                "metal_obstacles": [[m.rect.x, m.rect.y, m.rect.w, m.rect.h] for m in getattr(self.game, 'metal_obstacles', [])],
                "rope_blocks": [[r.rect.x, r.rect.y, r.rect.w, r.rect.h] for r in getattr(self.game, 'rope_blocks', [])],
                "grapple_pickups": [[int(g.start_x), int(g.start_y)] for g in getattr(self.game, 'grapple_pickups', [])],
                "enemies": [[int(e.start_x), int(e.y), e.patrol_range, e.speed] for e in self.game.enemies],
                "spikes": [[s.rect.x, s.rect.y, s.rect.w, s.rect.h] for s in self.game.spikes],
                "allies": [[int(a.x), int(a.y)] for a in self.game.allies],
                "turrets": [[int(t.x), int(t.y)] for t in self.game.turrets],
                "goal": [self.game.portal.rect.x, self.game.portal.rect.y],
                "spawn": [self.game.start_x, self.game.pole_rect.x, self.game.pole_rect.y]
            }
            with open("custom_level.json", "w") as f:
                json.dump(data, f, indent=4)
            self.show_message("Level code printed to console & saved to custom_level.json!", 240)
        except Exception as err:
            self.show_message("Code exported to console!", 180)

    def update(self):
        """Smooth camera panning in build mode."""
        if not self.active:
            return

        keys = pygame.key.get_pressed()
        pan_speed = 14 if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) else 8

        # Pan with A/D or Left/Right arrows
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.cam_x = max(0, self.cam_x - pan_speed)
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.cam_x += pan_speed

        if self.message_timer > 0:
            self.message_timer -= 1

    def draw(self):
        """Renders the editor view, grid, and toolbar."""
        screen = self.game.screen
        cam_x = self.cam_x

        # 1. Fill background
        screen.fill((18, 18, 22))

        # 2. Draw subtle grid dots
        if self.grid_enabled:
            start_x = -(cam_x % self.grid_size)
            for gx in range(start_x, self.game.screen.get_width(), self.grid_size):
                for gy in range(0, self.game.screen.get_height(), self.grid_size):
                    screen.set_at((gx, gy), (45, 45, 55))

        # 3. Draw game entities
        for p in self.game.platforms:
            p.draw(screen, cam_x)
        for w in self.game.breakable_woods:
            w.draw(screen, cam_x)
        for m in getattr(self.game, 'metal_obstacles', []):
            m.draw(screen, cam_x)
        for rb in getattr(self.game, 'rope_blocks', []):
            rb.draw(screen, cam_x)
        for gp in getattr(self.game, 'grapple_pickups', []):
            gp.draw(screen, cam_x)
        for s in self.game.spikes:
            s.draw(screen, cam_x)
        for e in self.game.enemies:
            e.draw(screen, cam_x)
            # Draw patrol line indicator
            p_start = int(e.start_x - e.patrol_range - cam_x)
            p_end = int(e.start_x + e.patrol_range - cam_x)
            pygame.draw.line(screen, (220, 50, 50), (p_start, int(e.y)), (p_end, int(e.y)), 1)
            pygame.draw.circle(screen, (255, 100, 100), (p_start, int(e.y)), 3)
            pygame.draw.circle(screen, (255, 100, 100), (p_end, int(e.y)), 3)
        for t in self.game.turrets:
            t.draw(screen, cam_x)
        for a in self.game.allies:
            a.draw(screen, cam_x)

        self.game.portal.draw(screen, cam_x)

        # Draw Player & Anchor Pole
        pole_sx = self.game.pole_rect.x - cam_x
        pygame.draw.rect(screen, (90, 90, 95), (pole_sx, self.game.pole_rect.y, self.game.pole_rect.w, self.game.pole_rect.h))
        self.game.player.draw(screen, cam_x)

        # 4. Draw drag placement outline
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.screen_to_world(mx, my)

        if self.drag_start_world:
            sx, sy = self.drag_start_world
            rx = min(sx, wx) - cam_x
            ry = min(sy, wy)
            rw = max(20, abs(wx - sx))
            rh = max(20, abs(wy - sy))
            cur_color = self.TOOLS[self.current_tool_idx]["color"]
            pygame.draw.rect(screen, cur_color, (rx, ry, rw, rh), 2)
        elif my >= 45:
            # Ghost cursor preview
            cur_tool = self.TOOLS[self.current_tool_idx]["id"]
            cur_color = self.TOOLS[self.current_tool_idx]["color"]
            snapped_sx = wx - cam_x
            snapped_sy = wy
            if cur_tool == "PLATFORM":
                pygame.draw.rect(screen, cur_color, (snapped_sx, snapped_sy, 120, 30), 1)
            elif cur_tool == "WOOD":
                pygame.draw.rect(screen, cur_color, (snapped_sx, snapped_sy, 28, 70), 1)
            elif cur_tool == "METAL":
                pygame.draw.rect(screen, cur_color, (snapped_sx, snapped_sy, 32, 70), 1)
            elif cur_tool == "ROPE":
                pygame.draw.rect(screen, cur_color, (snapped_sx, snapped_sy, 80, 24), 1)
            elif cur_tool == "GRAPPLE":
                pygame.draw.circle(screen, cur_color, (snapped_sx, snapped_sy), 12, 1)
                pygame.draw.line(screen, (255, 255, 255), (snapped_sx, snapped_sy - 4), (snapped_sx, snapped_sy + 6), 2)
                pygame.draw.arc(screen, (255, 255, 255), (snapped_sx - 6, snapped_sy + 1, 12, 8), 0, math.pi, 2)
            elif cur_tool in ("ENEMY", "SPAWN"):
                pygame.draw.circle(screen, cur_color, (snapped_sx, snapped_sy), 15, 1)
            elif cur_tool == "GOAL":
                pygame.draw.rect(screen, cur_color, (snapped_sx, snapped_sy, 40, 70), 1)
            elif cur_tool == "SPIKE":
                pts = [(snapped_sx, snapped_sy - 24), (snapped_sx - 12, snapped_sy), (snapped_sx + 12, snapped_sy)]
                pygame.draw.polygon(screen, cur_color, pts, 1)
            elif cur_tool == "ALLY":
                pts = [(snapped_sx, snapped_sy - 11), (snapped_sx - 11, snapped_sy + 10), (snapped_sx + 11, snapped_sy + 10)]
                pygame.draw.polygon(screen, cur_color, pts, 1)
                pygame.draw.rect(screen, (100, 100, 110), (snapped_sx - 18, snapped_sy - 18, 36, 36), 1)
            elif cur_tool == "TURRET":
                pygame.draw.circle(screen, cur_color, (snapped_sx, snapped_sy), 16, 1)
                pygame.draw.line(screen, cur_color, (snapped_sx, snapped_sy), (snapped_sx + 20, snapped_sy), 3)

        # 5. Top Toolbar Header (semi-transparent dark background)
        header_surf = pygame.Surface((self.game.screen.get_width(), 42), pygame.SRCALPHA)
        header_surf.fill((25, 25, 30, 235))
        screen.blit(header_surf, (0, 0))
        pygame.draw.line(screen, (60, 60, 70), (0, 42), (self.game.screen.get_width(), 42), 1)

        # Draw tool selector buttons
        btn_w = 68
        gap = 4
        start_x = 4
        for i, tool in enumerate(self.TOOLS):
            bx = start_x + i * (btn_w + gap)
            is_active = (i == self.current_tool_idx)
            btn_col = tool["color"] if is_active else (45, 45, 52)
            txt_col = (255, 255, 255) if is_active else (180, 180, 190)

            pygame.draw.rect(screen, btn_col, (bx, 6, btn_w, 28), border_radius=4)
            pygame.draw.rect(screen, (80, 80, 95), (bx, 6, btn_w, 28), 1, border_radius=4)
            lbl = self.font_btn.render(tool["name"], True, txt_col)
            screen.blit(lbl, (bx + (btn_w - lbl.get_width()) // 2, 13))

        # Bottom help & status toast
        if self.message_timer > 0:
            toast = self.font_small.render(self.message, True, (255, 230, 90))
            bg = pygame.Rect(10, self.game.screen.get_height() - 26, toast.get_width() + 14, 20)
            pygame.draw.rect(screen, (30, 30, 35), bg, border_radius=3)
            pygame.draw.rect(screen, (80, 80, 90), bg, 1, border_radius=3)
            screen.blit(toast, (17, self.game.screen.get_height() - 24))

        # Key help overlay on top right
        help_txt = self.font_small.render("[B] Play/Build  [F11] Fullscreen  [A/D] Pan  [R-Click] Delete  [Z] Undo  [S] Export", True, (160, 160, 175))
        screen.blit(help_txt, (self.game.screen.get_width() - help_txt.get_width() - 10, 48))

    def run_standalone(self):
        """Runs the level editor directly as a standalone program."""
        clock = pygame.time.Clock()
        running = True
        while running:
            clock.tick(60)
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_b:
                    self.toggle()
                else:
                    if self.active:
                        self.handle_event(event)
                    else:
                        self.game.handle_events([event])

            if self.active:
                self.update()
                self.draw()
            else:
                self.game.update()
                self.game.draw()

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    from main import Game
    game_instance = Game()
    editor = LevelEditor(game_instance)
    editor.active = True
    editor.run_standalone()
