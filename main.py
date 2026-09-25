import pygame
import sys
import random
import math
import os
import json

from player import Player, HangingRope
from boss import GiantWatcher
from menu import load_best_time, save_best_time, MainMenu

# --- CONSTANTS ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450

COLOR_BLACK = (20, 20, 20)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY  = (100, 100, 100)
COLOR_BLUE  = (0, 180, 255)
COLOR_GREEN = (50, 220, 80)
COLOR_RED   = (255, 60, 60)
COLOR_PURPLE = (180, 0, 180)


# --- PLATFORM ---
class Platform:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x):
        screen_x = self.rect.x - camera_x
        draw_rect = (screen_x, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(screen, COLOR_GRAY, draw_rect)


# --- BREAKABLE WOOD ---
class BreakableWood:
    def __init__(self, x, y, width=28, height=70):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_broken = False
        self.particles = []

    def break_wood(self):
        if not self.is_broken:
            self.is_broken = True
            for _ in range(12):
                vx = random.uniform(-5.0, 6.0)
                vy = random.uniform(-6.0, -1.0)
                size = random.randint(4, 8)
                self.particles.append([float(self.rect.centerx), float(self.rect.centery), vx, vy, size])

    def update(self, player):
        if self.is_broken:
            for p in self.particles:
                p[0] += p[2]
                p[1] += p[3]
                p[3] += 0.45
            return

        if self.rect.colliderect(player.rect):
            if player.dash_timer > 0 or abs(player.vx) > 12:
                self.break_wood()
            else:
                if player.rect.centerx < self.rect.centerx:
                    player.rect.right = self.rect.left
                    if player.vx > 0:
                        player.vx = 0
                else:
                    player.rect.left = self.rect.right
                    if player.vx < 0:
                        player.vx = 0

    def draw(self, screen, camera_x):
        if not self.is_broken:
            sx = self.rect.x - camera_x
            draw_rect = pygame.Rect(sx, self.rect.y, self.rect.w, self.rect.h)
            pygame.draw.rect(screen, (140, 85, 45), draw_rect)
            pygame.draw.rect(screen, (75, 42, 20), draw_rect, 2)
            pygame.draw.line(screen, (95, 55, 25), (sx + 4, self.rect.y + 4), (sx + self.rect.w - 4, self.rect.bottom - 4), 2)
            pygame.draw.line(screen, (95, 55, 25), (sx + self.rect.w - 4, self.rect.y + 4), (sx + 4, self.rect.bottom - 4), 2)
            for cx, cy in [(sx + 5, self.rect.y + 6), (sx + self.rect.w - 6, self.rect.y + 6),
                           (sx + 5, self.rect.bottom - 7), (sx + self.rect.w - 6, self.rect.bottom - 7)]:
                pygame.draw.circle(screen, (40, 25, 15), (cx, cy), 2)
        else:
            for p in self.particles:
                psx = p[0] - camera_x
                if -20 < psx < SCREEN_WIDTH + 20 and p[1] < SCREEN_HEIGHT + 50:
                    pygame.draw.rect(screen, (130, 80, 40), (psx, int(p[1]), p[4], max(2, p[4] // 2)))


# --- METAL OBSTACLE ---
class MetalObstacle:
    def __init__(self, x, y, width=32, height=70):
        self.rect = pygame.Rect(x, y, width, height)
        self.is_broken = False
        self.is_dead = False
        self.health = 3
        self.particles = []

    def break_obstacle(self):
        if not self.is_broken:
            self.is_broken = True
            self.is_dead = True
            for _ in range(16):
                vx = random.uniform(-6.0, 6.0)
                vy = random.uniform(-7.0, -1.0)
                size = random.randint(3, 7)
                col = random.choice([(140, 145, 155), (90, 95, 105), (190, 195, 205), (255, 180, 50)])
                self.particles.append([float(self.rect.centerx), float(self.rect.centery), vx, vy, size, col])

    def update(self, player, game=None):
        if self.is_broken:
            for p in self.particles:
                p[0] += p[2]
                p[1] += p[3]
                p[3] += 0.45
            return

        if self.rect.colliderect(player.rect):
            if player.dash_timer > 0 or abs(player.vx) > 12:
                player.dash_timer = 0
                player.dizzy_timer = 60
                knock_dir = -1 if player.vx > 0 else (1 if player.vx < 0 else (-1 if player.direction == "R" else 1))
                player.vx = knock_dir * 9
                player.vy = -6
                if knock_dir < 0:
                    player.rect.right = self.rect.left
                else:
                    player.rect.left = self.rect.right
                if game is not None:
                    game.spawn_dash_hit(player.rect.centerx, player.rect.centery, is_metal=True)
            else:
                if player.rect.centerx < self.rect.centerx:
                    player.rect.right = self.rect.left
                    if player.vx > 0:
                        player.vx = 0
                else:
                    player.rect.left = self.rect.right
                    if player.vx < 0:
                        player.vx = 0

    def draw(self, screen, camera_x):
        if not self.is_broken:
            sx = self.rect.x - camera_x
            draw_rect = pygame.Rect(sx, self.rect.y, self.rect.w, self.rect.h)
            pygame.draw.rect(screen, (70, 75, 85), draw_rect)
            pygame.draw.rect(screen, (160, 170, 185), draw_rect, 2)
            if self.rect.w > 8 and self.rect.h > 8:
                pygame.draw.rect(screen, (50, 55, 65), (sx + 4, self.rect.y + 4, self.rect.w - 8, self.rect.h - 8))
            for rx, ry in [(sx + 5, self.rect.y + 5), (sx + self.rect.w - 6, self.rect.y + 5),
                           (sx + 5, self.rect.bottom - 6), (sx + self.rect.w - 6, self.rect.bottom - 6)]:
                pygame.draw.circle(screen, (190, 200, 215), (rx, ry), 2)
            pygame.draw.line(screen, (90, 95, 110), (sx + 4, self.rect.y + 4), (sx + self.rect.w - 4, self.rect.bottom - 4), 2)
            pygame.draw.line(screen, (90, 95, 110), (sx + self.rect.w - 4, self.rect.y + 4), (sx + 4, self.rect.bottom - 4), 2)
            if self.health < 3:
                pygame.draw.line(screen, (255, 140, 40), (sx + self.rect.w // 2, self.rect.y + 6),
                                 (sx + self.rect.w // 2 + 4, self.rect.y + self.rect.h // 2), 2)
                if self.health == 1:
                    pygame.draw.line(screen, (255, 180, 60), (sx + 4, self.rect.y + self.rect.h // 2),
                                     (sx + self.rect.w - 4, self.rect.bottom - 8), 2)
        else:
            for p in self.particles:
                psx = p[0] - camera_x
                if -20 < psx < SCREEN_WIDTH + 20 and p[1] < SCREEN_HEIGHT + 50:
                    pygame.draw.rect(screen, p[5], (psx, int(p[1]), p[4], p[4]))


# --- ROPE BLOCK ---
class RopeBlock:
    def __init__(self, x, y, width=80, height=24):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x):
        sx = self.rect.x - camera_x
        draw_rect = pygame.Rect(sx, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(screen, (245, 245, 252), draw_rect, border_radius=3)
        pygame.draw.rect(screen, (160, 165, 180), draw_rect, 2, border_radius=3)
        seg_w = 12
        for bx in range(sx + 4, sx + self.rect.w - 4, seg_w):
            pygame.draw.line(screen, (180, 185, 200), (bx, self.rect.y + 3), (bx + 6, self.rect.bottom - 4), 2)
            pygame.draw.line(screen, (255, 255, 255), (bx + 6, self.rect.y + 3), (bx + 12, self.rect.bottom - 4), 1)
        pygame.draw.rect(screen, (85, 90, 100), (sx, self.rect.y, 4, self.rect.h), border_radius=2)
        pygame.draw.rect(screen, (85, 90, 100), (sx + self.rect.w - 4, self.rect.y, 4, self.rect.h), border_radius=2)


# --- GRAPPLE PICKUP ---
class GrapplePickup:
    def __init__(self, x, y):
        self.start_x = float(x)
        self.start_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.rect = pygame.Rect(int(x) - 12, int(y) - 12, 24, 24)
        self.collected = False
        self.bob_timer = 0.0

    def update(self, player):
        if self.collected:
            return
        self.bob_timer += 0.08
        self.y = self.start_y + math.sin(self.bob_timer) * 4
        self.rect.centery = int(self.y)

        if self.rect.colliderect(player.rect):
            self.collected = True
            player.has_grapple = True

    def draw(self, screen, camera_x):
        if self.collected:
            return
        cx = int(self.x - camera_x)
        cy = int(self.y)
        glow_rad = int(14 + math.sin(self.bob_timer * 1.5) * 3)
        pygame.draw.circle(screen, (0, 180, 240), (cx, cy), glow_rad, 1)
        pygame.draw.circle(screen, (230, 235, 245), (cx, cy - 5), 4, 2)
        pygame.draw.line(screen, (200, 210, 220), (cx, cy - 3), (cx, cy + 7), 3)
        pygame.draw.arc(screen, (200, 210, 220), (cx - 8, cy + 1, 16, 10), 0, math.pi, 2)


# --- CIRCLE ENEMY ---
class CircleEnemy:
    def __init__(self, x, y, patrol_range=80, speed=1.0):
        self.x = float(x)
        self.y = float(y)
        self.start_x = float(x)
        self.patrol_range = patrol_range
        self.speed = speed
        self.radius = 15
        self.rect = pygame.Rect(int(x) - 15, int(y) - 15, 30, 30)
        self.is_dead = False
        self.health = 3
        self.hit_cooldown = 0

    def update(self):
        if self.is_dead:
            return
        if self.hit_cooldown > 0:
            self.hit_cooldown -= 1
        self.x += self.speed
        if abs(self.x - self.start_x) > self.patrol_range:
            self.speed *= -1
        self.rect.centerx = int(self.x)

    def draw(self, screen, camera_x):
        if not self.is_dead:
            cx, cy = int(self.x - camera_x), int(self.y)
            pygame.draw.circle(screen, (220, 45, 45), (cx, cy), self.radius)
            pygame.draw.circle(screen, (130, 15, 15), (cx, cy), self.radius, 2)
            eye_off_x = 4 if self.speed > 0 else -4
            pygame.draw.circle(screen, COLOR_WHITE, (cx + eye_off_x, cy - 2), 5)
            pygame.draw.circle(screen, (20, 20, 20), (cx + eye_off_x + (1 if self.speed > 0 else -1), cy - 2), 2)


# --- BULLET ---
class Bullet:
    def __init__(self, x, y, vx, vy, from_ally=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.from_ally = from_ally
        self.life = 180
        self.is_dead = False

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        if self.life <= 0:
            self.is_dead = True

    def draw(self, screen, camera_x):
        sx = int(self.x - camera_x)
        sy = int(self.y)
        if self.from_ally:
            pygame.draw.circle(screen, (255, 230, 80), (sx, sy), 5)
            pygame.draw.circle(screen, (255, 255, 255), (sx, sy), 2)
        else:
            pygame.draw.circle(screen, (255, 50, 50), (sx, sy), 5)
            pygame.draw.circle(screen, (255, 200, 200), (sx, sy), 2)


# --- SPIKE ---
class Spike:
    def __init__(self, x, y, width=24, height=24):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen, camera_x):
        rx, ry = self.rect.x - camera_x, self.rect.y
        points = [
            (rx, ry + self.rect.h),
            (rx + self.rect.w // 2, ry),
            (rx + self.rect.w, ry + self.rect.h)
        ]
        pygame.draw.polygon(screen, (255, 50, 50), points)
        pygame.draw.polygon(screen, (255, 255, 255), points, 1)


# --- TRI-ANGER ---
class TriAnger:
    def __init__(self, x, y):
        self.start_x = float(x)
        self.start_y = float(y)
        self.x = float(x)
        self.y = float(y)
        self.cage_rect = pygame.Rect(int(x) - 18, int(y) - 18, 36, 36)
        self.rect = pygame.Rect(int(x) - 11, int(y) - 11, 22, 22)
        self.is_caged = True
        self.shooting_enabled = True
        self.reload_timer = 0
        self.burst_shots_left = 0
        self.burst_timer = 0
        self.sight_range = 450
        self.target = None
        self.bob_timer = 0.0
        self.cage_particles = []

    def break_cage(self):
        if self.is_caged:
            self.is_caged = False
            for _ in range(14):
                vx = random.uniform(-5.0, 5.0)
                vy = random.uniform(-6.0, -1.0)
                self.cage_particles.append([self.x, self.y, vx, vy, random.randint(3, 6)])

    def toggle_shooting(self):
        self.shooting_enabled = not self.shooting_enabled
        if not self.shooting_enabled:
            self.target = None

    def update(self, player, enemies, bullets):
        for p in self.cage_particles:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.4
        self.cage_particles = [p for p in self.cage_particles if p[1] < SCREEN_HEIGHT + 50]

        if self.is_caged:
            if self.cage_rect.colliderect(player.rect):
                if player.dash_timer > 0 or abs(player.vx) > 12:
                    self.break_cage()
                else:
                    if player.rect.centerx < self.cage_rect.centerx:
                        player.rect.right = self.cage_rect.left
                        if player.vx > 0:
                            player.vx = 0
                    else:
                        player.rect.left = self.cage_rect.right
                        if player.vx < 0:
                            player.vx = 0
            return

        self.bob_timer += 0.08
        offset_x = -26 if player.direction == "R" else 26
        target_x = player.rect.centerx + offset_x
        target_y = player.rect.top - 18 + math.sin(self.bob_timer) * 4

        self.x += (target_x - self.x) * 0.16
        self.y += (target_y - self.y) * 0.16
        self.rect.center = (int(self.x), int(self.y))

        if not self.shooting_enabled:
            self.target = None
            return

        if self.reload_timer > 0:
            self.reload_timer -= 1

        valid_targets = [e for e in enemies if not e.is_dead and abs(e.rect.centery - self.y) < 180 and abs(e.rect.centerx - self.x) <= self.sight_range]
        if valid_targets:
            valid_targets.sort(key=lambda e: abs(e.rect.centerx - self.x))
            self.target = valid_targets[0]

            if self.reload_timer <= 0 and self.burst_shots_left == 0:
                self.burst_shots_left = 3
                self.burst_timer = 0
        else:
            self.target = None

        if self.burst_shots_left > 0:
            if not self.target or self.target.is_dead:
                if valid_targets:
                    self.target = valid_targets[0]
                else:
                    self.target = None
            if self.target and not self.target.is_dead:
                if self.burst_timer <= 0:
                    dx = self.target.rect.centerx - self.x
                    dy = self.target.rect.centery - self.y
                    dist = math.hypot(dx, dy)
                    if dist > 0:
                        speed = 9.5
                        bullets.append(Bullet(self.x, self.y, (dx / dist) * speed, (dy / dist) * speed, from_ally=True))
                    self.burst_shots_left -= 1
                    self.burst_timer = 20
                    if self.burst_shots_left == 0:
                        self.reload_timer = 300
                else:
                    self.burst_timer -= 1

    def draw_target_reticle(self, screen, camera_x, target):
        tx = int(target.rect.centerx - camera_x)
        ty = int(target.rect.centery)
        r = getattr(target, 'radius', 16) + 5
        pygame.draw.circle(screen, (255, 215, 0), (tx, ty), r, 2)
        b = 6
        pygame.draw.line(screen, (255, 255, 100), (tx - r - b, ty - r), (tx - r, ty - r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx - r, ty - r - b), (tx - r, ty - r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx + r, ty - r), (tx + r + b, ty - r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx + r, ty - r - b), (tx + r, ty - r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx - r - b, ty + r), (tx - r, ty + r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx - r, ty + r), (tx - r, ty + r + b), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx + r, ty + r), (tx + r + b, ty + r), 2)
        pygame.draw.line(screen, (255, 255, 100), (tx + r, ty + r), (tx + r, ty + r + b), 2)

    def draw(self, screen, camera_x):
        for p in self.cage_particles:
            psx = int(p[0] - camera_x)
            psy = int(p[1])
            pygame.draw.rect(screen, (130, 130, 140), (psx, psy, p[4], p[4]))

        cx, cy = int(self.x - camera_x), int(self.y)

        if self.target and not self.target.is_dead and self.shooting_enabled and not self.is_caged:
            self.draw_target_reticle(screen, camera_x, self.target)

        points = [(cx, cy - 11), (cx - 11, cy + 10), (cx + 11, cy + 10)]
        if self.is_caged:
            body_color = (160, 120, 60)
        elif not self.shooting_enabled:
            body_color = (200, 180, 70)
        else:
            body_color = (255, 170, 30)

        pygame.draw.polygon(screen, body_color, points)
        pygame.draw.polygon(screen, (190, 75, 10), points, 2)

        eye_y = cy + 1
        pygame.draw.circle(screen, (255, 255, 255), (cx, eye_y), 4)
        pupil_x = cx
        if self.target:
            pupil_x = cx + (2 if self.target.rect.centerx > self.x else -2)
        elif not self.is_caged:
            pupil_x = cx + (1 if self.x < cx else -1)
        pygame.draw.circle(screen, (20, 20, 20), (pupil_x, eye_y), 2)

        if self.shooting_enabled and not self.is_caged:
            pygame.draw.line(screen, (40, 20, 0), (cx - 5, eye_y - 4), (cx + 5, eye_y - 2), 2)
        else:
            pygame.draw.line(screen, (40, 20, 0), (cx - 4, eye_y - 3), (cx + 4, eye_y - 3), 1)

        if self.is_caged:
            csx = self.cage_rect.x - camera_x
            csy = self.cage_rect.y
            cw = self.cage_rect.w
            ch = self.cage_rect.h
            pygame.draw.rect(screen, (80, 80, 90), (csx, csy, cw, ch), 2)
            for bx in (csx + 7, csx + 14, csx + 21, csx + 28):
                pygame.draw.line(screen, (120, 120, 130), (bx, csy + 2), (bx, csy + ch - 2), 2)
            pygame.draw.line(screen, (100, 100, 110), (csx + 2, csy + ch // 2), (csx + cw - 2, csy + ch // 2), 2)
            pygame.draw.circle(screen, (255, 215, 0), (csx + cw // 2, csy + ch - 6), 4)
            pygame.draw.rect(screen, (200, 160, 0), (csx + cw // 2 - 4, csy + ch - 6, 8, 7))


# --- ENEMY TURRET ---
class EnemyTurret:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.radius = 16
        self.rect = pygame.Rect(int(x) - 16, int(y) - 16, 32, 32)
        self.shoot_timer = 180
        self.is_dead = False
        self.health = 3
        self.angle = 0.0

    def update(self, player, bullets):
        if self.is_dead:
            return

        dx = player.rect.centerx - self.x
        dy = player.rect.centery - self.y
        dist = math.hypot(dx, dy)
        if dist > 500:
            return

        self.angle = math.atan2(dy, dx)

        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = 180
            speed = 8.5
            vx = math.cos(self.angle) * speed
            vy = math.sin(self.angle) * speed
            barrel_x = self.x + math.cos(self.angle) * 22
            barrel_y = self.y + math.sin(self.angle) * 22
            bullets.append(Bullet(barrel_x, barrel_y, vx, vy, from_ally=False))

    def draw(self, screen, camera_x):
        if self.is_dead:
            return

        cx, cy = int(self.x - camera_x), int(self.y)
        barrel_len = 20
        barrel_w = 7
        bx_end = cx + int(math.cos(self.angle) * barrel_len)
        by_end = cy + int(math.sin(self.angle) * barrel_len)
        pygame.draw.line(screen, (50, 50, 60), (cx, cy), (bx_end, by_end), barrel_w)
        pygame.draw.line(screen, (100, 100, 110), (cx, cy), (bx_end, by_end), 2)
        pygame.draw.circle(screen, (70, 70, 80), (cx, cy), self.radius)
        pygame.draw.circle(screen, (120, 120, 130), (cx, cy), self.radius, 2)
        pygame.draw.circle(screen, (220, 40, 40), (cx, cy), 6)
        pygame.draw.circle(screen, (255, 120, 120), (cx, cy), 2)


# --- GOAL ---
class Goal:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 40, 70)

    def draw(self, screen, camera_x):
        screen_x = self.rect.x - camera_x
        draw_rect = (screen_x, self.rect.y, self.rect.w, self.rect.h)
        pygame.draw.rect(screen, COLOR_GREEN, draw_rect)
        pygame.draw.rect(screen, COLOR_WHITE, draw_rect, 2)
        pygame.draw.rect(screen, COLOR_PURPLE, (screen_x + 10, self.rect.y + 10, 20, 50))


# --- GAME ---
class Game:
    def __init__(self, screen=None):
        self.start_ticks = 0
        self.final_elapsed_time = 0.0
        self.best_time = load_best_time()
        self.is_new_best = False
        self.return_to_menu = False
        
        if not pygame.get_init():
            pygame.init()
        pygame.display.set_caption("Squerre Escape")
        if screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
            self.is_fullscreen = True
        else:
            self.screen = screen
            self.is_fullscreen = (self.screen.get_flags() & pygame.FULLSCREEN) != 0

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 14)
        self.font_big = pygame.font.SysFont("arial", 32, bold=True)
        self.running = True
        self.god_mode = False
        self.reset()
        from level_editor import LevelEditor
        self.editor = LevelEditor(self)

    def toggle_fullscreen(self):
        self.is_fullscreen = not self.is_fullscreen
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        if hasattr(self, 'editor') and self.editor:
            self.editor.screen = self.screen

    def reset(self):
        self.state = 'PLAYING'
        self.final_elapsed_time = 0.0
        self.is_new_best = False
        self.best_time = load_best_time()
        self.start_ticks = 0
        self.start_x = 50
        self.camera_x = 0
        self.player = Player(self.start_x, 352)
        self.player.is_grounded = True
        self.player.god_mode = getattr(self, 'god_mode', False)
        self.portal = Goal(7470, 240)
        self.watcher = GiantWatcher(x=400, y=140, radius=130)

        self.is_chained = True
        self.break_grace = 0
        self.pole_rect = pygame.Rect(20, 310, 14, 70)
        self.chain_max_len = 90

        level_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_level.json")
        if os.path.exists(level_file):
            try:
                with open(level_file, "r") as f:
                    data = json.load(f)
                self.platforms = [Platform(p[0], p[1], p[2], p[3]) for p in data.get("platforms", [])]
                self.breakable_woods = [BreakableWood(w[0], w[1], w[2], w[3]) for w in data.get("breakable_woods", [])]
                self.metal_obstacles = [MetalObstacle(m[0], m[1], m[2], m[3]) for m in data.get("metal_obstacles", [])]
                self.rope_blocks = [RopeBlock(r[0], r[1], r[2], r[3]) for r in data.get("rope_blocks", [])]
                self.grapple_pickups = [GrapplePickup(g[0], g[1]) for g in data.get("grapple_pickups", [])]
                self.enemies = [CircleEnemy(e[0], e[1], patrol_range=e[2], speed=e[3]) for e in data.get("enemies", [])]
                self.spikes = [Spike(s[0], s[1], s[2], s[3]) for s in data.get("spikes", [])]
                self.allies = [TriAnger(a[0], a[1]) for a in data.get("allies", [])]
                self.turrets = [EnemyTurret(t[0], t[1]) for t in data.get("turrets", [])]
                if "goal" in data and len(data["goal"]) >= 2:
                    self.portal = Goal(data["goal"][0], data["goal"][1])
                if "spawn" in data and len(data["spawn"]) >= 3:
                    self.start_x = data["spawn"][0]
                    self.pole_rect = pygame.Rect(data["spawn"][1], data["spawn"][2], 14, 70)
                    self.player.rect.x = self.start_x
            except Exception:
                self._load_fallback_level()
        else:
            self._load_fallback_level()

        self.hanging_ropes = []
        self.bullets = []
        self.effects = []

    def _load_fallback_level(self):
        self.platforms = [
            Platform(0, 380, 500, 70),
            Platform(625, 380, 500, 70),
            Platform(1200, 360, 250, 50),
            Platform(1600, 340, 90, 100),
            Platform(1900, 330, 90, 100),
            Platform(2205, 300, 400, 300),
            Platform(2200, 0, 20, 200),
            Platform(5000, 380, 250, 70),
        ]
        self.breakable_woods = [BreakableWood(1400, 290)]
        self.metal_obstacles = [MetalObstacle(2450, 230)]
        self.rope_blocks = [RopeBlock(1720, 220)]
        self.grapple_pickups = [GrapplePickup(1500, 310)]
        self.enemies = [CircleEnemy(750, 365, patrol_range=100)]
        self.spikes = [Spike(620, 356)]
        self.allies = [TriAnger(1000, 300)]
        self.turrets = [EnemyTurret(3160, 180)]

    def spawn_combat_effect(self, x, y, eff_type, color, count=8):
        for _ in range(count):
            if eff_type == 'spark':
                angle = random.uniform(0, 2 * math.pi)
                spd = random.uniform(3.0, 8.5)
                vx = math.cos(angle) * spd
                vy = math.sin(angle) * spd
                life = random.randint(12, 22)
                self.effects.append({'type': 'spark', 'x': float(x), 'y': float(y), 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'color': color})
            elif eff_type == 'debris':
                vx = random.uniform(-5.0, 5.0)
                vy = random.uniform(-6.0, -1.0)
                life = random.randint(18, 30)
                rad = random.randint(3, 6)
                self.effects.append({'type': 'debris', 'x': float(x), 'y': float(y), 'vx': vx, 'vy': vy, 'life': life, 'max_life': life, 'radius': rad, 'color': color})
            elif eff_type == 'ring':
                self.effects.append({'type': 'ring', 'x': float(x), 'y': float(y), 'radius': 4.0, 'max_radius': 26.0, 'life': 14, 'max_life': 14, 'color': color})

    def spawn_dash_hit(self, x, y, is_metal=False):
        c1 = (255, 180, 50) if is_metal else (0, 240, 255)
        c2 = (255, 230, 100) if is_metal else (255, 255, 255)
        self.spawn_combat_effect(x, y, 'spark', c1, count=12)
        self.spawn_combat_effect(x, y, 'ring', c2, count=1)
        self.spawn_combat_effect(x, y, 'debris', (180, 190, 205) if is_metal else (0, 180, 255), count=6)

    def spawn_enemy_death(self, x, y):
        self.spawn_combat_effect(x, y, 'spark', (255, 80, 80), count=14)
        self.spawn_combat_effect(x, y, 'debris', (200, 30, 30), count=10)
        self.spawn_combat_effect(x, y, 'ring', (255, 160, 160), count=1)

    def spawn_turret_death(self, x, y):
        self.spawn_combat_effect(x, y, 'spark', (255, 200, 50), count=16)
        self.spawn_combat_effect(x, y, 'debris', (80, 85, 95), count=12)
        self.spawn_combat_effect(x, y, 'ring', (255, 220, 100), count=2)

    def run(self):
        while self.running:
            self.clock.tick(60)
            events = pygame.event.get()
            
            self.handle_events(events)
            if self.editor.active:
                self.editor.update()
                self.editor.draw()
            else:
                self.update()
                self.draw()
            
            pygame.display.flip()

        if not getattr(self, 'return_to_menu', False):
            pygame.quit()
            sys.exit()
        return self.return_to_menu

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and not self.editor.active):
                self.running = False
                self.return_to_menu = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_b:
                    self.editor.toggle()
                elif self.editor.active:
                    self.editor.handle_event(event)
                elif self.state in ('WIN', 'GAME_OVER') and event.key == pygame.K_m:
                    self.return_to_menu = True
                    self.running = False
                elif self.state in ('WIN', 'GAME_OVER') and event.key in (pygame.K_SPACE, pygame.K_r):
                    self.reset()
                elif event.key == pygame.K_g:
                    self.god_mode = not self.god_mode
                    self.player.god_mode = self.god_mode
                elif event.key == pygame.K_q:
                    for ally in self.allies:
                        ally.toggle_shooting()
                elif event.key == pygame.K_F11:
                    self.toggle_fullscreen()
            elif self.editor.active:
                self.editor.handle_event(event)
            elif not self.editor.active and self.state == 'PLAYING':
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.player.grapple_target is not None:
                        self.player.shoot_grapple(self.player.grapple_target.rect.centerx, self.player.grapple_target.rect.centery)
                    else:
                        mx, my = pygame.mouse.get_pos()
                        self.player.shoot_grapple(mx + self.camera_x, my)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.player.release_grapple(self)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
                    if self.player.dash_target is not None:
                        self.player.execute_dash_attack()

        if self.state == 'PLAYING' and not self.editor.active:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)

    def update(self):
        if self.state != 'PLAYING':
            return

        all_platforms = self.platforms + self.rope_blocks
        self.player.update(all_platforms)

        for pickup in self.grapple_pickups:
            pickup.update(self.player)

        mx, my = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()
        is_holding_rmb = mouse_pressed[2] if len(mouse_pressed) > 2 else False
        self.player.update_dash_targeting(self.enemies, self.turrets, mx + self.camera_x, my, is_holding_rmb)
        self.player.update_grapple_targeting(self.rope_blocks, self.turrets, self.enemies, mx + self.camera_x, my)

        self.player.update_grapple(self.rope_blocks, self.turrets, self.enemies, self)

        for rope in self.hanging_ropes:
            rope.update()

        for spike in self.spikes:
            if self.player.rect.colliderect(spike.rect):
                if not self.god_mode:
                    self.player.health = 0

        for wood in self.breakable_woods:
            wood.update(self.player)

        for metal in self.metal_obstacles:
            metal.update(self.player, self)

        for enemy in self.enemies:
            enemy.update()
            if not enemy.is_dead and self.player.rect.colliderect(enemy.rect):
                is_stomp = (self.player.prev_y + self.player.rect.h <= enemy.rect.centery + 4)
                is_dash = (self.player.dash_timer > 0 or abs(self.player.vx) > 10)
                if is_dash or is_stomp:
                    enemy.is_dead = True
                    self.spawn_enemy_death(enemy.rect.centerx, enemy.rect.centery)
                    if is_dash:
                        self.spawn_dash_hit(enemy.rect.centerx, enemy.rect.centery)
                        self.player.dash_cooldown = 0
                        self.player.can_dash = True
                    self.player.vy = -9
                else:
                    if not self.god_mode:
                        self.player.health -= 25
                        self.player.vy = -6

        for turret in self.turrets:
            turret.update(self.player, self.bullets)
            if not turret.is_dead and self.player.rect.colliderect(turret.rect):
                if self.player.dash_timer > 0 or abs(self.player.vx) > 10:
                    turret.is_dead = True
                    self.spawn_turret_death(turret.rect.centerx, turret.rect.centery)
                    self.spawn_dash_hit(turret.rect.centerx, turret.rect.centery)
                    self.player.dash_cooldown = 0
                    self.player.can_dash = True
                    self.player.vy = -7
                else:
                    if not self.god_mode:
                        self.player.health -= 15
                        self.player.vy = -6

        valid_targets = [e for e in self.enemies if not e.is_dead] + [t for t in self.turrets if not t.is_dead] + [m for m in self.metal_obstacles if not m.is_broken]
        for ally in self.allies:
            ally.update(self.player, valid_targets, self.bullets)

        for bullet in self.bullets:
            bullet.update()
            if not bullet.is_dead:
                for platform in self.platforms + self.rope_blocks:
                    if platform.rect.collidepoint(bullet.x, bullet.y):
                        bullet.is_dead = True
                        break

                if not bullet.is_dead and bullet.from_ally:
                    for enemy in self.enemies:
                        if not enemy.is_dead and enemy.rect.collidepoint(bullet.x, bullet.y):
                            bullet.is_dead = True
                            enemy.is_dead = True
                            self.spawn_enemy_death(enemy.rect.centerx, enemy.rect.centery)
                            break
                    if not bullet.is_dead:
                        for turret in self.turrets:
                            if not turret.is_dead and turret.rect.collidepoint(bullet.x, bullet.y):
                                bullet.is_dead = True
                                turret.health -= 1
                                if turret.health <= 0:
                                    turret.is_dead = True
                                    self.spawn_turret_death(turret.rect.centerx, turret.rect.centery)
                                else:
                                    self.spawn_combat_effect(turret.rect.centerx, turret.rect.centery, 'spark', (255, 200, 50), count=6)
                                break
                    if not bullet.is_dead:
                        for metal in self.metal_obstacles:
                            if not metal.is_broken and metal.rect.collidepoint(bullet.x, bullet.y):
                                bullet.is_dead = True
                                metal.health -= 1
                                if metal.health <= 0:
                                    metal.break_obstacle()
                                else:
                                    self.spawn_combat_effect(bullet.x, bullet.y, 'spark', (255, 180, 60), count=6)
                                break
                elif not bullet.is_dead and not bullet.from_ally:
                    for metal in self.metal_obstacles:
                        if not metal.is_broken and metal.rect.collidepoint(bullet.x, bullet.y):
                            bullet.is_dead = True
                            break
                    if not bullet.is_dead and self.player.rect.collidepoint(bullet.x, bullet.y):
                        bullet.is_dead = True
                        if not self.god_mode:
                            self.player.health -= 15
                            self.player.vy = -4

        self.bullets = [b for b in self.bullets if not b.is_dead]

        for eff in self.effects:
            eff['life'] -= 1
            if eff['type'] == 'spark':
                eff['x'] += eff['vx']
                eff['y'] += eff['vy']
                eff['vy'] += 0.2
            elif eff['type'] == 'debris':
                eff['x'] += eff['vx']
                eff['y'] += eff['vy']
                eff['vy'] += 0.35
            elif eff['type'] == 'ring':
                progress = 1.0 - (eff['life'] / float(eff['max_life']))
                eff['radius'] = 4.0 + (eff['max_radius'] - 4.0) * progress
        self.effects = [e for e in self.effects if e['life'] > 0]

        if self.is_chained:
            if self.player.dash_timer > 0:
                self.is_chained = False
                for _ in range(12):
                    self.effects.append({
                        'type': 'debris',
                        'x': float(self.pole_rect.centerx),
                        'y': float(self.pole_rect.centery),
                        'vx': random.uniform(-4.0, 4.0),
                        'vy': random.uniform(-5.0, -1.0),
                        'life': 24,
                        'max_life': 24,
                        'radius': random.randint(3, 6),
                        'color': (180, 180, 195)
                    })
                self.start_ticks = pygame.time.get_ticks()
                self.break_grace = 25
            else:
                max_x = self.pole_rect.centerx + self.chain_max_len
                if self.player.rect.centerx > max_x:
                    self.player.rect.centerx = max_x

        self.watcher.update(self.player, self.is_chained)

        if not self.god_mode:
            if self.player.rect.y > SCREEN_HEIGHT + 50 or self.player.health <= 0:
                self.state = 'GAME_OVER'

        if self.player.rect.colliderect(self.portal.rect):
            if self.state == 'PLAYING':
                self.final_elapsed_time = (pygame.time.get_ticks() - self.start_ticks) / 1000.0 if self.start_ticks > 0 else 0.0
                if self.best_time is None or self.final_elapsed_time < self.best_time:
                    self.best_time = self.final_elapsed_time
                    self.is_new_best = True
                    save_best_time(self.best_time)
            self.state = 'WIN'

        target_cam_x = self.player.rect.x - SCREEN_WIDTH // 3
        max_cam_x = self.portal.rect.x - SCREEN_WIDTH + 100
        self.camera_x = max(0, min(max_cam_x, target_cam_x))

        if self.player.rect.left < self.camera_x:
            self.player.rect.left = self.camera_x
            if self.player.vx < 0:
                self.player.vx = 0
        elif self.player.rect.right > self.camera_x + SCREEN_WIDTH:
            self.player.rect.right = self.camera_x + SCREEN_WIDTH
            if self.player.vx > 0:
                self.player.vx = 0

    def draw(self):
        self.screen.fill(COLOR_BLACK)
        cam_x = self.camera_x
        self.watcher.draw(self.screen, cam_x, self.player)

        for platform in self.platforms:
            platform.draw(self.screen, cam_x)

        for spike in self.spikes:
            spike.draw(self.screen, cam_x)

        for wood in self.breakable_woods:
            wood.draw(self.screen, cam_x)

        for metal in self.metal_obstacles:
            metal.draw(self.screen, cam_x)

        for rb in self.rope_blocks:
            rb.draw(self.screen, cam_x)

        for hr in self.hanging_ropes:
            hr.draw(self.screen, cam_x)

        for gp in self.grapple_pickups:
            gp.draw(self.screen, cam_x)

        for eff in self.effects:
            ex = int(eff['x'] - cam_x)
            ey = int(eff['y'])
            if -50 < ex < SCREEN_WIDTH + 50:
                if eff['type'] == 'spark':
                    ex2 = int(ex - eff['vx'] * 1.5)
                    ey2 = int(ey - eff['vy'] * 1.5)
                    pygame.draw.line(self.screen, eff['color'], (ex, ey), (ex2, ey2), 2)
                elif eff['type'] == 'debris':
                    pygame.draw.circle(self.screen, eff['color'], (ex, ey), max(1, int(eff['radius'])))
                elif eff['type'] == 'ring':
                    r = max(1, int(eff['radius']))
                    pygame.draw.circle(self.screen, eff['color'], (ex, ey), r, 2)

        for enemy in self.enemies:
            enemy.draw(self.screen, cam_x)

        for turret in self.turrets:
            turret.draw(self.screen, cam_x)

        for ally in self.allies:
            ally.draw(self.screen, cam_x)

        for bullet in self.bullets:
            bullet.draw(self.screen, cam_x)

        pole_sx = self.pole_rect.x - cam_x
        pygame.draw.rect(self.screen, (70, 70, 75), (pole_sx, self.pole_rect.y, self.pole_rect.w, self.pole_rect.h))
        pygame.draw.rect(self.screen, (150, 150, 160), (pole_sx, self.pole_rect.y, self.pole_rect.w, self.pole_rect.h), 2)
        anchor_x = pole_sx + self.pole_rect.w // 2
        anchor_y = self.pole_rect.y + 12
        pygame.draw.circle(self.screen, (190, 190, 200), (anchor_x, anchor_y), 7, 2)

        if self.is_chained:
            player_center_x = self.player.rect.centerx - cam_x
            player_center_y = self.player.rect.centery
            num_links = 6
            for i in range(num_links + 1):
                t = i / num_links
                lx = anchor_x + (player_center_x - anchor_x) * t
                ly = anchor_y + (player_center_y - anchor_y) * t
                dist = math.hypot(player_center_x - anchor_x, player_center_y - anchor_y)
                sag = max(0.0, (1.0 - (dist / self.chain_max_len))) * 12.0
                ly += sag * (4 * t * (1 - t))
                pygame.draw.circle(self.screen, (180, 180, 190), (int(lx), int(ly)), 4)
                pygame.draw.circle(self.screen, (40, 40, 45), (int(lx), int(ly)), 2)

        self.portal.draw(self.screen, cam_x)
        self.player.draw(self.screen, cam_x)
        self.draw_ui()

        if self.state == 'WIN':
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((10, 20, 15, 180))
            self.screen.blit(overlay, (0, 0))

            title = self.font_big.render("FREEDOM ACHIEVED!", True, COLOR_GREEN)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 65))

            time_str = f"TIME: {self.final_elapsed_time:.2f}s"
            time_surf = self.font.render(time_str, True, COLOR_WHITE)
            self.screen.blit(time_surf, (SCREEN_WIDTH // 2 - time_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 25))

            best_val = self.best_time if self.best_time is not None else self.final_elapsed_time
            best_str = f"BEST TIME: {best_val:.2f}s"
            best_surf = self.font.render(best_str, True, (255, 215, 0))
            self.screen.blit(best_surf, (SCREEN_WIDTH // 2 - best_surf.get_width() // 2, SCREEN_HEIGHT // 2 - 5))

            if self.is_new_best:
                rec_surf = self.font.render("* NEW RECORD! *", True, (255, 235, 80))
                self.screen.blit(rec_surf, (SCREEN_WIDTH // 2 - rec_surf.get_width() // 2, SCREEN_HEIGHT // 2 + 15))

            sub = self.font.render("[R] PLAY AGAIN      [M] MAIN MENU", True, (200, 210, 220))
            self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 40))

        elif self.state == 'GAME_OVER':
            msg_text = "CAUGHT MOVING! (PRESS R TO RETRY)" if self.player.killed_by_boss else "GAME OVER (PRESS R TO RETRY)"
            msg = self.font_big.render(msg_text, True, COLOR_RED)
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            sub = self.font.render("[M] MAIN MENU", True, (200, 210, 220))
            self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

    def draw_ui(self):
        pygame.draw.rect(self.screen, (60, 60, 60), (15, 15, 100, 10))
        pygame.draw.rect(self.screen, COLOR_GREEN, (15, 15, max(0, self.player.health), 10))
        hp_text = self.font.render(f"HP: {self.player.health}", True, COLOR_WHITE)
        self.screen.blit(hp_text, (15, 28))

        total_dist = self.portal.rect.x - self.start_x
        current_dist = self.player.rect.x - self.start_x
        progress = max(0.0, min(1.0, current_dist / total_dist))
        
        bar_w, bar_h = 400, 10
        bar_x = (SCREEN_WIDTH - bar_w) // 2
        bar_y = SCREEN_HEIGHT - 24
        
        pygame.draw.rect(self.screen, (50, 50, 50), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(self.screen, COLOR_BLUE, (bar_x, bar_y, int(bar_w * progress), bar_h))
        pygame.draw.rect(self.screen, COLOR_WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
        
        prog_text = self.font.render(f"ESCAPE PROGRESS: {int(progress * 100)}%", True, COLOR_WHITE)
        self.screen.blit(prog_text, (bar_x, bar_y - 18))

        if self.is_chained or self.start_ticks == 0:
            elapsed = 0.0
        elif self.state == 'PLAYING':
            elapsed = (pygame.time.get_ticks() - self.start_ticks) / 1000.0
        else:
            elapsed = self.final_elapsed_time

        time_text = self.font.render(f"TIME: {elapsed:.1f}s", True, COLOR_WHITE)
        self.screen.blit(time_text, (SCREEN_WIDTH - 110, 15))

        if self.is_chained:
            hint = self.font.render("CHAINED! DASH [SHIFT] TO BREAK FREE", True, (255, 230, 90))
            self.screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2, 60))

        if self.allies and any(not a.is_caged for a in self.allies):
            is_on = any(a.shooting_enabled for a in self.allies if not a.is_caged)
            targeting_status = "TARGETING: ON [Q]" if is_on else "TARGETING: OFF [Q]"
            col = (255, 170, 30) if is_on else (160, 160, 170)
            ally_ui = self.font.render(f"TRI-ANGER: {targeting_status}", True, col)
            self.screen.blit(ally_ui, (15, 45))

        if self.player.has_grapple:
            grapple_ui = self.font.render("GRAPPLE: [HOLD L-CLICK]", True, (0, 220, 255))
            self.screen.blit(grapple_ui, (15, 62))

        if self.player.holding_dash_lock:
            col = (255, 90, 90) if self.player.dash_target else (200, 140, 140)
            status = "DASH ATTACK: [LOCKED - RELEASE OR SHIFT]" if self.player.dash_target else "DASH LOCK: [TARGETING...]"
            dash_ui = self.font.render(status, True, col)
            y_pos = 78 if self.player.has_grapple else 62
            self.screen.blit(dash_ui, (15, y_pos))


if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
