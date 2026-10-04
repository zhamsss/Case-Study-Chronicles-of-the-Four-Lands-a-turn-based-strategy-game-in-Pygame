import pygame


class Button:

    def __init__(
        self,
        x,
        y,
        width,
        height,
        text,
        font_size=36
    ):

        self.rect = pygame.Rect(
            x,
            y,
            width,
            height
        )

        self.text = text

        self.font = pygame.font.Font(
            None,
            font_size
        )

        self.enabled = True

        self.active = False

    def draw(self, screen):

        if not self.enabled:
            background = (42, 46, 54)
            foreground = (115, 115, 115)

        elif self.active:
            background = (60, 130, 80)
            foreground = (255, 255, 255)

        elif self.rect.collidepoint(pygame.mouse.get_pos()):
            background = (95, 95, 95)
            foreground = (255, 255, 255)

        else:
            background = (70, 70, 70)
            foreground = (255, 255, 255)

        pygame.draw.rect(
            screen,
            background,
            self.rect,
            border_radius=10
        )

        text_surface = self.font.render(
            self.text,
            True,
            foreground
        )

        screen.blit(
            text_surface,
            text_surface.get_rect(
                center=self.rect.center
            )
        )

    def is_clicked(self, pos):

        return (
            self.enabled
            and self.rect.collidepoint(pos)
        )
