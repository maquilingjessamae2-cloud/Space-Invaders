import pygame
import random
import math
from entities.player import Player
from entities.button import MobileButtons
from entities.enemy import Enemy
from entities.bullet import Bullet
from entities.powerup import PowerUp
from managers.audio_manager import AudioManager
from managers.db_manager import DBManager
from managers.settings_manager import SettingsManager

# --- Profile options ---
CONTROL_SCHEMES = ["arrows", "wasd"]
DIFFICULTIES    = ["easy", "normal", "hard"]
DIFFICULTY_LABELS = {"easy": "Easy", "normal": "Normal", "hard": "Hard"}

# Difficulty multipliers (enemy spawn count modifier)
DIFFICULTY_SPAWN = {"easy": 3, "normal": 5, "hard": 8}

# Singularity palette: event-horizon black, ion violet, and plasma cyan.
DARK_BG    = (5, 7, 18)
ACCENT     = (177, 91, 255)
ACCENT_2   = (72, 224, 255)
WHITE      = (235, 242, 255)
GRAY       = (139, 154, 182)
DARK_BTN   = (13, 18, 38)
SEL_BTN    = (91, 48, 155)
SEL_BTN_H  = (152, 83, 226)
RED_ERR    = (255, 112, 147)
GOLD       = (255, 207, 92)
PANEL_BG   = (10, 14, 31)
PANEL_BOR  = (70, 82, 130)
FIELD_BG   = (7, 11, 26)
ACCENT_DIM = (48, 36, 92)
BACKGROUND_CACHE = {}


def draw_panel(screen, rect, fill_color=PANEL_BG, border_color=PANEL_BOR, radius=18):
    """Draw a glassy, neon-edged Singularity panel."""
    shadow = pygame.Rect(rect.x + 7, rect.y + 9, rect.width, rect.height)
    shadow_surface = pygame.Surface((shadow.width, shadow.height), pygame.SRCALPHA)
    pygame.draw.rect(shadow_surface, (0, 0, 0, 150), shadow_surface.get_rect(), border_radius=radius)
    screen.blit(shadow_surface, shadow.topleft)

    pygame.draw.rect(screen, fill_color, rect, border_radius=radius)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=radius)

    top_line = pygame.Rect(rect.x + 16, rect.y + 14, rect.width - 32, 2)
    pygame.draw.rect(screen, ACCENT_2, top_line, border_radius=2)

    inner = pygame.Rect(rect.x + 10, rect.y + 10, rect.width - 20, rect.height - 20)
    inner_surface = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
    pygame.draw.rect(inner_surface, (96, 133, 255, 12), inner_surface.get_rect(), border_radius=radius - 6)
    screen.blit(inner_surface, inner.topleft)


def draw_option_row(screen, font, label, options, selected, y, x_start, item_w=120, item_h=40):
    """Draw a labeled row of selectable option buttons. Returns list of (rect, option) tuples."""
    label_surf = font.render(label, True, WHITE)
    screen.blit(label_surf, (x_start, y + 8))

    rects = []
    btn_x = x_start + 180
    for opt in options:
        rect = pygame.Rect(btn_x, y, item_w, item_h)
        is_selected = opt == selected
        color = SEL_BTN if is_selected else DARK_BTN
        base_border = ACCENT_2 if is_selected else (70, 82, 130)
        pygame.draw.rect(screen, color, rect, border_radius=10)
        pygame.draw.rect(screen, base_border, rect, 2, border_radius=10)

        disp = opt.upper() if label == "Controls:" else DIFFICULTY_LABELS.get(opt, opt.capitalize())
        txt = font.render(disp, True, WHITE)
        screen.blit(txt, (btn_x + (item_w - txt.get_width()) // 2,
                           y + (item_h - txt.get_height()) // 2))

        rects.append((rect, opt))
        btn_x += item_w + 10
    return rects


def draw_glow_rect(screen, rect, color, radius=10, layers=3):
    """Draw a soft rectangular glow around a rect."""
    pulse = 0.78 + 0.22 * math.sin(pygame.time.get_ticks() * 0.004)
    for i in range(layers, 0, -1):
        expand = i * 3
        alpha = int((42 // i) * pulse)
        glow_rect = rect.inflate(expand * 2, expand * 2)
        s = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius + expand)
        screen.blit(s, glow_rect.topleft)


def draw_text_field(screen, font, rect, text, placeholder, focused, masked=False, label=None, label_font=None):
    """Draw a styled input field with optional floating label above it."""
    border_color = ACCENT_2 if focused else (54, 68, 108)
    bg_color = (12, 19, 42) if focused else FIELD_BG

    if focused:
        draw_glow_rect(screen, rect, ACCENT, radius=12, layers=2)

    pygame.draw.rect(screen, bg_color, rect, border_radius=12)
    pygame.draw.rect(screen, border_color, rect, 2, border_radius=12)

    dot_x = rect.x + 14
    dot_spacing = 15
    if masked and text:
        dot_radius = 4
        max_width = rect.width - 36
        if len(text) > 1:
            dot_spacing = min(dot_spacing, max_width / (len(text) - 1))
        dot_radius = min(dot_radius, max(1, int(dot_spacing / 2)))
        total_width = (len(text) - 1) * dot_spacing + dot_radius * 2
        dot_x = int(rect.centerx - total_width / 2 + dot_radius)
        dot_y = rect.centery
        old_clip = screen.get_clip()
        screen.set_clip(rect.inflate(-6, -6))
        for index in range(len(text)):
            pygame.draw.circle(
                screen,
                WHITE,
                (int(dot_x + index * dot_spacing), dot_y),
                dot_radius,
            )
        screen.set_clip(old_clip)
        surf = None
    elif text:
        surf = font.render(text, True, WHITE)
    else:
        surf = font.render(placeholder, True, (91, 109, 146))

    if not masked or not text:
        screen.blit(surf, (rect.x + 14, rect.y + (rect.height - surf.get_height()) // 2))

    if focused and (pygame.time.get_ticks() // 530) % 2 == 0:
        if masked:
            cx_pos = min(rect.right - 12, dot_x + len(text) * dot_spacing)
        else:
            cx_pos = rect.x + 14 + (surf.get_width() if text else 0) + 2
        pygame.draw.line(screen, ACCENT,
                         (cx_pos, rect.y + 10),
                         (cx_pos, rect.bottom - 10), 2)

    if label and label_font and focused:
        lbl_surf = label_font.render(label, True, ACCENT)
        lx = rect.x + 10
        ly = rect.y - lbl_surf.get_height() - 4
        screen.blit(lbl_surf, (lx, ly))


def draw_button(screen, font, rect, text, primary=True):
    """Draw a neon control button for the Singularity interface."""
    pulse = 0.72 + 0.28 * math.sin(pygame.time.get_ticks() * 0.004)
    if primary:
        fill = tuple(int(channel * pulse) for channel in SEL_BTN)
        border = tuple(int(channel * pulse) for channel in ACCENT_2)
        pygame.draw.rect(screen, fill, rect, border_radius=10)
        pygame.draw.rect(screen, border, rect, 1, border_radius=10)
    else:
        pygame.draw.rect(screen, DARK_BTN, rect, border_radius=12)
        pygame.draw.rect(screen, (72, 82, 126), rect, 1, border_radius=12)

    txt_surf = font.render(text, True, WHITE)
    screen.blit(txt_surf, (rect.centerx - txt_surf.get_width() // 2,
                            rect.centery - txt_surf.get_height() // 2))


def draw_divider(screen, cx, y, width=340, color=None):
    """Draw a horizontal decorative divider."""
    if color is None:
        color = ACCENT_2
    pygame.draw.line(screen, color, (cx - width // 2, y), (cx + width // 2, y), 2)


def draw_glow_title(screen, big_font, text, cx, y, color=ACCENT_2):
    """Draw title text with a soft colour glow underneath."""
    glow = big_font.render(text, True, (*color, 80))
    for dx, dy in [(-2, 2), (2, 2), (0, 3)]:
        gs = pygame.Surface(glow.get_size(), pygame.SRCALPHA)
        gs.blit(glow, (0, 0))
        gs.set_alpha(45)
        screen.blit(gs, (cx - glow.get_width() // 2 + dx, y + dy))
    surf = big_font.render(text, True, color)
    screen.blit(surf, (cx - surf.get_width() // 2, y))


def draw_singularity(screen, center, radius):
    """Draw a compact event-horizon emblem with violet and cyan accretion rings."""
    diameter = radius * 2 + 34
    halo = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    center_pt = (diameter // 2, diameter // 2)
    phase = pygame.time.get_ticks() * 0.001

    for index, (offset, color, alpha) in enumerate((
        (15, ACCENT_2, 34),
        (8, ACCENT, 70),
        (0, ACCENT_2, 150),
    )):
        wobble = math.sin(phase * 1.4 + index * 1.2) * 4
        width = int((radius + offset + wobble) * 2)
        height = int(radius + offset + wobble)
        ring = pygame.Rect(
            center_pt[0] - width // 2,
            center_pt[1] - height // 2,
            width,
            height,
        )
        pygame.draw.ellipse(halo, (*color, alpha), ring, 2)

    for index in range(6):
        angle = phase * (0.45 if index % 2 else -0.32) + index * math.tau / 6
        px = center_pt[0] + math.cos(angle) * (radius + 8)
        py = center_pt[1] + math.sin(angle) * (radius * 0.47 + 8)
        particle_color = ACCENT_2 if index % 2 else WHITE
        pygame.draw.circle(halo, (*particle_color, 150), (int(px), int(py)), 2)

    pulse = 0.85 + 0.15 * math.sin(phase * 2)
    core_radius = max(2, int(radius * 0.5 * pulse))
    pygame.draw.circle(halo, (2, 3, 10, 255), center_pt, core_radius)
    pygame.draw.circle(halo, (*ACCENT, 185), center_pt, core_radius, 2)
    screen.blit(halo, (center[0] - diameter // 2, center[1] - diameter // 2))


def _get_background(size):
    """Build and cache a low-resolution nebula gradient for smooth, fast blits."""
    if size in BACKGROUND_CACHE:
        return BACKGROUND_CACHE[size]

    width, height = size
    gradient = pygame.Surface((max(1, width // 4), max(1, height // 4)))
    gradient_width, gradient_height = gradient.get_size()
    for y in range(gradient_height):
        for x in range(gradient_width):
            nx = x / gradient_width
            ny = y / gradient_height
            violet = math.exp(-(((nx - 0.76) / 0.48) ** 2 + ((ny - 0.33) / 0.68) ** 2) * 2.1)
            cyan = math.exp(-(((nx - 0.18) / 0.42) ** 2 + ((ny - 0.76) / 0.52) ** 2) * 2.4)
            color = (
                min(255, int(5 + violet * 18 + cyan * 2)),
                min(255, int(7 + violet * 4 + cyan * 14)),
                min(255, int(18 + violet * 34 + cyan * 28)),
            )
            gradient.set_at((x, y), color)

    background = pygame.transform.smoothscale(gradient, size)
    BACKGROUND_CACHE[size] = background
    return background


def draw_stars(screen, stars):
    """Render the animated Singularity nebula, drifting stars, and occasional comets."""
    screen_w, screen_h = screen.get_size()
    t = pygame.time.get_ticks()
    seconds = t * 0.001

    screen.blit(_get_background((screen_w, screen_h)), (0, 0))

    energy = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    for band in range(3):
        points = []
        phase = seconds * (0.22 if band % 2 else -0.16) + band * 2.1
        baseline = screen_h * (0.31 + band * 0.18)
        for x in range(-10, screen_w + 20, 12):
            y = baseline + math.sin(x * 0.009 + phase) * 15 + math.sin(x * 0.021 - phase * 1.4) * 7
            points.append((x, int(y)))
        color = ACCENT if band % 2 == 0 else ACCENT_2
        pygame.draw.aalines(energy, (*color, 13), False, points)
        pygame.draw.aalines(energy, (*color, 5), False,
                            [(x, y + 3) for x, y in points])
    screen.blit(energy, (0, 0))

    for i, star in enumerate(stars):
        x, y, r, brightness, speed, drift = star

        x = (x + drift * 0.10) % (screen_w + 20)
        y += speed * 0.45

        if y > screen_h + 10:
            y = -5
            x = random.randint(0, screen_w)

        twinkle = 0.74 + 0.26 * math.sin(seconds * 2.1 + i * 1.73)
        flicker = max(75, min(230, int(brightness * twinkle)))
        if i % 7 == 0:
            star_color = (flicker // 2, flicker, min(255, flicker + 45))
        elif i % 5 == 0:
            star_color = (min(255, flicker + 28), flicker // 2, min(255, flicker + 20))
        else:
            star_color = (flicker, flicker, min(255, flicker + 28))
        pygame.draw.circle(screen, star_color, (int(x), int(y)), max(1, r))

        if r >= 2:
            pygame.draw.circle(screen, (190, 232, 255), (int(x), int(y)), 1)

        stars[i] = (x, y, r, brightness, speed, drift)

    comet_cycle = t % 6200
    if comet_cycle < 700:
        comet_index = t // 6200
        comet_x = (comet_index * 193 + 120) % (screen_w + 180) - 90
        progress = comet_cycle / 700
        head = (int(comet_x + progress * 190), int(screen_h * 0.16 + progress * 125))
        tail = (head[0] - 48, head[1] - 28)
        streak = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        pygame.draw.line(streak, (*ACCENT_2, 22), tail, head, 7)
        pygame.draw.line(streak, (*ACCENT_2, 175), tail, head, 2)
        pygame.draw.circle(streak, (*WHITE, 220), head, 2)
        screen.blit(streak, (0, 0))


def generate_stars(screen_width, screen_height, count=110):
    """Generate a galaxy-inspired star field with low motion and soft neon tones."""
    stars = []
    for _ in range(count):
        x = random.randint(0, screen_width)
        y = random.randint(0, screen_height)
        r = random.choice([1, 1, 1, 2, 2, 2, 3])
        b = random.randint(110, 200)
        speed = random.uniform(0.08, 0.5)
        drift = random.uniform(-0.2, 0.2)
        stars.append((x, y, r, b, speed, drift))
    return stars


def clean_username(username):
    """Filter out non-printable ASCII or control characters from username."""
    if not username:
        return "Guest"
    cleaned = "".join(c for c in username if c.isprintable() and ord(c) >= 32)
    return cleaned.strip() or "Guest"


def render_retro_score(score_val, color, scale=3):
    """Render score as pixelated 8-bit retro font by drawing at small size and scaling up."""
    small_font = pygame.font.SysFont("Consolas", 14, bold=True)
    temp = small_font.render(str(score_val), False, color)
    w, h = temp.get_size()
    return pygame.transform.scale(temp, (int(w * scale), int(h * scale)))


def draw_heart(screen, x, y, color, size=14):
    """Draw a smooth, symmetric heart at the requested HUD position."""
    scale = 3
    surface = pygame.Surface((size * 2 * scale, size * 2 * scale), pygame.SRCALPHA)
    center = size * scale
    points = []
    for step in range(65):
        angle = math.tau * step / 64
        px = 16 * math.sin(angle) ** 3
        py = (
            13 * math.cos(angle)
            - 5 * math.cos(2 * angle)
            - 2 * math.cos(3 * angle)
            - math.cos(4 * angle)
        )
        points.append((
            int(center + px * size * scale / 18),
            int(center - py * size * scale / 18),
        ))
    pygame.draw.polygon(surface, color, points)
    edge = tuple(max(0, channel - 48) for channel in color[:3]) + (255,)
    pygame.draw.aalines(surface, edge, True, points, 1)
    pygame.draw.line(surface, (255, 225, 238, 150),
                     (center - size * scale // 2, center - size * scale // 2),
                     (center - size * scale // 5, center - size * scale // 3), 2)
    surface = pygame.transform.smoothscale(surface, (size * 2, size * 2))
    screen.blit(surface, (x, y))


def draw_player_shield(screen, player, now_ms):
    """Draw a pulsing cyan shield around the player while its timer remains."""
    pulse = 0.5 + 0.5 * math.sin(now_ms * 0.012)
    shield_rect = player.get_rect().inflate(30, 20)
    shield = pygame.Surface(shield_rect.size, pygame.SRCALPHA)
    pygame.draw.ellipse(shield, (72, 224, 255, int(18 + pulse * 12)), shield.get_rect())
    pygame.draw.ellipse(shield, (72, 224, 255, int(125 + pulse * 90)),
                        shield.get_rect(), 2)
    pygame.draw.arc(shield, (218, 250, 255, 210),
                    shield.get_rect().inflate(-8, -8), 0.3, 2.4, 2)
    screen.blit(shield, shield_rect.topleft)


class GameManager:
    def __init__(self, screen, screen_width, screen_height, player_name=""):
        self.screen = screen
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.player_name = player_name
        self.db = DBManager(user="root", password="")
        self.settings = SettingsManager()
        self.volume = max(0, min(100, int(self.settings.get("volume", 100))))
        self.mobile_controls_enabled = bool(self.settings.get("mobile_controls", True))
        self.audio = AudioManager()
        self._apply_volume()
        self.leaderboard = []
        self.stars = generate_stars(screen_width, screen_height)

        self.font       = pygame.font.SysFont("Bahnschrift", 25, bold=True)
        self.big_font   = pygame.font.SysFont("Bahnschrift", 58, bold=True)
        self.settings_title_font = pygame.font.SysFont("Bahnschrift", 46, bold=True)
        self.small_font = pygame.font.SysFont("Bahnschrift", 20, bold=True)
        self.tiny_font  = pygame.font.SysFont("Bahnschrift", 15, bold=True)

        # --- Layout constants ---
        cx = screen_width // 2

        # Name input screen rects (shown after login)
        self.name_input_rect   = pygame.Rect(378, 298, 354, 44)
        self.start_button_rect = pygame.Rect(378, 465, 146, 44)
        self.profile_btn_rect  = pygame.Rect(536, 465, 104, 44)
        self.dashboard_lb_rect = pygame.Rect(650, 465, 102, 44)
        self.dashboard_settings_rect = pygame.Rect(642, 48, 110, 36)
        self.escape_settings_rect = pygame.Rect(650, 108, 120, 32)

        # Reload rect (game over) — repositioned dynamically in _update_game_over
        self.reload_button_rect = pygame.Rect(cx - 110, screen_height // 2 + 50, 220, 52)

        # Profile state
        self.profile_ship_color   = "original"
        self.profile_control      = "arrows"
        self.profile_difficulty   = "normal"
        self.profile_back_rect    = pygame.Rect(cx - 110, screen_height - 80, 220, 48)
        self.profile_option_rects = []

        # --- Login screen rects ---
        field_w = 340
        self.login_user_rect    = pygame.Rect(400, 203, field_w, 52)
        self.login_pass_rect    = pygame.Rect(400, 282, field_w, 52)
        self.login_btn_rect     = pygame.Rect(400, 370, 158, 50)
        self.login_reg_btn_rect = pygame.Rect(574, 370, 166, 50)
        self.login_lb_btn_rect  = pygame.Rect(450, 444, 240, 42)

        # --- Register screen rects ---
        self.reg_user_rect    = pygame.Rect(400, 170, field_w, 50)
        self.reg_pass_rect    = pygame.Rect(400, 250, field_w, 50)
        self.reg_conf_rect    = pygame.Rect(400, 330, field_w, 50)
        self.reg_create_rect  = pygame.Rect(400, 416, 158, 50)
        self.reg_back_rect    = pygame.Rect(574, 416, 166, 50)

        # --- Leaderboard screen rect ---
        self.lb_back_rect = pygame.Rect(cx - 105, 526, 210, 46)
        self.settings_volume_rect = pygame.Rect(cx - 188, 259, 294, 14)
        self.settings_test_audio_rect = pygame.Rect(cx + 116, 242, 94, 46)
        self.settings_controls_rect = pygame.Rect(cx + 86, 342, 112, 42)
        self.settings_dashboard_rect = pygame.Rect(cx - 204, 449, 190, 48)
        self.settings_resume_rect = pygame.Rect(cx + 14, 449, 190, 48)
        self.settings_return_state = "name_input"

        # --- Auth state ---
        self.login_username  = ""
        self.login_password  = ""
        self.login_focus     = "username"   # "username" | "password"
        self.login_error     = ""

        self.reg_username    = ""
        self.reg_password    = ""
        self.reg_confirm     = ""
        self.reg_focus       = "username"   # "username" | "password" | "confirm"
        self.reg_error       = ""
        self.reg_success     = ""

        self.old_name = ""
        self.fire_cooldown = 0
        self.reset_game()

    # ------------------------------------------------------------------
    # reset_game
    # ------------------------------------------------------------------
    def reset_game(self):
        self.player  = Player(self.screen_width, self.screen_height, self.profile_ship_color)
        self.buttons = MobileButtons()
        self.bullets = []
        self.enemy_bullets = []
        self.enemies = []

        self.score        = 0
        self.personal_best = 0
        self.max_player_lives = 3
        self.player_lives = self.max_player_lives
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.game_state   = "login"

        self.old_name     = self.player_name
        self.player_history = []
        self.timer        = 0
        self.state_timer  = 0
        self.enemy_direction = 1
        self.enemy_fire_timer = 0
        self.fire_cooldown = 0
        self.bullets = []
        self.enemy_bullets = []
        self.powerups = []
        self.powerup_spawn_timer = 0
        self.powerup_spawn_interval = random.randint(7 * 60, 10 * 60)
        self.shield_until_ms = 0

        # Clear auth fields on full reset
        self.login_username = self.player_name  # pre-fill if returning
        self.login_password = ""
        self.login_error    = ""
        self.reg_username   = ""
        self.reg_password   = ""
        self.reg_confirm    = ""
        self.reg_error      = ""
        self.reg_success    = ""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _load_profile_from_db(self):
        """Pull saved profile settings for the current player from DB."""
        if not self.player_name:
            return
        profile = self.db.get_player_profile(self.player_name)
        if profile:
            self.profile_ship_color = profile.get("ship_color", "original") or "original"
            self.profile_ship_color = "original"
            self.profile_control    = profile.get("control_scheme", "arrows") or "arrows"
            self.profile_difficulty = profile.get("difficulty", "normal") or "normal"
            self.player.set_color(self.profile_ship_color)
        self.personal_best = self.db.get_player_best_score(self.player_name)

    def _save_profile_to_db(self):
        """Persist current profile settings to DB."""
        if not self.player_name:
            return
        self.db.get_or_create_player(self.player_name)
        self.db.update_player_profile(
            self.player_name,
            ship_color     = self.profile_ship_color,
            control_scheme = self.profile_control,
            difficulty     = self.profile_difficulty,
        )

    def _after_login(self):
        """Common post-login initialisation."""
        self._load_profile_from_db()
        self.leaderboard = self.db.get_top_scores(limit=10)
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.player.set_color(self.profile_ship_color)
        self.game_state = "name_input"

    def _start_game(self):
        """Common logic when pressing START from the name input screen."""
        self.player_name = self.player_name.strip() or "Guest"
        if self.old_name and self.old_name != self.player_name:
            self.db.update_player_username(self.old_name, self.player_name)
        self.db.get_or_create_player(self.player_name)
        self._load_profile_from_db()
        self.spawn_number = DIFFICULTY_SPAWN.get(self.profile_difficulty, 5)
        self.player.set_color(self.profile_ship_color)
        self.game_state = "playing"
        self.spawn_enemies()

    def _handle_text_input(self, event, field_name, max_len=50, digits_only=False):
        """Generic keyboard handling for a text input field. Returns updated string."""
        current = getattr(self, field_name)
        ctrl = pygame.key.get_mods() & pygame.KMOD_CTRL
        if event.key == pygame.K_BACKSPACE:
            if ctrl:
                current = ""
            else:
                current = current[:-1]
        elif event.key == pygame.K_v and ctrl:
            try:
                clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                if clip:
                    text = clip.decode("utf-8", errors="ignore").replace("\x00", "").split("\n")[0]
                    current = (current + text)[:max_len]
            except Exception:
                pass
        elif event.unicode and event.unicode.isprintable() and event.key != pygame.K_TAB:
            if len(current) < max_len:
                current += event.unicode
        setattr(self, field_name, current)

    # ------------------------------------------------------------------
    # spawn_enemies
    # ------------------------------------------------------------------
    def spawn_enemies(self):
        self.enemies = []
        self.enemy_direction = 1
        for i in range(self.spawn_number):
            enemy = Enemy(i, self.spawn_number, self.screen_width, self.screen_height)
            enemy.direction = self.enemy_direction
            enemy.y = 100 + (i % 4) * 34
            self.enemies.append(enemy)
        self.timer = 0

    # ------------------------------------------------------------------
    # update (main dispatcher)
    # ------------------------------------------------------------------
    def update(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.game_state == "settings":
                    self.game_state = self.settings_return_state
                else:
                    self.settings_return_state = self.game_state
                    self.game_state = "settings"
                self._update_settings([])
                return

        if self.game_state == "login":
            self._update_login(events)
        elif self.game_state == "register":
            self._update_register(events)
        elif self.game_state == "leaderboard":
            self._update_leaderboard(events)
        elif self.game_state == "name_input":
            self._update_name_input(events)
        elif self.game_state == "profile":
            self._update_profile(events)
        elif self.game_state == "settings":
            self._update_settings(events)
        elif self.game_state in ("playing", "blinking"):
            self._update_playing(events)
        elif self.game_state == "game_over":
            self._update_game_over(events)

    def _apply_volume(self, save=False):
        volume = self.volume / 100
        self.audio.set_volume(volume)
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(volume)
            for channel_index in range(pygame.mixer.get_num_channels()):
                pygame.mixer.Channel(channel_index).set_volume(volume)
        if save:
            self.settings.set("volume", self.volume)

    def _update_settings(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.settings_volume_rect.inflate(0, 28).collidepoint(event.pos):
                    self.volume = round(
                        max(0, min(100, (event.pos[0] - self.settings_volume_rect.x)
                                   / self.settings_volume_rect.width * 100))
                    )
                    self._apply_volume()
                elif self.settings_test_audio_rect.collidepoint(event.pos):
                    self.audio.play("click")
                elif self.settings_controls_rect.collidepoint(event.pos):
                    self.mobile_controls_enabled = not self.mobile_controls_enabled
                    self.settings.set("mobile_controls", self.mobile_controls_enabled)
                    self.audio.play("click")
                elif self.settings_dashboard_rect.collidepoint(event.pos):
                    destination = "name_input" if self.player_name else "login"
                    self.settings_return_state = destination
                    self.game_state = destination
                    return
                elif self.settings_resume_rect.collidepoint(event.pos):
                    self.game_state = self.settings_return_state
                    self.audio.play("click")
                    return
            elif event.type == pygame.MOUSEMOTION and event.buttons[0]:
                if self.settings_volume_rect.inflate(0, 28).collidepoint(event.pos):
                    self.volume = round(
                        max(0, min(100, (event.pos[0] - self.settings_volume_rect.x)
                                   / self.settings_volume_rect.width * 100))
                    )
                    self._apply_volume()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.settings.set("volume", self.volume)

        self._draw_settings()

    def _draw_settings(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)
        cx = self.screen_width // 2
        draw_glow_title(self.screen, self.settings_title_font, "SYSTEM SETTINGS", cx, 30, color=ACCENT_2)
        subtitle = self.tiny_font.render("SINGULARITY  //  CONFIGURE YOUR EXPERIENCE", True, GRAY)
        self.screen.blit(subtitle, (cx - subtitle.get_width() // 2, 98))
        panel = pygame.Rect(cx - 235, 137, 470, 421)
        draw_panel(self.screen, panel, radius=20)

        audio_title = self.small_font.render("AUDIO OUTPUT", True, WHITE)
        self.screen.blit(audio_title, (panel.x + 30, 178))
        volume_label = self.tiny_font.render(f"MASTER VOLUME  {self.volume:03d}%", True, ACCENT_2)
        self.screen.blit(volume_label, (panel.right - volume_label.get_width() - 28, 182))
        track = self.settings_volume_rect
        pygame.draw.rect(self.screen, (35, 44, 76), track, border_radius=8)
        fill = track.copy()
        fill.width = round(track.width * self.volume / 100)
        if fill.width:
            pygame.draw.rect(self.screen, ACCENT, fill, border_radius=8)
        knob_x = max(track.left, min(track.right, track.x + fill.width))
        pygame.draw.circle(self.screen, (46, 32, 77), (knob_x, track.centery), 12)
        pygame.draw.circle(self.screen, WHITE, (knob_x, track.centery), 8)
        pygame.draw.circle(self.screen, ACCENT_2, (knob_x, track.centery), 8, 2)

        draw_button(self.screen, self.tiny_font, self.settings_test_audio_rect,
                    "TEST SOUND", primary=self.audio.available)
        pygame.draw.line(self.screen, (43, 53, 86),
                         (panel.x + 28, 294), (panel.right - 28, 294), 1)

        controls_title = self.small_font.render("TOUCH CONTROLS", True, WHITE)
        controls_detail = self.tiny_font.render("In-game movement and fire buttons", True, GRAY)
        self.screen.blit(controls_title, (panel.x + 30, 316))
        self.screen.blit(controls_detail, (panel.x + 30, 349))
        toggle_label = "ON" if self.mobile_controls_enabled else "OFF"
        toggle_rect = self.settings_controls_rect
        toggle_color = SEL_BTN if self.mobile_controls_enabled else DARK_BTN
        pygame.draw.rect(self.screen, toggle_color, toggle_rect, border_radius=12)
        pygame.draw.rect(self.screen, ACCENT_2 if self.mobile_controls_enabled else PANEL_BOR,
                         toggle_rect, 2, border_radius=12)
        toggle_text = self.tiny_font.render(toggle_label, True, WHITE)
        self.screen.blit(toggle_text, (toggle_rect.centerx - toggle_text.get_width() // 2,
                                       toggle_rect.centery - toggle_text.get_height() // 2))
        if not self.audio.available:
            audio_error = self.tiny_font.render("AUDIO DEVICE UNAVAILABLE", True, RED_ERR)
            self.screen.blit(audio_error, (panel.x + 30, 275))

        pygame.draw.line(self.screen, (43, 53, 86),
                         (panel.x + 28, 410), (panel.right - 28, 410), 1)
        draw_button(
            self.screen,
            self.tiny_font,
            self.settings_dashboard_rect,
            "DASHBOARD" if self.player_name else "BACK TO LOGIN",
            primary=True,
        )
        if self.settings_return_state in ("playing", "blinking"):
            resume_label = "RESUME MISSION"
        else:
            resume_label = "BACK"
        draw_button(
            self.screen,
            self.tiny_font,
            self.settings_resume_rect,
            resume_label,
            primary=False,
        )
        hint = self.tiny_font.render("ESC  //  RETURN TO PREVIOUS SCREEN", True, GRAY)
        self.screen.blit(hint, (cx - hint.get_width() // 2, 565))

    # ------------------------------------------------------------------
    # LOGIN state
    # ------------------------------------------------------------------
    def _update_login(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    self.login_focus = "password" if self.login_focus == "username" else "username"
                elif event.key == pygame.K_RETURN:
                    self._do_login()
                    return
                elif self.login_focus == "username":
                    self._handle_text_input(event, "login_username", max_len=50)
                elif self.login_focus == "password":
                    self._handle_text_input(event, "login_password", max_len=100)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.login_user_rect.collidepoint(event.pos):
                    self.login_focus = "username"
                elif self.login_pass_rect.collidepoint(event.pos):
                    self.login_focus = "password"
                elif self.login_btn_rect.collidepoint(event.pos):
                    self._do_login()
                    return
                elif self.login_reg_btn_rect.collidepoint(event.pos):
                    self.reg_username = self.login_username
                    self.reg_password = ""
                    self.reg_confirm  = ""
                    self.reg_error    = ""
                    self.reg_success  = ""
                    self.reg_focus    = "username"
                    self.game_state   = "register"
                    return
                elif self.login_lb_btn_rect.collidepoint(event.pos):
                    self.leaderboard = self.db.get_top_scores(limit=10)
                    self.settings_return_state = "login"
                    self.game_state  = "leaderboard"
                    return

        self._draw_login()

    def _do_login(self):
        if not self.login_username.strip():
            self.login_error = "Please enter a username."
            return
        if not self.login_password:
            self.login_error = "Please enter a password."
            return

        player_row = self.db.login_player(self.login_username.strip(), self.login_password)
        if player_row:
            self.player_name  = player_row["username"]
            self.login_error  = ""
            self.login_password = ""
            self._after_login()
        else:
            self.login_error = "Incorrect username or password."

    def _draw_login(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        draw_singularity(self.screen, (174, 293), 95)
        brand_font = pygame.font.SysFont("Bahnschrift", 42, bold=True)
        brand = brand_font.render("SINGULARITY", True, WHITE)
        self.screen.blit(brand, (34, 96))
        sub = self.small_font.render("DEEP SPACE // PILOT ACCESS", True, ACCENT_2)
        self.screen.blit(sub, (38, 145))
        self.screen.blit(pygame.transform.smoothscale(self.player.image, (190, 142)), (79, 338))
        tagline = self.tiny_font.render("ENTER THE EVENT HORIZON", True, GRAY)
        self.screen.blit(tagline, (45, 512))

        panel = pygame.Rect(366, 104, 414, 416)
        draw_panel(self.screen, panel, radius=20)
        heading = self.font.render("PILOT LOGIN", True, WHITE)
        self.screen.blit(heading, (400, 129))
        subheading = self.tiny_font.render("Authenticate to continue your mission.", True, GRAY)
        self.screen.blit(subheading, (400, 160))

        lbl_u = self.tiny_font.render("USERNAME", True, ACCENT_2)
        lbl_p = self.tiny_font.render("PASSWORD", True, ACCENT_2)
        self.screen.blit(lbl_u, (self.login_user_rect.x + 6,
                                  self.login_user_rect.y - lbl_u.get_height() - 4))
        self.screen.blit(lbl_p, (self.login_pass_rect.x + 6,
                                  self.login_pass_rect.y - lbl_p.get_height() - 4))

        draw_text_field(self.screen, self.font, self.login_user_rect,
                        self.login_username, "Enter username...", self.login_focus == "username")
        draw_text_field(self.screen, self.font, self.login_pass_rect,
                        self.login_password, "Enter password...", self.login_focus == "password", masked=True)

        draw_button(self.screen, self.font, self.login_btn_rect,     "ENTER",    primary=True)
        draw_button(self.screen, self.font, self.login_reg_btn_rect, "REGISTER", primary=False)
        draw_button(self.screen, self.small_font, self.login_lb_btn_rect, "VIEW GLOBAL RANKINGS", primary=False)

        if self.login_error:
            err_bg = pygame.Rect(400, 337, 340, 28)
            pygame.draw.rect(self.screen, (52, 13, 34), err_bg, border_radius=6)
            err = self.small_font.render(self.login_error, True, RED_ERR)
            self.screen.blit(err, (err_bg.centerx - err.get_width() // 2,
                                   err_bg.centery - err.get_height() // 2))

        hint = self.tiny_font.render("TAB SWITCHES FIELDS  //  ENTER TO SIGN IN", True, (89, 105, 145))
        self.screen.blit(hint, (400, 496))

    # ------------------------------------------------------------------
    # REGISTER state
    # ------------------------------------------------------------------
    def _update_register(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    order = ["username", "password", "confirm"]
                    idx = order.index(self.reg_focus)
                    self.reg_focus = order[(idx + 1) % len(order)]
                elif event.key == pygame.K_RETURN:
                    self._do_register()
                    return
                elif self.reg_focus == "username":
                    self._handle_text_input(event, "reg_username", max_len=50)
                elif self.reg_focus == "password":
                    self._handle_text_input(event, "reg_password", max_len=100)
                elif self.reg_focus == "confirm":
                    self._handle_text_input(event, "reg_confirm", max_len=100)

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.reg_user_rect.collidepoint(event.pos):
                    self.reg_focus = "username"
                elif self.reg_pass_rect.collidepoint(event.pos):
                    self.reg_focus = "password"
                elif self.reg_conf_rect.collidepoint(event.pos):
                    self.reg_focus = "confirm"
                elif self.reg_create_rect.collidepoint(event.pos):
                    self._do_register()
                    return
                elif self.reg_back_rect.collidepoint(event.pos):
                    self.game_state = "login"
                    return

        self._draw_register()

    def _do_register(self):
        username = self.reg_username.strip()
        password = self.reg_password
        confirm  = self.reg_confirm

        if not username or len(username) < 3:
            self.reg_error = "Username must be at least 3 characters."
            return
        if not password or len(password) < 4:
            self.reg_error = "Password must be at least 4 characters."
            return
        if password != confirm:
            self.reg_error = "Passwords do not match."
            return

        ok, result = self.db.register_player(username, password)
        if ok:
            # Auto-login after successful registration
            self.player_name   = username
            self.reg_error     = ""
            self.reg_success   = f"Account created! Welcome, {username}!"
            self._after_login()
        else:
            self.reg_error = result

    def _draw_register(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        draw_singularity(self.screen, (174, 285), 95)
        brand_font = pygame.font.SysFont("Bahnschrift", 42, bold=True)
        brand = brand_font.render("SINGULARITY", True, WHITE)
        self.screen.blit(brand, (34, 96))
        sub = self.small_font.render("CREATE YOUR PILOT ID", True, ACCENT_2)
        self.screen.blit(sub, (38, 145))
        self.screen.blit(pygame.transform.smoothscale(self.player.image, (190, 142)), (79, 338))
        tagline = self.tiny_font.render("YOUR NEXT RUN STARTS HERE", True, GRAY)
        self.screen.blit(tagline, (45, 512))

        panel = pygame.Rect(366, 72, 414, 476)
        draw_panel(self.screen, panel, radius=20)
        heading = self.font.render("NEW PILOT", True, WHITE)
        self.screen.blit(heading, (400, 97))
        subheading = self.tiny_font.render("Create an account to record your scores.", True, GRAY)
        self.screen.blit(subheading, (400, 126))

        labels_data = [
            ("USERNAME (3+ chars)",  self.reg_user_rect),
            ("PASSWORD (4+ chars)",  self.reg_pass_rect),
            ("CONFIRM PASSWORD",     self.reg_conf_rect),
        ]
        for lbl_text, f_rect in labels_data:
            lbl = self.tiny_font.render(lbl_text, True, ACCENT_2)
            self.screen.blit(lbl, (f_rect.x + 4, f_rect.y - lbl.get_height() - 3))

        draw_text_field(self.screen, self.font, self.reg_user_rect,
                        self.reg_username, "Choose a username...", self.reg_focus == "username")
        draw_text_field(self.screen, self.font, self.reg_pass_rect,
                        self.reg_password, "Choose a password...", self.reg_focus == "password", masked=True)
        draw_text_field(self.screen, self.font, self.reg_conf_rect,
                        self.reg_confirm,  "Re-enter password...", self.reg_focus == "confirm",  masked=True)

        draw_button(self.screen, self.font, self.reg_create_rect, "CREATE ID", primary=True)
        draw_button(self.screen, self.font, self.reg_back_rect,   "BACK", primary=False)

        msg_y = 480
        if self.reg_error:
            err_bg = pygame.Rect(400, msg_y - 3, 340, 30)
            pygame.draw.rect(self.screen, (52, 13, 34), err_bg, border_radius=6)
            err = self.tiny_font.render(self.reg_error, True, RED_ERR)
            self.screen.blit(err, (err_bg.centerx - err.get_width() // 2, msg_y))
        if self.reg_success:
            ok_surf = self.small_font.render(self.reg_success, True, ACCENT)
            self.screen.blit(ok_surf, (400, msg_y))

        hint = self.tiny_font.render("TAB SWITCHES FIELDS  //  ENTER TO CREATE", True, (89, 105, 145))
        self.screen.blit(hint, (400, 521))

    # ------------------------------------------------------------------
    # LEADERBOARD state
    # ------------------------------------------------------------------
    def _update_leaderboard(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.lb_back_rect.collidepoint(event.pos):
                    self.game_state = self.settings_return_state
                    return
            elif event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                self.game_state = self.settings_return_state
                return

        self._draw_leaderboard()

    def _draw_leaderboard(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        cx = self.screen_width // 2

        draw_glow_title(self.screen, self.big_font, "GLOBAL RANKINGS", cx, 18, color=ACCENT_2)

        sub = self.small_font.render("SINGULARITY  //  TOP 10 PILOT SCORES", True, GRAY)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 90))

        draw_divider(self.screen, cx, 118, width=360, color=ACCENT)

        table_rect = pygame.Rect(cx - 285, 126, 570, 384)
        draw_panel(self.screen, table_rect, radius=18)

        header_y = 138
        rank_x  = cx - 258
        name_x  = cx - 190
        score_center_x = cx + 125
        date_x  = cx + 172

        headers = [("RANK", rank_x), ("PILOT", name_x), ("DATE", date_x)]
        for h_text, h_x in headers:
            h_surf = self.tiny_font.render(h_text, True, ACCENT_2)
            self.screen.blit(h_surf, (h_x, header_y))

        score_lbl_surf = self.tiny_font.render("SCORE", True, ACCENT_2)
        self.screen.blit(score_lbl_surf, (score_center_x - score_lbl_surf.get_width() // 2, header_y))

        pygame.draw.line(self.screen, (55, 72, 118),
                         (table_rect.x + 12, header_y + 24),
                         (table_rect.right - 12, header_y + 24), 1)

        if not self.leaderboard:
            no_data = self.small_font.render("NO SCORES RECORDED // BE THE FIRST PILOT", True, GRAY)
            self.screen.blit(no_data, (cx - no_data.get_width() // 2, 285))
        else:
            row_y = header_y + 32
            rank_colors = {1: GOLD, 2: ACCENT_2, 3: ACCENT}
            medals      = {1: "01", 2: "02", 3: "03"}
            for i, entry in enumerate(self.leaderboard, start=1):
                display_name = clean_username(entry["username"])
                is_me     = (entry["username"] == self.player_name)
                row_color = ACCENT_2 if is_me else WHITE

                if is_me:
                    strip = pygame.Rect(table_rect.x + 6, row_y - 4,
                                        table_rect.width - 12, 32)
                    s = pygame.Surface((strip.width, strip.height), pygame.SRCALPHA)
                    s.fill((*ACCENT_2, 22))
                    self.screen.blit(s, strip.topleft)
                    pygame.draw.rect(self.screen, (*ACCENT_2, 70), strip, 1, border_radius=4)

                elif i % 2 == 0:
                    strip = pygame.Rect(table_rect.x + 6, row_y - 4,
                                        table_rect.width - 12, 32)
                    s = pygame.Surface((strip.width, strip.height), pygame.SRCALPHA)
                    s.fill((110, 138, 210, 8))
                    self.screen.blit(s, strip.topleft)

                rank_color = rank_colors.get(i, GRAY)
                rank_label = medals.get(i, str(i))
                rank_surf  = self.small_font.render(rank_label, True, rank_color)
                name_surf  = self.small_font.render(display_name[:18], True, row_color)
                score_surf = self.font.render(str(entry["score"]), True, row_color)

                achieved = entry.get("achieved_at")
                date_str = str(achieved)[:10] if achieved else "—"
                date_surf = self.tiny_font.render(date_str, True, GRAY)

                self.screen.blit(rank_surf,  (rank_x,  row_y))
                self.screen.blit(name_surf,  (name_x,  row_y))
                self.screen.blit(score_surf, (score_center_x - score_surf.get_width() // 2, row_y - 2))
                self.screen.blit(date_surf,  (date_x,  row_y + 6))
                row_y += 31

        back_label = (
            "BACK TO DASHBOARD"
            if self.settings_return_state == "name_input"
            else "BACK"
        )
        draw_button(self.screen, self.small_font, self.lb_back_rect, back_label, primary=False)

    # ------------------------------------------------------------------
    # NAME INPUT state
    # ------------------------------------------------------------------
    def _update_name_input(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                ctrl_held = pygame.key.get_mods() & pygame.KMOD_CTRL
                if event.key == pygame.K_BACKSPACE:
                    if ctrl_held or getattr(self, "_name_select_all", False):
                        self.player_name = ""
                        self._name_select_all = False
                    else:
                        self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_a and ctrl_held:
                    self._name_select_all = True
                elif event.key == pygame.K_v and ctrl_held:
                    try:
                        clipboard = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clipboard:
                            text = clipboard.decode("utf-8", errors="ignore").replace("\x00", "").split("\n")[0]
                            combined = self.player_name + text
                            self.player_name = combined[:15]
                    except Exception:
                        pass
                elif event.key == pygame.K_RETURN:
                    self._start_game()
                    return
                elif event.key != pygame.K_TAB and event.unicode.isprintable():
                    if getattr(self, "_name_select_all", False):
                        self.player_name = event.unicode
                        self._name_select_all = False
                    elif len(self.player_name) < 15:
                        self.player_name += event.unicode
                else:
                    self._name_select_all = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.start_button_rect.collidepoint(event.pos):
                    self._start_game()
                    return
                if self.dashboard_settings_rect.collidepoint(event.pos):
                    self.settings_return_state = "name_input"
                    self.game_state = "settings"
                    return
                if self.dashboard_lb_rect.collidepoint(event.pos):
                    self.leaderboard = self.db.get_top_scores(limit=10)
                    self.settings_return_state = "name_input"
                    self.game_state = "leaderboard"
                    return
                if self.profile_btn_rect.collidepoint(event.pos):
                    self.player_name = self.player_name.strip() or "Guest"
                    self.db.get_or_create_player(self.player_name)
                    self._load_profile_from_db()
                    self.game_state = "profile"
                    return

        self._draw_dashboard()

    def _draw_dashboard(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        draw_singularity(self.screen, (184, 294), 108)
        brand = self.font.render("SINGULARITY", True, WHITE)
        self.screen.blit(brand, (42, 48))
        section = self.tiny_font.render("COMMAND DECK  //  PILOT ONLINE", True, ACCENT_2)
        self.screen.blit(section, (45, 84))
        self.screen.blit(pygame.transform.smoothscale(self.player.image, (220, 165)), (74, 344))

        pilot_tag = self.tiny_font.render("CURRENT PILOT", True, GRAY)
        self.screen.blit(pilot_tag, (44, 213))
        pilot_name = self.small_font.render(clean_username(self.player_name).upper(), True, WHITE)
        self.screen.blit(pilot_name, (44, 236))

        card = pygame.Rect(340, 111, 430, 414)
        draw_panel(self.screen, card, radius=20)
        heading = self.font.render("MISSION CONTROL", True, WHITE)
        self.screen.blit(heading, (378, 144))
        status = self.tiny_font.render("SYSTEM STATUS  /  READY", True, ACCENT_2)
        self.screen.blit(status, (378, 175))
        draw_button(
            self.screen,
            self.tiny_font,
            self.dashboard_settings_rect,
            "SETTINGS / ESC",
            primary=False,
        )

        pilot_card = pygame.Rect(378, 203, 354, 82)
        pygame.draw.rect(self.screen, (13, 20, 43), pilot_card, border_radius=10)
        pygame.draw.rect(self.screen, (55, 72, 118), pilot_card, 1, border_radius=10)
        pilot_lbl = self.tiny_font.render("PILOT", True, GRAY)
        pilot_val = self.small_font.render(clean_username(self.player_name), True, ACCENT)
        self.screen.blit(pilot_lbl, (394, 216))
        self.screen.blit(pilot_val, (394, 239))
        pygame.draw.line(self.screen, (55, 72, 118), (570, 215), (570, 273), 1)
        pb_lbl = self.tiny_font.render("PERSONAL BEST", True, GRAY)
        pb_val = render_retro_score(self.personal_best, GOLD, scale=1.55)
        self.screen.blit(pb_lbl, (590, 216))
        self.screen.blit(pb_val, (590, 240))

        dn_lbl = self.tiny_font.render("DISPLAY CALLSIGN", True, ACCENT_2)
        self.screen.blit(dn_lbl, (self.name_input_rect.x + 4,
                                   self.name_input_rect.y - dn_lbl.get_height() - 4))

        draw_text_field(self.screen, self.font, self.name_input_rect,
                        self.player_name, "Your display name...", True)

        lb_title = self.tiny_font.render("GLOBAL LEADERBOARD  //  TOP PILOTS", True, ACCENT_2)
        self.screen.blit(lb_title, (378, 352))
        for index, entry in enumerate(self.leaderboard[:3]):
            row_y = 374 + index * 25
            rank_color = (GOLD, ACCENT_2, ACCENT)[index]
            rank = self.tiny_font.render(f"{index + 1:02}", True, rank_color)
            name = self.tiny_font.render(clean_username(entry["username"])[:19], True, WHITE)
            score = self.tiny_font.render(str(entry["score"]), True, rank_color)
            self.screen.blit(rank, (382, row_y))
            self.screen.blit(name, (416, row_y))
            self.screen.blit(score, (706 - score.get_width(), row_y))
        if not self.leaderboard:
            no_scores = self.tiny_font.render("No scores recorded yet.", True, GRAY)
            self.screen.blit(no_scores, (382, 377))

        draw_button(self.screen, self.tiny_font, self.start_button_rect, "LAUNCH", primary=True)
        draw_button(self.screen, self.tiny_font, self.profile_btn_rect, "PILOT", primary=False)
        draw_button(self.screen, self.tiny_font, self.dashboard_lb_rect, "RANKS", primary=False)

    # ------------------------------------------------------------------
    # PROFILE state
    # ------------------------------------------------------------------
    def _update_profile(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, category, value in self.profile_option_rects:
                    if rect.collidepoint(event.pos):
                        if category == "control":
                            self.profile_control = value
                        elif category == "difficulty":
                            self.profile_difficulty = value
                if self.profile_back_rect.collidepoint(event.pos):
                    self._save_profile_to_db()
                    self.game_state = "name_input"

        self._draw_profile()

    def _draw_profile(self):
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)
        self.profile_option_rects = []

        cx = self.screen_width // 2

        draw_glow_title(self.screen, self.big_font, "Player Profile", cx, 26)
        draw_divider(self.screen, cx, 104, width=260, color=(0, 120, 55))

        sub = self.small_font.render(f"Player:  {self.player_name}", True, GRAY)
        self.screen.blit(sub, (cx - sub.get_width() // 2, 114))

        x_start = cx - 290
        y = 225
        rects = draw_option_row(self.screen, self.small_font,
                                "Controls:", CONTROL_SCHEMES, self.profile_control,
                                y, x_start, item_w=115)
        self.profile_option_rects += [(r, "control", v) for r, v in rects]
        y += 62
        rects = draw_option_row(self.screen, self.small_font,
                                "Difficulty:", DIFFICULTIES, self.profile_difficulty,
                                y, x_start, item_w=85)
        self.profile_option_rects += [(r, "difficulty", v) for r, v in rects]
        y += 62

        legend = self.small_font.render("Arrow Keys / WASD  —  move    SPACE  —  shoot", True, (80, 90, 130))
        self.screen.blit(legend, (cx - legend.get_width() // 2, y))

        draw_button(self.screen, self.font, self.profile_back_rect, "Save & Back", primary=True)

    # ------------------------------------------------------------------
    # PLAYING / BLINKING state
    # ------------------------------------------------------------------
    def _update_playing(self, events):
        for event in events:
            if (
                event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.escape_settings_rect.collidepoint(event.pos)
            ):
                self.settings_return_state = self.game_state
                self.game_state = "settings"
                self._draw_settings()
                return

        if self.game_state in ("playing", "blinking"):
            self.player_history.append((self.player.x, self.player.y))
            if len(self.player_history) > 60:
                self.player_history.pop(0)

        if self.game_state == "playing":
            keys = pygame.key.get_pressed()
            use_wasd = (self.profile_control == "wasd")

            left_key  = pygame.K_a    if use_wasd else pygame.K_LEFT
            right_key = pygame.K_d    if use_wasd else pygame.K_RIGHT

            if keys[left_key]:
                self.player.move_left()
            if keys[right_key]:
                self.player.move_right()

            screen_button_fired = (
                self.buttons.handle_mouse(self.player, events)
                if self.mobile_controls_enabled
                else False
            )
            keyboard_fired = keys[pygame.K_SPACE]

            if self.fire_cooldown > 0:
                self.fire_cooldown -= 1

            if (screen_button_fired or keyboard_fired) and self.fire_cooldown <= 0:
                bullet_x = self.player.x + self.player.width // 2 - 10
                self.bullets.append(Bullet(
                    bullet_x,
                    self.player.y - 34,
                    direction="up",
                    speed=5,
                    screen_height=self.screen_height,
                ))
                self.audio.play("shoot")
                self.fire_cooldown = 20

            self.player.keep_inside_screen()

            self.powerup_spawn_timer += 1
            if self.powerup_spawn_timer >= self.powerup_spawn_interval:
                powerup_x = random.randint(20, self.screen_width - PowerUp.WIDTH - 20)
                powerup_kind = random.choice(("heart", "shield"))
                self.powerups.append(PowerUp(powerup_kind, powerup_x))
                self.powerup_spawn_timer = 0
                self.powerup_spawn_interval = random.randint(12 * 60, 20 * 60)

            player_rect = self.player.get_rect()
            for powerup in self.powerups[:]:
                powerup.update(self.screen_height)
                if powerup.rect.colliderect(player_rect):
                    self.audio.play("pickup")
                    if powerup.kind == "heart":
                        self.player_lives = min(self.max_player_lives, self.player_lives + 1)
                    else:
                        self.shield_until_ms = pygame.time.get_ticks() + 6000
                    powerup.is_active = False
                if not powerup.is_active:
                    self.powerups.remove(powerup)

            for bullet in self.bullets[:]:
                bullet.update()
                if not bullet.is_active:
                    self.bullets.remove(bullet)

            self.timer += 1
            self.enemy_fire_timer += 1

            alive_enemies = [e for e in self.enemies if e.state == "waiting"]
            if alive_enemies:
                min_x = min(e.x for e in alive_enemies)
                max_x = max(e.x + e.width for e in alive_enemies)
                if min_x <= 0 or max_x >= self.screen_width:
                    self.enemy_direction *= -1

            for enemy in self.enemies:
                enemy.update(self.enemy_direction)

            if self.enemy_fire_timer >= 90:
                can_fire = [e for e in self.enemies if e.state == "waiting"]
                if can_fire:
                    shooter = random.choice(can_fire)
                    bullet_x = shooter.x + shooter.width // 2 - 10
                    bullet_y = shooter.y + shooter.height - 20
                    self.enemy_bullets.append(Bullet(
                        bullet_x,
                        bullet_y,
                        direction="down",
                        speed=2.5,
                        screen_height=self.screen_height,
                    ))
                self.enemy_fire_timer = 0

            for enemy_bullet in self.enemy_bullets[:]:
                enemy_bullet.update()
                if not enemy_bullet.is_active:
                    self.enemy_bullets.remove(enemy_bullet)

            all_despawned = all(e.state == "offscreen" for e in self.enemies)
            if all_despawned:
                self.spawn_number += 1
                self.spawn_enemies()

            self.check_collisions()

        elif self.game_state == "blinking":
            self.player.update_blink()
            self.state_timer += 1
            for enemy in self.enemies:
                enemy.update()

            if self.state_timer >= 180:
                if self.player_lives <= 0:
                    self.db.save_score(self.player_name, self.score)
                    if self.score > self.personal_best:
                        self.personal_best = self.score
                    self.leaderboard = self.db.get_top_scores(limit=10)
                    self.game_state = "game_over"
                else:
                    self.game_state = "playing"
                    self.player.is_blinking = False
                    self.player.visible = True
                    self.player.x = self.screen_width // 2 - self.player.width // 2
                    self.player.y = self.screen_height - 100
                    self.bullets = []
                    self.enemy_bullets = []

        # --- Draw playing / blinking ---
        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        for powerup in self.powerups:
            powerup.draw(self.screen)
        now_ms = pygame.time.get_ticks()
        if now_ms < self.shield_until_ms:
            draw_player_shield(self.screen, self.player, now_ms)
        self.player.draw(self.screen)
        for enemy in self.enemies:
            enemy.draw(self.screen)
        for bullet in self.bullets:
            bullet.draw(self.screen)
        for enemy_bullet in self.enemy_bullets:
            enemy_bullet.draw(self.screen)
        if self.mobile_controls_enabled:
            self.buttons.draw(self.screen)

        # HUD — score chip (compact layout)
        score_bg = pygame.Rect(10, 10, 150, 38)
        pygame.draw.rect(self.screen, (14, 16, 36), score_bg, border_radius=8)
        pygame.draw.rect(self.screen, (40, 44, 80), score_bg, 1, border_radius=8)
        score_lbl = self.tiny_font.render("SCORE", True, (80, 90, 140))
        self.screen.blit(score_lbl, (20, 20))
        
        score_val = render_retro_score(self.score, WHITE, scale=1.8)
        self.screen.blit(score_val, (84, 17))
 
        # HUD — best chip (compact layout)
        pb_bg = pygame.Rect(10, 54, 150, 38)
        pygame.draw.rect(self.screen, (14, 16, 36), pb_bg, border_radius=8)
        pygame.draw.rect(self.screen, (40, 44, 80), pb_bg, 1, border_radius=8)
        pb_lbl = self.tiny_font.render("BEST", True, (100, 80, 10))
        self.screen.blit(pb_lbl, (20, 64))
        
        pb_val = render_retro_score(self.personal_best, GOLD, scale=1.8)
        self.screen.blit(pb_val, (84, 61))

        lives_bg = pygame.Rect(self.screen_width - 190, 58, 170, 38)
        pygame.draw.rect(self.screen, (14, 16, 36), lives_bg, border_radius=8)
        pygame.draw.rect(self.screen, (40, 44, 80), lives_bg, 1, border_radius=8)
        lives_lbl = self.tiny_font.render("LIVES", True, (200, 100, 110))
        self.screen.blit(lives_lbl, (self.screen_width - 180, 68))

        heart_x = self.screen_width - 132
        for i in range(self.max_player_lives):
            heart_color = (255, 80, 90) if i < self.player_lives else (80, 80, 90)
            draw_heart(self.screen, heart_x + i * 34, 62, heart_color, size=15)

        if now_ms < self.shield_until_ms:
            shield_seconds = (self.shield_until_ms - now_ms + 999) // 1000
            shield_label = self.tiny_font.render(
                f"SHIELD ACTIVE  {shield_seconds}s", True, ACCENT_2
            )
            self.screen.blit(shield_label, (self.screen_width - shield_label.get_width() - 14, 154))

        # HUD — right side hints
        ctrl_hint = "← → Move  |  SPACE Shoot" if self.profile_control == "arrows" else "A D Move  |  SPACE Shoot"
        hint_surf = self.tiny_font.render(ctrl_hint, True, (70, 75, 110))
        self.screen.blit(hint_surf, (self.screen_width - hint_surf.get_width() - 12, 14))

        diff_colors = {"easy": (0, 200, 80), "normal": (255, 200, 0), "hard": (255, 60, 60)}
        diff_col  = diff_colors.get(self.profile_difficulty, WHITE)
        diff_surf = self.small_font.render(self.profile_difficulty.upper(), True, diff_col)
        self.screen.blit(diff_surf, (self.screen_width - diff_surf.get_width() - 12, 32))
        draw_button(
            self.screen,
            self.tiny_font,
            self.escape_settings_rect,
            "ESC / SETTINGS",
            primary=False,
        )

    # ------------------------------------------------------------------
    # GAME OVER state
    # ------------------------------------------------------------------
    def _update_game_over(self, events):
        cx = self.screen_width // 2

        # Dynamic rects based on leaderboard length (max 5 shown on game over screen)
        lb_count = min(len(self.leaderboard), 5)
        lb_height = max(lb_count, 1) * 34
        view_lb_y = 274 + lb_height + 12
        play_again_y = view_lb_y + 54

        self.view_lb_btn_rect    = pygame.Rect(cx - 120, view_lb_y, 240, 44)
        self.reload_button_rect  = pygame.Rect(cx - 100, play_again_y, 200, 50)

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.reload_button_rect.collidepoint(event.pos):
                    # Keep player logged in; only reset gameplay
                    saved_name   = self.player_name
                    saved_best   = self.personal_best
                    saved_color  = self.profile_ship_color
                    saved_ctrl   = self.profile_control
                    saved_diff   = self.profile_difficulty
                    self.reset_game()
                    self.player_name      = saved_name
                    self.personal_best    = saved_best
                    self.profile_ship_color = saved_color
                    self.profile_control   = saved_ctrl
                    self.profile_difficulty = saved_diff
                    self.player.set_color(saved_color)
                    self.spawn_number = DIFFICULTY_SPAWN.get(saved_diff, 5)
                    self.game_state = "name_input"
                    return
                if self.view_lb_btn_rect.collidepoint(event.pos):
                    self.settings_return_state = "game_over"
                    self.game_state = "leaderboard"
                    return

        self.screen.fill(DARK_BG)
        draw_stars(self.screen, self.stars)

        # Title
        draw_glow_title(self.screen, self.big_font, "GAME OVER", cx, 24, color=(220, 40, 40))

        # Score card (made taller to prevent score text overflow/overlap)
        score_card = pygame.Rect(cx - 160, 96, 320, 96)
        pygame.draw.rect(self.screen, PANEL_BG, score_card, border_radius=16)
        pygame.draw.rect(self.screen, PANEL_BOR, score_card, 2, border_radius=16)

        sc_lbl  = self.tiny_font.render("FINAL SCORE", True, (80, 90, 140))
        self.screen.blit(sc_lbl, (cx - sc_lbl.get_width() // 2, 106))
        
        # Retro pixelated score value
        sc_val = render_retro_score(self.score, WHITE, scale=3.6)
        self.screen.blit(sc_val, (cx - sc_val.get_width() // 2, 130))

        # New best badge (pushed down slightly to keep clean margins)
        new_best_y = 202
        if self.score >= self.personal_best and self.score > 0:
            nb_bg = pygame.Rect(cx - 120, new_best_y - 2, 240, 28)
            pygame.draw.rect(self.screen, (35, 28, 0), nb_bg, border_radius=8)
            pygame.draw.rect(self.screen, (140, 100, 0), nb_bg, 1, border_radius=8)
            nb_surf = self.small_font.render(" New Personal Best!", True, GOLD)
            self.screen.blit(nb_surf, (cx - nb_surf.get_width() // 2, new_best_y))

        # Leaderboard mini-table (repositioned to account for taller score card)
        lb_title = self.small_font.render("TOP SCORES", True, (120, 100, 20))
        self.screen.blit(lb_title, (cx - lb_title.get_width() // 2, 242))
        draw_divider(self.screen, cx, 266, width=360, color=(60, 50, 0))

        y_offset = 274
        if self.leaderboard:
            rank_colors = {1: GOLD, 2: (210, 210, 210), 3: (205, 130, 55)}
            for i, entry in enumerate(self.leaderboard[:5], start=1):
                display_name = clean_username(entry["username"])
                is_me = entry["username"] == self.player_name
                row_col = ACCENT if is_me else (200, 200, 215)
                rk_col  = rank_colors.get(i, row_col)

                if is_me:
                    hi = pygame.Rect(cx - 190, y_offset - 3, 380, 30)
                    hs = pygame.Surface((hi.width, hi.height), pygame.SRCALPHA)
                    hs.fill((0, 200, 80, 22))
                    self.screen.blit(hs, hi.topleft)

                rk_surf  = self.small_font.render(str(i), True, rk_col)
                nm_surf  = self.small_font.render(display_name[:16], True, row_col)
                sc_surf2 = self.font.render(str(entry["score"]), True, row_col)
                self.screen.blit(rk_surf,  (cx - 185, y_offset))
                self.screen.blit(nm_surf,  (cx - 155, y_offset))
                self.screen.blit(sc_surf2, (cx + 80,  y_offset - 2))
                y_offset += 34
        else:
            no_scores = self.small_font.render("No scores yet", True, GRAY)
            self.screen.blit(no_scores, (cx - no_scores.get_width() // 2, y_offset))
            y_offset += 34

        # View full leaderboard
        draw_button(self.screen, self.small_font, self.view_lb_btn_rect,
                    "  Full Leaderboard", primary=False)

        # Play Again
        draw_button(self.screen, self.font, self.reload_button_rect, "PLAY AGAIN", primary=True)

    # ------------------------------------------------------------------
    # Collision detection
    # ------------------------------------------------------------------
    def _take_hit(self):
        if (
            self.player.is_blinking
            or self.game_state != "playing"
            or pygame.time.get_ticks() < self.shield_until_ms
        ):
            return

        self.player_lives -= 1
        self.audio.play("hit")
        self.player.is_blinking = True
        self.game_state = "blinking"
        self.state_timer = 0
        self.bullets = []
        self.enemy_bullets = []

    def check_collisions(self):
        player_rect = self.player.get_rect()
        shield_active = pygame.time.get_ticks() < self.shield_until_ms

        for enemy in self.enemies:
            if enemy.state == "offscreen":
                continue

            enemy_rect = enemy.get_rect()

            if player_rect.colliderect(enemy_rect):
                if not shield_active:
                    self._take_hit()
                    return

            for bullet in self.bullets[:]:
                if bullet.get_rect().colliderect(enemy_rect):
                    enemy.state = "offscreen"
                    bullet.is_active = False
                    self.score += 1
                    self.audio.play("enemy")
                    break

        for enemy_bullet in self.enemy_bullets[:]:
            if enemy_bullet.get_rect().colliderect(player_rect):
                enemy_bullet.is_active = False
                if not shield_active:
                    self._take_hit()
                    return