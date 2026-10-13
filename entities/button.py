import pygame

class MobileButtons:
    def __init__(self):
        self.left = pygame.Rect(20, 520, 80, 60)
        self.right = pygame.Rect(120, 520, 80, 60)
        self.fire = pygame.Rect(680, 520, 100, 60)

    def draw(self, screen):
        buttons = (
            (self.left, "<", (31, 118, 160)),
            (self.right, ">", (31, 118, 160)),
            (self.fire, "FIRE", (126, 49, 166)),
        )
        font = pygame.font.SysFont("Bahnschrift", 17, bold=True)
        for rect, label, color in buttons:
            pygame.draw.rect(screen, (8, 15, 35), rect, border_radius=10)
            pygame.draw.rect(screen, color, rect, 2, border_radius=10)
            text = font.render(label, True, (225, 241, 255))
            screen.blit(text, text.get_rect(center=rect.center))

    def handle_mouse(self, player, events):
        mouse_pressed = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        if mouse_pressed[0]:
            if self.left.collidepoint(mouse_pos):
                player.move_left()
            if self.right.collidepoint(mouse_pos):
                player.move_right()
            if self.fire.collidepoint(mouse_pos):
                return True

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.fire.collidepoint(event.pos):
                    return True
        return False
