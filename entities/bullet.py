import pygame

class Bullet:
    def __init__(self, x, y, direction="up", speed=None, screen_height=600):
        self.width = 20
        self.height = 40
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed if speed is not None else (5 if direction == "up" else 3)
        self.vx = 0
        self.vy = -self.speed if direction == "up" else self.speed
        self.screen_height = screen_height
        self.is_active = True
        self.image = self._make_image()

    def _make_image(self):
        image = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        core = (85, 235, 255) if self.direction == "up" else (255, 105, 190)
        glow = (80, 100, 255) if self.direction == "up" else (255, 50, 110)
        pygame.draw.ellipse(image, (*glow, 48), (1, 1, self.width - 2, self.height - 2))
        pygame.draw.polygon(image, (*core, 180), [
            (self.width // 2, 1),
            (self.width - 2, self.height // 2),
            (self.width // 2, self.height - 1),
            (2, self.height // 2),
        ])
        pygame.draw.rect(image, core, (self.width // 2 - 4, 5, 8, self.height - 10), border_radius=4)
        pygame.draw.line(image, (245, 255, 255), (self.width // 2, 7),
                         (self.width // 2, self.height - 8), 2)
        return image

    def update(self):
        self.x += self.vx
        self.y += self.vy

        if self.direction == "up":
            if self.y < -self.height:
                self.is_active = False
        else:
            if self.y > self.screen_height + self.height:
                self.is_active = False

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, (self.x, self.y))
