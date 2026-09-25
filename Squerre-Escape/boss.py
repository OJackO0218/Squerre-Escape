import pygame
import math
import random


class GiantWatcher:
    def __init__(self, x=400, y=140, radius=120):
        self.world_x = x
        self.world_y = y
        self.radius = radius

        self.state = 'WATCHING'
        self.timer = random.randint(180, 260)
        self.turn_progress = 0.0
        self.turn_duration = 75
        self.is_alert = False

        self.screen_on = False
        self.screen_anim_timer = 0
        self.screen_off_transition = 1.0

    def update(self, player, is_chained):
        if self.state == 'WATCHING':
            self.turn_progress = 0.0
            self.screen_on = False
            self.screen_off_transition = 1.0

            if not is_chained and not getattr(player, 'god_mode', False):
                moved_pos = (player.rect.x != player.prev_x) or (player.rect.y != player.prev_y)
                has_vel = abs(player.vx) > 0.4 or (not player.is_grounded and abs(player.vy) > 1.0)
                if moved_pos or has_vel:
                    self.is_alert = True
                    player.killed_by_boss = True
                    player.health = 0
                    return

            self.timer -= 1
            if self.timer <= 0:
                self.state = 'TURNING_AWAY'
                self.turn_progress = 0.0
                self.screen_on = True
                self.screen_off_transition = 0.0

        elif self.state == 'TURNING_AWAY':
            self.screen_on = True
            self.screen_off_transition = 0.0
            self.screen_anim_timer += 1
            self.turn_progress += 1.0 / self.turn_duration
            if self.turn_progress >= 1.0:
                self.turn_progress = 1.0
                self.state = 'BACK_TURNED'
                self.timer = random.randint(300, 600)

        elif self.state == 'BACK_TURNED':
            self.turn_progress = 1.0
            self.screen_anim_timer += 1
            self.timer -= 1

            if self.timer <= 70:
                self.screen_on = False
                if self.screen_off_transition < 1.0:
                    self.screen_off_transition = min(1.0, self.screen_off_transition + 0.08)
            else:
                self.screen_on = True
                self.screen_off_transition = 0.0

            if self.timer <= 0:
                self.state = 'TURNING_TO_US'
                self.turn_progress = 1.0

        elif self.state == 'TURNING_TO_US':
            self.screen_on = False
            self.screen_off_transition = 1.0
            self.turn_progress -= 1.0 / self.turn_duration
            if self.turn_progress <= 0.0:
                self.turn_progress = 0.0
                self.state = 'WATCHING'
                self.timer = random.randint(180, 260)

    def draw_monitor(self, screen, screen_x, screen_y):
        mon_w = 92
        mon_h = 62
        mon_x = screen_x + 135
        mon_y = screen_y - 55

        mount_x = mon_x + 40
        pygame.draw.line(screen, (55, 60, 70), (mount_x, 0), (mount_x, mon_y), 4)
        pygame.draw.line(screen, (85, 90, 105), (mount_x - 1, 0), (mount_x - 1, mon_y), 1)
        pygame.draw.circle(screen, (75, 80, 95), (mount_x, mon_y), 6)
        pygame.draw.circle(screen, (30, 32, 40), (mount_x, mon_y), 3)

        pygame.draw.line(screen, (60, 65, 75), (mount_x, mon_y), (mon_x + 10, mon_y + 10), 3)

        if self.screen_on and self.screen_off_transition < 0.8:
            glow_surf = pygame.Surface((mon_w + 50, mon_h + 50), pygame.SRCALPHA)
            glow_alpha = int(45 + math.sin(self.screen_anim_timer * 0.25) * 12)
            glow_color = (40, 180, 240, glow_alpha)
            pygame.draw.ellipse(glow_surf, glow_color, (0, 0, mon_w + 50, mon_h + 50))
            screen.blit(glow_surf, (mon_x - 25, mon_y - 25))

        chassis_rect = pygame.Rect(mon_x, mon_y, mon_w, mon_h)
        pygame.draw.rect(screen, (32, 34, 42), chassis_rect, border_radius=6)
        pygame.draw.rect(screen, (65, 70, 85), chassis_rect, 2, border_radius=6)

        panel_x = mon_x + mon_w - 18
        pygame.draw.rect(screen, (24, 26, 32), (panel_x, mon_y + 6, 12, mon_h - 12), border_radius=2)
        for vy in (mon_y + 11, mon_y + 16, mon_y + 21, mon_y + 26):
            pygame.draw.line(screen, (45, 48, 58), (panel_x + 2, vy), (panel_x + 10, vy), 1)

        led_y = mon_y + 36
        if self.screen_on and self.screen_off_transition < 0.5:
            pygame.draw.circle(screen, (50, 255, 80), (panel_x + 6, led_y), 3)
            pygame.draw.circle(screen, (180, 255, 190), (panel_x + 6, led_y), 1)
        else:
            pygame.draw.circle(screen, (220, 40, 40), (panel_x + 6, led_y), 2)

        knob_y = mon_y + 48
        pygame.draw.circle(screen, (50, 52, 62), (panel_x + 6, knob_y), 4)
        pygame.draw.circle(screen, (80, 85, 98), (panel_x + 6, knob_y), 1)

        scr_x = mon_x + 6
        scr_y = mon_y + 6
        scr_w = mon_w - 28
        scr_h = mon_h - 12
        screen_inner = pygame.Rect(scr_x, scr_y, scr_w, scr_h)

        if self.screen_off_transition >= 1.0:
            pygame.draw.rect(screen, (14, 16, 22), screen_inner, border_radius=3)
            pygame.draw.line(screen, (28, 32, 44), (scr_x + 4, scr_y + 4), (scr_x + scr_w - 12, scr_y + scr_h - 6), 2)
        elif self.screen_off_transition > 0.0:
            pygame.draw.rect(screen, (10, 12, 16), screen_inner, border_radius=3)
            t = self.screen_off_transition
            if t < 0.65:
                beam_h = max(2, int(scr_h * ((1.0 - t / 0.65) ** 2)))
                beam_y = scr_y + (scr_h - beam_h) // 2
                beam_w = scr_w - 6
                beam_x = scr_x + 3
                pygame.draw.rect(screen, (220, 245, 255), (beam_x, beam_y, beam_w, beam_h), border_radius=1)
                pygame.draw.line(screen, (255, 255, 255), (beam_x, scr_y + scr_h // 2), (beam_x + beam_w, scr_y + scr_h // 2), 2)
            else:
                dot_t = (t - 0.65) / 0.35
                dot_rad = max(1, int(4 * (1.0 - dot_t)))
                pygame.draw.circle(screen, (255, 255, 255), (scr_x + scr_w // 2, scr_y + scr_h // 2), dot_rad)
        else:
            pygame.draw.rect(screen, (15, 24, 52), screen_inner, border_radius=3)

            sun_phase = self.screen_anim_timer * 0.05
            sun_y = scr_y + 14 + int(math.sin(sun_phase) * 2)
            pygame.draw.circle(screen, (255, 220, 80), (scr_x + scr_w - 14, sun_y), 5)

            poly_pts = [
                (scr_x, scr_y + scr_h - 10),
                (scr_x + 12, scr_y + 24),
                (scr_x + 26, scr_y + 30),
                (scr_x + 40, scr_y + 20),
                (scr_x + scr_w, scr_y + 28),
                (scr_x + scr_w, scr_y + scr_h - 10),
            ]
            pygame.draw.polygon(screen, (28, 45, 85), poly_pts)

            pygame.draw.rect(screen, (20, 80, 55), (scr_x, scr_y + scr_h - 10, scr_w, 10))
            pygame.draw.line(screen, (40, 160, 95), (scr_x, scr_y + scr_h - 10), (scr_x + scr_w, scr_y + scr_h - 10), 1)

            run_step = (self.screen_anim_timer * 1.8) % (scr_w - 14)
            char_x = int(scr_x + 4 + run_step)
            jump_cycle = (self.screen_anim_timer * 0.12) % (2 * math.pi)
            char_bounce = -abs(math.sin(jump_cycle)) * 8 if math.sin(jump_cycle) > 0.3 else 0
            char_y = int(scr_y + scr_h - 17 + char_bounce)

            pygame.draw.rect(screen, (255, 80, 160), (char_x, char_y, 7, 7))
            pygame.draw.rect(screen, (255, 255, 255), (char_x + 4, char_y + 1, 2, 2))

            star_x = scr_x + 30
            star_y = scr_y + 18 + int(math.sin(self.screen_anim_timer * 0.15) * 3)
            pygame.draw.circle(screen, (255, 240, 60), (star_x, star_y), 2)

            if (self.screen_anim_timer // 24) % 2 == 0:
                pygame.draw.polygon(screen, (80, 255, 120), [(scr_x + 4, scr_y + 4), (scr_x + 4, scr_y + 9), (scr_x + 8, scr_y + 6)])
                pygame.draw.circle(screen, (80, 255, 120), (scr_x + 12, scr_y + 6), 1)

            for sly in range(scr_y + 2, scr_y + scr_h, 4):
                pygame.draw.line(screen, (10, 15, 30), (scr_x, sly), (scr_x + scr_w, sly), 1)

            pygame.draw.line(screen, (120, 180, 255), (scr_x + 4, scr_y + 2), (scr_x + 24, scr_y + 2), 1)
            pygame.draw.line(screen, (120, 180, 255), (scr_x + 2, scr_y + 4), (scr_x + 2, scr_y + 16), 1)

        pygame.draw.rect(screen, (18, 20, 26), screen_inner, 1, border_radius=3)

    def draw(self, screen, camera_x, player):
        screen_x = int(self.world_x - (camera_x * 0.10))
        screen_y = self.world_y

        self.draw_monitor(screen, screen_x, screen_y)

        if self.is_alert:
            pygame.draw.circle(screen, (180, 20, 20), (screen_x, screen_y), self.radius + 6, 4)
            pygame.draw.circle(screen, (70, 10, 20), (screen_x, screen_y), self.radius)
            pygame.draw.circle(screen, (255, 40, 40), (screen_x, screen_y), self.radius, 5)
        else:
            pygame.draw.circle(screen, (45, 10, 25), (screen_x, screen_y), self.radius)
            pygame.draw.circle(screen, (120, 20, 40), (screen_x, screen_y), self.radius, 4)

        phi = self.turn_progress * math.pi
        r_orbit = 95
        eye_y = screen_y - 15

        phi_back = phi - math.pi
        z_back = math.cos(phi_back)
        if z_back > 0.05:
            if self.screen_on and self.screen_off_transition < 0.6:
                rim_arc_rect = (screen_x - self.radius, screen_y - self.radius, self.radius * 2, self.radius * 2)
                pygame.draw.arc(screen, (60, 160, 230), rim_arc_rect, -math.pi * 0.25, math.pi * 0.35, 3)

            back_x = screen_x + int(r_orbit * math.sin(phi_back) * 0.6)
            for offset_y in (-35, -15, 5, 25, 45):
                plate_w = max(4, int((36 - abs(offset_y) * 0.4) * z_back))
                plate_rect = pygame.Rect(back_x - plate_w // 2, screen_y + offset_y - 6, plate_w, 12)
                pygame.draw.rect(screen, (30, 8, 18), plate_rect)
                pygame.draw.rect(screen, (85, 20, 40), plate_rect, 2)

        eyes = [
            {'side': 'L', 'lambda': -0.46},
            {'side': 'R', 'lambda': 0.46}
        ]

        player_screen_x = player.rect.centerx - camera_x
        player_screen_y = player.rect.centery

        for eye in eyes:
            theta = eye['lambda'] + phi
            z = math.cos(theta)

            if z > 0.02:
                ex = screen_x + int(r_orbit * math.sin(theta))
                ey = eye_y

                rx = max(2, int(30 * z))
                ry = 30

                sclera_col = (255, 30, 30) if self.is_alert else (240, 220, 160)
                pygame.draw.ellipse(screen, sclera_col, (ex - rx, ey - ry, rx * 2, ry * 2))
                pygame.draw.ellipse(screen, (10, 0, 0), (ex - rx, ey - ry, rx * 2, ry * 2), 2)

                if self.is_alert:
                    p_rx = max(1, int(18 * z))
                    pygame.draw.ellipse(screen, (255, 220, 0), (ex - p_rx, ey - 18, p_rx * 2, 36))
                    core_rx = max(1, int(8 * z))
                    pygame.draw.ellipse(screen, (0, 0, 0), (ex - core_rx, ey - 10, core_rx * 2, 20))
                else:
                    dx = player_screen_x - ex
                    dy = player_screen_y - ey
                    angle = math.atan2(dy, dx)
                    p_offset_x = int(math.cos(angle) * 14 * z)
                    p_offset_y = int(math.sin(angle) * 14)
                    px = ex + p_offset_x
                    py = ey + p_offset_y
                    prx = max(1, int(12 * z))
                    pry = 12

                    pygame.draw.ellipse(screen, (220, 20, 20), (px - prx, py - pry, prx * 2, pry * 2))
                    core_x = max(1, int(6 * z))
                    pygame.draw.ellipse(screen, (0, 0, 0), (px - core_x, py - 6, core_x * 2, 12))

                b1_ang = theta - 0.28
                b2_ang = theta + 0.28
                if eye['side'] == 'L':
                    y1, y2 = ey - 35, ey - 15
                else:
                    y1, y2 = ey - 15, ey - 35

                z1 = math.cos(b1_ang)
                z2 = math.cos(b2_ang)
                if z1 > 0.02 and z2 > 0.02:
                    x1 = screen_x + int(r_orbit * math.sin(b1_ang))
                    x2 = screen_x + int(r_orbit * math.sin(b2_ang))
                    thick = max(2, int(10 * min(z1, z2)))
                    pygame.draw.line(screen, (20, 5, 10), (x1, y1), (x2, y2), thick)

