import pygame
import math
import random

COLOR_BLACK = (20, 20, 20)
COLOR_BLUE  = (0, 180, 255)
COLOR_RED   = (255, 60, 60)


class HangingRope:
    def __init__(self, x, y, length):
        self.x = float(x)
        self.y = float(y)
        self.length = max(30.0, float(length))
        self.timer = 0.0
        self.swing_amp = 7.0

    def update(self):
        self.timer += 0.05
        self.swing_amp *= 0.994

    def draw(self, screen, camera_x):
        sx = self.x - camera_x
        sy = self.y
        sway = math.sin(self.timer) * self.swing_amp
        end_x = sx + sway
        end_y = sy + self.length

        mid_x = (sx + end_x) / 2 + sway * 0.4
        mid_y = sy + self.length * 0.5
        num_segs = 6
        prev_pt = (int(sx), int(sy))
        for i in range(1, num_segs + 1):
            t = i / float(num_segs)
            pt_x = (1 - t)**2 * sx + 2 * (1 - t) * t * mid_x + t**2 * end_x
            pt_y = (1 - t)**2 * sy + 2 * (1 - t) * t * mid_y + t**2 * end_y
            cur_pt = (int(pt_x), int(pt_y))
            pygame.draw.line(screen, (240, 240, 248), prev_pt, cur_pt, 2)
            pygame.draw.circle(screen, (170, 175, 190), cur_pt, 2)
            prev_pt = cur_pt
        pygame.draw.circle(screen, (80, 85, 95), (int(sx), int(sy)), 4)


# --- PLAYER ---
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 28)
        self.vx = 0
        self.vy = 0
        self.direction = "R" 
        self.is_grounded = False

        self.dash_timer = 0
        self.dash_cooldown = 0
        self.can_dash = True
        self.dash_trail = []
        self.dash_key_prev = False

        self.jumps_left = 2
        self.jump_key_prev = False
        self.jump_particles = []

        self.dizzy_timer = 0

        self.tilt_angle = 0.0

        self.has_grapple = False
        self.active_grapple = None
        self.grapple_target = None
        self.dash_target = None
        self.holding_dash_lock = False
        self.is_dash_locked = False
        
        self.health = 100
        self.killed_by_boss = False
        self.god_mode = False
        self.prev_x = x
        self.prev_y = y

    def spawn_jump_effect(self, is_double=False):
        color = (0, 220, 255) if is_double else (210, 210, 220)
        count = 7 if is_double else 5
        spread = 5.0 if is_double else 3.5
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(0.5, 2.5) if not is_double else random.uniform(-1.5, 1.8)
            self.jump_particles.append({
                'x': float(self.rect.centerx),
                'y': float(self.rect.bottom),
                'vx': vx,
                'vy': vy,
                'life': 14,
                'color': color,
                'radius': random.uniform(2.5, 4.2)
            })

    def update_grapple_targeting(self, rope_blocks, turrets, enemies, mouse_wx, mouse_wy):
        if not self.has_grapple or self.active_grapple is not None:
            self.grapple_target = None
            return

        px = float(self.rect.centerx)
        py = float(self.rect.centery)
        candidates = []

        for rb in rope_blocks:
            cx = float(rb.rect.centerx)
            cy = float(rb.rect.centery)
            d_player = math.hypot(px - cx, py - cy)
            if d_player <= 370.0:
                d_mouse = math.hypot(mouse_wx - cx, mouse_wy - cy)
                candidates.append((d_mouse - 50.0, d_mouse, d_player, rb))

        for t in turrets:
            if not t.is_dead:
                cx = float(t.x)
                cy = float(t.y)
                d_player = math.hypot(px - cx, py - cy)
                if d_player <= 370.0:
                    d_mouse = math.hypot(mouse_wx - cx, mouse_wy - cy)
                    candidates.append((d_mouse, d_mouse, d_player, t))

        for e in enemies:
            if not e.is_dead:
                cx = float(e.x)
                cy = float(e.y)
                d_player = math.hypot(px - cx, py - cy)
                if d_player <= 370.0:
                    d_mouse = math.hypot(mouse_wx - cx, mouse_wy - cy)
                    candidates.append((d_mouse, d_mouse, d_player, e))

        if candidates:
            candidates.sort(key=lambda c: c[0])
            _, best_d_mouse, best_d_player, best_cand = candidates[0]
            if best_d_mouse <= 280.0 or best_d_player <= 220.0:
                self.grapple_target = best_cand
            else:
                self.grapple_target = None
        else:
            self.grapple_target = None

    def draw_grapple_reticle(self, screen, camera_x):
        if not self.has_grapple or not self.grapple_target or self.active_grapple is not None:
            return
        target = self.grapple_target
        tx = int(target.rect.centerx - camera_x)
        ty = int(target.rect.centery)
        r = getattr(target, 'radius', None)
        if r is None:
            r = max(18, max(target.rect.w, target.rect.h) // 2 + 5)
        else:
            r = r + 5
        pulse = int(math.sin(pygame.time.get_ticks() * 0.01) * 2)
        r += pulse

        color = (0, 220, 255)
        color_bright = (180, 245, 255)

        pygame.draw.circle(screen, color_bright, (tx, ty), 3)
        pygame.draw.line(screen, color, (tx - 6, ty), (tx + 6, ty), 1)
        pygame.draw.line(screen, color, (tx, ty - 6), (tx, ty + 6), 1)
        pygame.draw.circle(screen, color, (tx, ty), r, 2)

        b = 6
        pygame.draw.line(screen, color_bright, (tx - r - b, ty - r), (tx - r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx - r, ty - r - b), (tx - r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty - r), (tx + r + b, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty - r - b), (tx + r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx - r - b, ty + r), (tx - r, ty + r), 2)
        pygame.draw.line(screen, color_bright, (tx - r, ty + r), (tx - r, ty + r + b), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty + r), (tx + r + b, ty + r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty + r), (tx + r, ty + r + b), 2)

        px = int(self.rect.centerx - camera_x)
        py = int(self.rect.centery)
        pygame.draw.line(screen, (0, 160, 210), (px, py), (tx, ty), 1)

    def update_dash_targeting(self, enemies, turrets, mouse_wx, mouse_wy, is_holding_rmb):
        if not is_holding_rmb or self.dash_timer > 0:
            self.dash_target = None
            self.holding_dash_lock = False
            return

        self.holding_dash_lock = True
        px = float(self.rect.centerx)
        py = float(self.rect.centery)
        candidates = []
        max_reach = 245.0

        for e in enemies:
            if not e.is_dead:
                cx = float(e.rect.centerx)
                cy = float(e.rect.centery)
                d_player = math.hypot(px - cx, py - cy)
                if d_player <= max_reach:
                    d_mouse = math.hypot(mouse_wx - cx, mouse_wy - cy)
                    candidates.append((d_mouse, d_player, e))

        for t in turrets:
            if not t.is_dead:
                cx = float(t.rect.centerx)
                cy = float(t.rect.centery)
                d_player = math.hypot(px - cx, py - cy)
                if d_player <= max_reach:
                    d_mouse = math.hypot(mouse_wx - cx, mouse_wy - cy)
                    candidates.append((d_mouse, d_player, t))

        if candidates:
            candidates.sort(key=lambda c: c[0])
            best_d_mouse, best_d_player, best_cand = candidates[0]
            if best_d_mouse <= 250.0:
                self.dash_target = best_cand
            else:
                self.dash_target = None
        else:
            self.dash_target = None

    def draw_dash_reticle(self, screen, camera_x):
        if not self.holding_dash_lock or not self.dash_target or self.dash_timer > 0:
            return
        target = self.dash_target
        tx = int(target.rect.centerx - camera_x)
        ty = int(target.rect.centery)
        r = getattr(target, 'radius', None)
        if r is None:
            r = max(18, max(target.rect.w, target.rect.h) // 2 + 5)
        else:
            r = r + 5
        pulse = int(math.sin(pygame.time.get_ticks() * 0.012) * 3)
        r += pulse

        color = (255, 60, 60)
        color_bright = (255, 220, 100)

        pygame.draw.circle(screen, color_bright, (tx, ty), 3)
        pygame.draw.line(screen, color, (tx - 6, ty), (tx + 6, ty), 1)
        pygame.draw.line(screen, color, (tx, ty - 6), (tx, ty + 6), 1)
        pygame.draw.circle(screen, color, (tx, ty), r, 2)

        b = 6
        pygame.draw.line(screen, color_bright, (tx - r - b, ty - r), (tx - r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx - r, ty - r - b), (tx - r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty - r), (tx + r + b, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty - r - b), (tx + r, ty - r), 2)
        pygame.draw.line(screen, color_bright, (tx - r - b, ty + r), (tx - r, ty + r), 2)
        pygame.draw.line(screen, color_bright, (tx - r, ty + r), (tx - r, ty + r + b), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty + r), (tx + r + b, ty + r), 2)
        pygame.draw.line(screen, color_bright, (tx + r, ty + r), (tx + r, ty + r + b), 2)

        px = int(self.rect.centerx - camera_x)
        py = int(self.rect.centery)
        pygame.draw.line(screen, (255, 80, 80), (px, py), (tx, ty), 2)

    def execute_dash_attack(self):
        if not self.dash_target or not self.can_dash or self.dash_cooldown > 0 or self.dizzy_timer > 0:
            return False
        target = self.dash_target
        dx = float(target.rect.centerx - self.rect.centerx)
        dy = float(target.rect.centery - self.rect.centery)
        dist = math.hypot(dx, dy)
        if dist < 4:
            return False

        speed = 24.0
        self.vx = (dx / dist) * speed
        self.vy = (dy / dist) * speed
        self.dash_timer = max(10, int(dist / speed) + 2)
        self.dash_cooldown = 100
        self.can_dash = False
        self.is_dash_locked = True
        self.direction = "R" if dx >= 0 else "L"
        self.dash_target = None
        return True

    def shoot_grapple(self, target_world_x, target_world_y):
        if not self.has_grapple or self.active_grapple is not None:
            return
        dx = target_world_x - self.rect.centerx
        dy = target_world_y - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist < 6:
            return
        speed = 28.0
        self.active_grapple = {
            'x': float(self.rect.centerx),
            'y': float(self.rect.centery),
            'vx': (dx / dist) * speed,
            'vy': (dy / dist) * speed,
            'state': 'FLYING',
            'dist_traveled': 0.0,
            'max_dist': 360.0,
            'anchor_x': 0.0,
            'anchor_y': 0.0,
            'length': 0.0,
            'target_type': None,
            'target_entity': None
        }

    def release_grapple(self, game=None):
        if not self.active_grapple:
            return
        if self.active_grapple['state'] == 'ATTACHED':
            if self.active_grapple['target_type'] in ('ROPE_BLOCK', 'TURRET') and game is not None:
                ax = self.active_grapple['anchor_x']
                ay = self.active_grapple['anchor_y']
                rlen = self.active_grapple['length']
                game.hanging_ropes.append(HangingRope(ax, ay, rlen))
        self.active_grapple = None

    def update_grapple(self, rope_blocks, turrets, enemies, game):
        if not self.active_grapple:
            return

        g = self.active_grapple
        if g['state'] == 'FLYING':
            steps = 2
            step_vx = g['vx'] / steps
            step_vy = g['vy'] / steps
            step_dist = math.hypot(step_vx, step_vy)
            for _ in range(steps):
                g['x'] += step_vx
                g['y'] += step_vy
                g['dist_traveled'] += step_dist
                hook_rect = pygame.Rect(int(g['x']) - 6, int(g['y']) - 6, 12, 12)

                for rb in rope_blocks:
                    if hook_rect.colliderect(rb.rect):
                        g['state'] = 'ATTACHED'
                        g['target_type'] = 'ROPE_BLOCK'
                        g['anchor_x'] = g['x']
                        g['anchor_y'] = g['y']
                        g['length'] = max(35.0, math.hypot(self.rect.centerx - g['anchor_x'], self.rect.centery - g['anchor_y']))
                        break

                if g['state'] == 'FLYING':
                    for t in turrets:
                        if not t.is_dead and (hook_rect.colliderect(t.rect) or math.hypot(t.x - g['x'], t.y - g['y']) <= 18):
                            g['state'] = 'ATTACHED'
                            g['target_type'] = 'TURRET'
                            g['anchor_x'] = float(t.x)
                            g['anchor_y'] = float(t.y)
                            g['length'] = max(35.0, math.hypot(self.rect.centerx - t.x, self.rect.centery - t.y))
                            break

                if g['state'] == 'FLYING':
                    for e in enemies:
                        if not e.is_dead and (hook_rect.colliderect(e.rect) or math.hypot(e.x - g['x'], e.y - g['y']) <= 18):
                            g['state'] = 'ATTACHED'
                            g['target_type'] = 'ENEMY'
                            g['target_entity'] = e
                            g['length'] = max(40.0, math.hypot(self.rect.centerx - e.x, self.rect.centery - e.y))
                            break

                if g['state'] == 'ATTACHED' or g['dist_traveled'] >= g['max_dist']:
                    break

            if g['dist_traveled'] >= g['max_dist'] and g['state'] == 'FLYING':
                self.active_grapple = None

        elif g['state'] == 'ATTACHED':
            if g['target_type'] in ('ROPE_BLOCK', 'TURRET'):
                ax = g['anchor_x']
                ay = g['anchor_y']
                dx = self.rect.centerx - ax
                dy = self.rect.centery - ay
                cur_dist = math.hypot(dx, dy)
                g['length'] = max(32.0, g['length'] - 0.55)
                rope_len = g['length']

                if cur_dist >= rope_len and cur_dist > 0:
                    nx = dx / cur_dist
                    ny = dy / cur_dist
                    tx = -ny
                    ty = nx

                    self.rect.centerx = int(ax + nx * rope_len)
                    self.rect.centery = int(ay + ny * rope_len)

                    tangent_vel = self.vx * tx + self.vy * ty
                    tangent_vel += 0.52 * ty

                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                        tangent_vel += 0.4 if tx < 0 else -0.4
                    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                        tangent_vel += 0.4 if tx > 0 else -0.4

                    self.vx = tangent_vel * tx - nx * 0.22
                    self.vy = tangent_vel * ty - ny * 0.22
                    self.is_grounded = False
                    self.jumps_left = 2

            elif g['target_type'] == 'ENEMY':
                e = g['target_entity']
                if e.is_dead:
                    self.active_grapple = None
                else:
                    g['length'] = max(28.0, g['length'] - 0.5)
                    dx = e.x - self.rect.centerx
                    dy = e.y - self.rect.centery
                    dist = math.hypot(dx, dy)
                    rope_len = g['length']
                    if dist > rope_len and dist > 0:
                        nx = dx / dist
                        ny = dy / dist
                        e.x = self.rect.centerx + nx * rope_len
                        e.y = self.rect.centery + ny * rope_len
                        e.rect.centerx = int(e.x)
                        e.rect.centery = int(e.y)
                    e.x += self.vx * 0.75 - (dx / max(1.0, dist)) * 0.35
                    e.y += self.vy * 0.75 - (dy / max(1.0, dist)) * 0.35
                    e.rect.centerx = int(e.x)
                    e.rect.centery = int(e.y)

    def handle_input(self, keys):
        jump_down = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        jump_pressed = jump_down and not self.jump_key_prev
        self.jump_key_prev = jump_down

        if self.dizzy_timer > 0:
            return

        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            move_dir += 1

        dash_down = keys[pygame.K_LSHIFT] or keys[pygame.K_k]
        dash_pressed = dash_down and not self.dash_key_prev
        self.dash_key_prev = dash_down

        if dash_pressed and self.can_dash and self.dash_cooldown <= 0:
            if self.dash_target is not None:
                self.execute_dash_attack()
            else:
                dash_dir = 1 if self.direction == "R" else -1
                self.vx = dash_dir * 20
                self.vy = 0
                self.dash_timer = 10
                self.dash_cooldown = 100
                self.can_dash = False

        target_speed = move_dir * 5
        if move_dir != 0:
            self.vx += (target_speed - self.vx) * (0.35 if self.is_grounded else 0.2)
        else:
            self.vx *= (0.8 if self.is_grounded else 0.96)
            if abs(self.vx) < 0.1:
                self.vx = 0

        if jump_pressed and self.jumps_left > 0:
            is_double = (self.jumps_left == 1)
            self.vy = -12
            self.is_grounded = False
            self.jumps_left -= 1
            self.spawn_jump_effect(is_double=is_double)

    def update(self, platforms):
        if self.vx > 0:
            self.direction = "R"
        elif self.vx < 0:
            self.direction = "L"

        self.prev_x = self.rect.x
        self.prev_y = self.rect.y

        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
        if self.dizzy_timer > 0:
            self.dizzy_timer -= 1
        if self.dash_timer > 0:
            self.dash_timer -= 1
            if not self.is_dash_locked:
                self.vy = 0
            self.dash_trail.append({'x': self.rect.x, 'y': self.rect.y, 'alpha': 160})
        else:
            self.is_dash_locked = False
            if not self.is_grounded:
                self.vy += 0.65
                if self.vy > 14:
                    self.vy = 14
            else:
                self.vy = 0

        for ghost in self.dash_trail:
            ghost['alpha'] -= 25
        self.dash_trail = [g for g in self.dash_trail if g['alpha'] > 0]

        for p in self.jump_particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            p['radius'] = max(0.5, p['radius'] * 0.9)
        self.jump_particles = [p for p in self.jump_particles if p['life'] > 0]

        self.rect.x += int(self.vx)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vx > 0:
                    self.rect.right = platform.rect.left
                elif self.vx < 0:
                    self.rect.left = platform.rect.right
                self.vx = 0

        self.rect.y += int(self.vy)
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vy > 0:
                    self.rect.bottom = platform.rect.top
                    self.vy = 0
                elif self.vy < 0:
                    self.rect.top = platform.rect.bottom
                    self.vy = 0

        ground_sensor = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.w, 2)
        self.is_grounded = any(ground_sensor.colliderect(p.rect) for p in platforms)
        if self.is_grounded:
            if self.vy >= 0:
                self.vy = 0
            self.can_dash = True
            self.jumps_left = 2
        elif self.jumps_left == 2:
            self.jumps_left = 1

        if self.is_grounded or self.dash_timer > 0:
            target_tilt = 0.0
        else:
            tilt_mag = max(-13.0, min(13.0, -self.vy * 1.5))
            target_tilt = tilt_mag if self.direction == "R" else -tilt_mag

        self.tilt_angle += (target_tilt - self.tilt_angle) * 0.22

    def draw(self, screen, camera_x):
        self.draw_grapple_reticle(screen, camera_x)
        self.draw_dash_reticle(screen, camera_x)
        screen_x = self.rect.x - camera_x

        for p in self.jump_particles:
            psx = p['x'] - camera_x
            pygame.draw.circle(screen, p['color'], (int(psx), int(p['y'])), max(1, int(p['radius'])))

        for ghost in self.dash_trail:
            gx = ghost['x'] - camera_x
            gy = ghost['y']
            ghost_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
            ghost_surf.fill((0, 200, 255, max(0, min(255, ghost['alpha']))))
            screen.blit(ghost_surf, (gx, gy))

        if self.active_grapple:
            g = self.active_grapple
            px = screen_x + self.rect.w // 2
            py = self.rect.centery
            if g['state'] == 'FLYING':
                gx = int(g['x'] - camera_x)
                gy = int(g['y'])
                pygame.draw.line(screen, (245, 245, 252), (px, py), (gx, gy), 2)
                pygame.draw.circle(screen, (210, 215, 225), (gx, gy), 4)
            elif g['state'] == 'ATTACHED':
                if g['target_type'] == 'ENEMY':
                    ax = int(g['target_entity'].x - camera_x)
                    ay = int(g['target_entity'].y)
                else:
                    ax = int(g['anchor_x'] - camera_x)
                    ay = int(g['anchor_y'])
                pygame.draw.line(screen, (245, 245, 252), (px, py), (ax, ay), 3)
                pygame.draw.line(screen, (170, 175, 190), (px, py), (ax, ay), 1)
                pygame.draw.circle(screen, (80, 85, 95), (px, py), 3)
                pygame.draw.circle(screen, (220, 225, 235), (ax, ay), 5)

        body_surf = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        body_color = COLOR_RED if self.killed_by_boss else COLOR_BLUE
        pygame.draw.rect(body_surf, body_color, (0, 0, self.rect.w, self.rect.h))
        if self.direction == "R":
            pygame.draw.rect(body_surf, COLOR_BLACK, (3, 2, self.rect.w - 20, self.rect.h - 18))
            pygame.draw.rect(body_surf, COLOR_BLACK, (19, 2, self.rect.w - 20, self.rect.h - 18))
        else:
            pygame.draw.rect(body_surf, COLOR_BLACK, (1, 2, self.rect.w - 20, self.rect.h - 18))
            pygame.draw.rect(body_surf, COLOR_BLACK, (17, 2, self.rect.w - 20, self.rect.h - 18))

        if abs(self.tilt_angle) > 0.4:
            rotated_surf = pygame.transform.rotate(body_surf, self.tilt_angle)
            rot_rect = rotated_surf.get_rect(center=(screen_x + self.rect.w // 2, self.rect.centery))
            screen.blit(rotated_surf, rot_rect.topleft)
        else:
            screen.blit(body_surf, (screen_x, self.rect.y))

        if self.dizzy_timer > 0:
            head_x = screen_x + self.rect.w // 2
            head_y = self.rect.y - 8
            orbit_phase = (60 - self.dizzy_timer) * 0.22
            for i in range(3):
                angle = orbit_phase + (i * (2 * math.pi / 3))
                star_x = head_x + math.cos(angle) * 14
                star_y = head_y + math.sin(angle) * 5
                pygame.draw.circle(screen, (255, 230, 60), (int(star_x), int(star_y)), 3)
                pygame.draw.line(screen, (255, 255, 180), (int(star_x) - 4, int(star_y)), (int(star_x) + 4, int(star_y)), 1)
                pygame.draw.line(screen, (255, 255, 180), (int(star_x), int(star_y) - 4), (int(star_x), int(star_y) + 4), 1)

        if self.dash_cooldown > 0:
            bar_w = self.rect.w
            bar_h = 4
            bar_x = screen_x
            bar_y = self.rect.bottom + 4
            pygame.draw.rect(screen, (35, 35, 45), (bar_x, bar_y, bar_w, bar_h))
            progress = max(0.0, min(1.0, 1.0 - (self.dash_cooldown / 100.0)))
            fill_w = int(bar_w * progress)
            if fill_w > 0:
                pygame.draw.rect(screen, (0, 220, 255), (bar_x, bar_y, fill_w, bar_h))
            pygame.draw.rect(screen, (15, 15, 20), (bar_x, bar_y, bar_w, bar_h), 1)

