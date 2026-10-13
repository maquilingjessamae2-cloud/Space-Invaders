import math

import pygame


class PowerUp:
    WIDTH = 38
    HEIGHT = 38

    def __init__(self, kind, x, y=-38, speed=2.0):
        self.kind = kind
        self.x = x
        self.y = y
        self.speed = speed
        self.is_active = True
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.image = self._make_image()

    def _make_image(self):
        cyan = (72, 224, 255)
        violet = (177, 91, 255)
        pink = (255, 105, 190)
        color = pink if self.kind == "heart" else cyan

        image = pygame.Surface((self.WIDTH, self.HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(image, (*color, 30), (19, 19), 18)
        pygame.draw.circle(image, (*color, 210), (19, 19), 15, 2)
        pygame.draw.circle(image, (*violet, 100), (19, 19), 11, 1)

        if self.kind == "heart":
            points = []
            for step in range(49):
                angle = math.tau * step / 48
                px = 16 * math.sin(angle) ** 3
                py = (
                    13 * math.cos(angle)
                    - 5 * math.cos(2 * angle)
                    - 2 * math.cos(3 * angle)
                    - math.cos(4 * angle)
                )
                points.append((int(19 + px * 0.55), int(19 - py * 0.55)))
            pygame.draw.polygon(image, color, points)
            pygame.draw.aalines(image, (255, 225, 245), True, points, 1)
        else:
            shield_points = [
                (19, 8), (28, 12), (27, 21), (23, 27), (19, 31),
                (15, 27), (11, 21), (10, 12),
            ]
            pygame.draw.polygon(image, color, shield_points, 2)
            pygame.draw.line(image, (225, 255, 255), (19, 12), (19, 26), 2)
            pygame.draw.line(image, (225, 255, 255), (14, 17), (24, 17), 1)

        return image

    def update(self, screen_height):
        self.y += self.speed
        self.rect.topleft = (round(self.x), round(self.y))
        if self.y > screen_height:
            self.is_active = False

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, self.rect)
