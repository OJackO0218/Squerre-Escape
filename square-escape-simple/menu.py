import pygame
import sys
import os
import json
import math

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 450

COLOR_BLACK = (20, 20, 20)
COLOR_WHITE = (255, 255, 255)
COLOR_BLUE  = (0, 180, 255)
COLOR_GOLD  = (255, 215, 0)

BEST_TIME_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'best_time.json')

def load_best_time():
    if os.path.exists(BEST_TIME_FILE):
        try:
            with open(BEST_TIME_FILE, 'r') as f:
                data = json.load(f)
                return data.get('best_time', None)
        except Exception:
            return None
    return None

def save_best_time(time_sec):
    try:
        with open(BEST_TIME_FILE, 'w') as f:
            json.dump({'best_time': round(float(time_sec), 2)}, f)
    except Exception:
        pass

class MainMenu:
    def __init__(self, screen=None):
        if not pygame.get_init():
            pygame.init()
        
        if screen is None:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN | pygame.SCALED)
            pygame.display.set_caption("Squerre Escape")
        else:
            self.screen = screen

        self.clock = pygame.time.Clock()
        self.font_title = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_button = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_info = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 14)

        self.running = True
        self.start_game_requested = False
        self.anim_timer = 0.0

        # Clickable button rect
        self.btn_w, self.btn_h = 240, 50
        self.btn_x = (SCREEN_WIDTH - self.btn_w) // 2
        self.btn_y = 265
        self.btn_rect = pygame.Rect(self.btn_x, self.btn_y, self.btn_w, self.btn_h)

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.start_game_requested = True
                self.running = False
            elif event.key == pygame.K_F11:
                pygame.display.toggle_fullscreen()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.start_game_requested = True
            self.running = False

    def update(self):
        self.anim_timer += 0.05

    def draw(self):
        self.screen.fill((16, 18, 24))

        # Background grid pattern
        for gx in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (24, 28, 38), (gx, 0), (gx, SCREEN_HEIGHT), 1)
        for gy in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.line(self.screen, (24, 28, 38), (0, gy), (SCREEN_WIDTH, gy), 1)

        # Title shadow & text
        title_text = "SQUERRE ESCAPE"
        shadow = self.font_title.render(title_text, True, (10, 30, 45))
        self.screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 53))
        title = self.font_title.render(title_text, True, COLOR_BLUE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # Animated little hero cube
        cube_cx = SCREEN_WIDTH // 2
        cube_cy = 175 + int(math.sin(self.anim_timer * 2.0) * 8)
        cube_size = 36
        cube_rect = pygame.Rect(cube_cx - cube_size // 2, cube_cy - cube_size // 2, cube_size, cube_size)

        # Cube shadow
        shadow_w = int(36 + math.sin(self.anim_timer * 2.0) * 6)
        pygame.draw.ellipse(self.screen, (10, 12, 16), (cube_cx - shadow_w // 2, 206, shadow_w, 8))

        # Cube body & eyes
        pygame.draw.rect(self.screen, COLOR_BLUE, cube_rect, border_radius=4)
        pygame.draw.rect(self.screen, (180, 240, 255), cube_rect, 2, border_radius=4)

        # Eye tracking towards mouse
        mx, my = pygame.mouse.get_pos()
        eye_dir = 1 if mx >= cube_cx else -1
        pygame.draw.rect(self.screen, COLOR_BLACK, (cube_rect.x + (18 if eye_dir > 0 else 6), cube_rect.y + 8, 5, 10))
        pygame.draw.rect(self.screen, COLOR_BLACK, (cube_rect.x + (26 if eye_dir > 0 else 14), cube_rect.y + 8, 5, 10))

        # Best Time display
        best_t = load_best_time()
        if best_t is not None:
            best_label = f"BEST TIME: {best_t:.2f}s"
            best_surf = self.font_info.render(best_label, True, COLOR_GOLD)
        else:
            best_surf = self.font_info.render("BEST TIME: --", True, (140, 140, 150))
        self.screen.blit(best_surf, (SCREEN_WIDTH // 2 - best_surf.get_width() // 2, 224))

        # Click to Start Button
        mouse_over = self.btn_rect.collidepoint(mx, my)
        pulse = math.sin(self.anim_timer * 3.5) * 20
        btn_col = (0, min(255, int(190 + pulse)), min(255, int(255 + pulse))) if mouse_over else (30, 140, 210)
        pygame.draw.rect(self.screen, btn_col, self.btn_rect, border_radius=8)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.btn_rect, 2, border_radius=8)

        start_lbl = self.font_button.render("CLICK TO START", True, COLOR_WHITE)
        self.screen.blit(start_lbl, (self.btn_x + (self.btn_w - start_lbl.get_width()) // 2,
                                     self.btn_y + (self.btn_h - start_lbl.get_height()) // 2))

        # Controls reference at bottom
        ctrls = "[A / D] MOVE   •   [SPACE] JUMP   •   [SHIFT] DASH   •   [L-CLICK] GRAPPLE   •   [R-CLICK] LOCK-ON"
        ctrl_surf = self.font_small.render(ctrls, True, (130, 135, 150))
        self.screen.blit(ctrl_surf, (SCREEN_WIDTH // 2 - ctrl_surf.get_width() // 2, SCREEN_HEIGHT - 35))

    def run(self):
        while self.running:
            events = pygame.event.get()
            for event in events:
                self.handle_event(event)
            self.update()
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)

        if self.start_game_requested:
            import main
            game = main.Game(screen=self.screen)
            return_to_menu = game.run()
            if return_to_menu:
                self.running = True
                self.start_game_requested = False
                self.run()

if __name__ == "__main__":
    menu = MainMenu()
    menu.run()
