import pygame
import random
import sys
import math

# Initialize Pygame (audio skipped to avoid ALSA errors)
pygame.init()
# No mixer initialization – game will run silently

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
GROUND_HEIGHT = 550
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_BLUE = (200, 200, 255)
DARK_PURPLE = (50, 50, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)

# Game states
MENU = 0
PLAYING = 1
GAME_OVER = 2

# ----------------------------------------------------------------------
# Particle System
# ----------------------------------------------------------------------
class Particle:
    def __init__(self, x, y, color, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.vx, self.vy = velocity
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.age += 1

    def draw(self, screen):
        fade_factor = 1 - self.age / self.lifetime
        color = (int(self.color[0] * fade_factor), int(self.color[1] * fade_factor), int(self.color[2] * fade_factor))
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 3)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, color, count=10):
        for _ in range(count):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-5, -1)
            lifetime = random.randint(20, 40)
            self.particles.append(Particle(x, y, color, (vx, vy), lifetime))

    def update(self):
        self.particles = [p for p in self.particles if p.age < p.lifetime]
        for p in self.particles:
            p.update()

    def draw(self, screen):
        for p in self.particles:
            p.draw(screen)

# ----------------------------------------------------------------------
# Player
# ----------------------------------------------------------------------
class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.width = 30
        self.height = 30
        self.image = pygame.Surface((self.width, self.height))
        self.form = "light"  # "light" or "shadow"
        self.update_image()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.gravity = 0.8
        self.jump_power = -12
        self.on_ground = False
        self.form_cooldown = False
        self.form_cooldown_timer = 0
        self.health = 3
        self.invincible_timer = 0
        self.score = 0

    def update_image(self):
        if self.form == "light":
            self.image.fill(WHITE)
            pygame.draw.circle(self.image, BLACK, (8, 10), 3)
            pygame.draw.circle(self.image, BLACK, (22, 10), 3)
        else:
            self.image.fill(BLACK)
            pygame.draw.circle(self.image, WHITE, (8, 10), 3)
            pygame.draw.circle(self.image, WHITE, (22, 10), 3)

    def switch_form(self):
        if self.form_cooldown:
            return
        self.form = "shadow" if self.form == "light" else "light"
        self.update_image()
        self.form_cooldown = True
        self.form_cooldown_timer = pygame.time.get_ticks()
        return True

    def update(self, keys):
        # Horizontal movement
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -self.speed
        if keys[pygame.K_RIGHT]:
            self.vel_x = self.speed
        self.rect.x += self.vel_x

        # Apply gravity
        self.vel_y += self.gravity
        self.rect.y += self.vel_y

        # Ground collision
        if self.rect.bottom >= GROUND_HEIGHT:
            self.rect.bottom = GROUND_HEIGHT
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = self.jump_power

        # Form switching (E key)
        if keys[pygame.K_e] and not self.form_cooldown:
            self.switch_form()

        # Cooldown timer
        if self.form_cooldown and pygame.time.get_ticks() - self.form_cooldown_timer > 500:
            self.form_cooldown = False

        # Invincibility frames
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Screen boundaries
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def take_damage(self):
        if self.invincible_timer <= 0:
            self.health -= 1
            self.invincible_timer = 60

    def draw(self, screen):
        if self.invincible_timer > 0 and (self.invincible_timer // 5) % 2 == 0:
            return
        screen.blit(self.image, self.rect)

# ----------------------------------------------------------------------
# Platforms (form-specific)
# ----------------------------------------------------------------------
class LightPlatform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(WHITE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.form_required = "light"

class ShadowPlatform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.form_required = "shadow"

# ----------------------------------------------------------------------
# Moving Platform
# ----------------------------------------------------------------------
class MovingPlatform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, move_range, speed, axis='x', form_required=None):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.start_x = x
        self.start_y = y
        self.move_range = move_range
        self.speed = speed
        self.axis = axis
        self.direction = 1
        self.form_required = form_required

    def update(self):
        if self.axis == 'x':
            self.rect.x += self.speed * self.direction
            if abs(self.rect.x - self.start_x) >= self.move_range:
                self.direction *= -1
        else:
            self.rect.y += self.speed * self.direction
            if abs(self.rect.y - self.start_y) >= self.move_range:
                self.direction *= -1

    def is_visible(self, player_form):
        return self.form_required is None or player_form == self.form_required

# ----------------------------------------------------------------------
# Pressure Plate (triggers doors)
# ----------------------------------------------------------------------
class PressurePlate(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, required_form, door):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.required_form = required_form
        self.door = door
        self.activated = False

    def update(self, player):
        if not self.activated and self.rect.colliderect(player.rect) and player.form == self.required_form:
            self.activated = True
            self.door.open()
            self.image.fill(GREEN)

class Door(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((139, 69, 19))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.is_open = False

    def open(self):
        self.is_open = True
        self.image.fill(GREEN)

    def can_pass(self):
        return self.is_open

# ----------------------------------------------------------------------
# Hazards (pools that damage if same form)
# ----------------------------------------------------------------------
class Hazard(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, hazard_type):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.hazard_type = hazard_type
        if hazard_type == "light":
            self.image.fill((255, 255, 150))
        else:
            self.image.fill((50, 50, 80))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def damage_player(self, player):
        if player.form == self.hazard_type:
            player.take_damage()
            return True
        return False

# ----------------------------------------------------------------------
# Orbs (collectibles)
# ----------------------------------------------------------------------
class Orb(pygame.sprite.Sprite):
    def __init__(self, x, y, orb_type):
        super().__init__()
        self.orb_type = orb_type
        self.image = pygame.Surface((15, 15))
        if orb_type == "light":
            self.image.fill(YELLOW)
        else:
            self.image.fill(MAGENTA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def collect(self, player):
        if player.form == self.orb_type:
            player.score += 10
            return True
        return False

# ----------------------------------------------------------------------
# Enemy (vulnerable only in specific form)
# ----------------------------------------------------------------------
class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, vulnerable_form):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vulnerable_form = vulnerable_form
        self.speed = 2
        self.direction = 1
        self.move_left = x - 50
        self.move_right = x + 50

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.x <= self.move_left or self.rect.x >= self.move_right:
            self.direction *= -1

    def damage_player(self, player):
        if player.form != self.vulnerable_form:
            player.take_damage()
            return False
        else:
            self.kill()
            player.score += 20
            return True

# ----------------------------------------------------------------------
# Game class
# ----------------------------------------------------------------------
class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Echoes of the Unseen")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.big_font = pygame.font.Font(None, 72)
        self.state = MENU
        self.particle_system = ParticleSystem()

    def new_game(self):
        self.player = Player(100, GROUND_HEIGHT - 50)
        self.all_sprites = pygame.sprite.Group()
        self.platforms = pygame.sprite.Group()
        self.moving_platforms = pygame.sprite.Group()
        self.hazards = pygame.sprite.Group()
        self.orbs = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.pressure_plates = pygame.sprite.Group()
        self.doors = pygame.sprite.Group()

        # Create level elements
        light_plat = LightPlatform(200, GROUND_HEIGHT - 80, 100, 20)
        shadow_plat = ShadowPlatform(400, GROUND_HEIGHT - 120, 100, 20)
        light_plat2 = LightPlatform(600, GROUND_HEIGHT - 150, 80, 20)
        shadow_plat2 = ShadowPlatform(800, GROUND_HEIGHT - 100, 100, 20)

        moving_plat = MovingPlatform(300, GROUND_HEIGHT - 200, 80, 20, 150, 2, axis='x', form_required='light')
        self.moving_platforms.add(moving_plat)

        door = Door(850, GROUND_HEIGHT - 50, 40, 50)
        pressure = PressurePlate(700, GROUND_HEIGHT - 30, 40, 10, 'light', door)
        self.doors.add(door)
        self.pressure_plates.add(pressure)

        hazard_light = Hazard(500, GROUND_HEIGHT - 20, 60, 20, "light")
        hazard_shadow = Hazard(650, GROUND_HEIGHT - 20, 60, 20, "shadow")
        self.hazards.add(hazard_light, hazard_shadow)

        orb1 = Orb(250, GROUND_HEIGHT - 100, "light")
        orb2 = Orb(450, GROUND_HEIGHT - 140, "shadow")
        orb3 = Orb(750, GROUND_HEIGHT - 70, "light")
        self.orbs.add(orb1, orb2, orb3)

        enemy = Enemy(550, GROUND_HEIGHT - 40, 30, 30, "shadow")
        self.enemies.add(enemy)

        self.platforms.add(light_plat, shadow_plat, light_plat2, shadow_plat2)
        self.all_sprites.add(self.player, light_plat, shadow_plat, light_plat2, shadow_plat2,
                             moving_plat, door, pressure, hazard_light, hazard_shadow,
                             orb1, orb2, orb3, enemy)

        self.camera_x = 0
        self.score = 0
        self.game_over = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if self.state == MENU and event.key == pygame.K_SPACE:
                    self.state = PLAYING
                    self.new_game()
                elif self.state == GAME_OVER and event.key == pygame.K_SPACE:
                    self.state = MENU
                elif self.state == PLAYING and event.key == pygame.K_ESCAPE:
                    self.state = MENU
        return True

    def update(self):
        if self.state != PLAYING:
            return

        keys = pygame.key.get_pressed()
        old_form = self.player.form
        self.player.update(keys)

        if old_form != self.player.form:
            color = WHITE if self.player.form == "light" else BLACK
            self.particle_system.emit(self.player.rect.centerx, self.player.rect.centery, color, 20)

        self.particle_system.update()
        self.moving_platforms.update()
        self.enemies.update()

        for plate in self.pressure_plates:
            plate.update(self.player)

        # Platform collision (only visible in current form)
        all_platforms = pygame.sprite.Group()
        for plat in self.platforms:
            if plat.form_required == self.player.form:
                all_platforms.add(plat)
        for plat in self.moving_platforms:
            if plat.is_visible(self.player.form):
                all_platforms.add(plat)

        # Vertical collision
        self.player.rect.y += 1
        hits = pygame.sprite.spritecollide(self.player, all_platforms, False)
        self.player.rect.y -= 1
        if hits:
            self.player.rect.bottom = hits[0].rect.top
            self.player.vel_y = 0
            self.player.on_ground = True

        # Horizontal collision
        self.player.rect.x += self.player.vel_x
        hits = pygame.sprite.spritecollide(self.player, all_platforms, False)
        if hits:
            if self.player.vel_x > 0:
                self.player.rect.right = hits[0].rect.left
            elif self.player.vel_x < 0:
                self.player.rect.left = hits[0].rect.right
            self.player.vel_x = 0

        for hazard in self.hazards:
            if self.player.rect.colliderect(hazard.rect):
                hazard.damage_player(self.player)

        for orb in self.orbs:
            if self.player.rect.colliderect(orb.rect):
                if orb.collect(self.player):
                    orb.kill()
                    self.player.score += 10

        for enemy in self.enemies:
            if self.player.rect.colliderect(enemy.rect):
                enemy.damage_player(self.player)

        for door in self.doors:
            if door.can_pass() and self.player.rect.colliderect(door.rect):
                self.state = GAME_OVER

        if self.player.health <= 0:
            self.state = GAME_OVER

    def draw_background(self):
        if self.player.form == "light":
            bg_color = LIGHT_BLUE
        else:
            bg_color = DARK_PURPLE
        self.screen.fill(bg_color)
        pygame.draw.rect(self.screen, (34, 139, 34), (0, GROUND_HEIGHT, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_HEIGHT))
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(self.screen, (0, 100, 0), (x, GROUND_HEIGHT), (x, GROUND_HEIGHT + 10), 2)

    def draw_hud(self):
        for i in range(self.player.health):
            pygame.draw.rect(self.screen, RED, (10 + i*30, 10, 25, 25))
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 50))
        form_text = self.font.render(f"Form: {self.player.form.upper()}", True, WHITE)
        self.screen.blit(form_text, (10, 90))
        controls = self.font.render("← →  SPACE  |  E = Switch Form  |  ESC = Menu", True, WHITE)
        self.screen.blit(controls, (10, SCREEN_HEIGHT - 30))

    def draw_menu(self):
        self.screen.fill(DARK_PURPLE)
        title = self.big_font.render("ECHOES OF THE UNSEEN", True, WHITE)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 150))
        self.screen.blit(title, title_rect)
        instructions = [
            "A game of Light and Shadow",
            "",
            "Switch forms (E) to see hidden platforms",
            "Avoid hazards that match your form",
            "Collect orbs of the same form for points",
            "Defeat enemies in their vulnerable form",
            "",
            "Press SPACE to start"
        ]
        y = 250
        for line in instructions:
            text = self.font.render(line, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, y))
            self.screen.blit(text, text_rect)
            y += 40

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        game_over = self.big_font.render("GAME OVER", True, RED)
        game_over_rect = game_over.get_rect(center=(SCREEN_WIDTH//2, 200))
        self.screen.blit(game_over, game_over_rect)
        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, 300))
        self.screen.blit(score_text, score_rect)
        restart = self.font.render("Press SPACE to return to menu", True, WHITE)
        restart_rect = restart.get_rect(center=(SCREEN_WIDTH//2, 400))
        self.screen.blit(restart, restart_rect)

    def draw(self):
        if self.state == MENU:
            self.draw_menu()
        elif self.state == PLAYING:
            self.draw_background()
            self.platforms.draw(self.screen)
            self.moving_platforms.draw(self.screen)
            self.hazards.draw(self.screen)
            self.orbs.draw(self.screen)
            self.enemies.draw(self.screen)
            self.pressure_plates.draw(self.screen)
            self.doors.draw(self.screen)
            self.player.draw(self.screen)
            self.particle_system.draw(self.screen)
            self.draw_hud()
        elif self.state == GAME_OVER:
            self.draw_background()
            self.draw_game_over()

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()