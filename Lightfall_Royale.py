import pygame
import sys
import math
import random

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Lightfall Royale - Light Capture Duel")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PLAYER_SIZE = 30
PLAYER_SPEED = 5
BULLET_SIZE = 10
BULLET_SPEED = 8
MAX_RADIANCE = 100
RADIANCE_REGEN_RATE = 0.5

# --- Classes for Game Objects ---

class Player:
    def __init__(self, x, y, color, player_id):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.color = color
        self.id = player_id
        self.radiance = 50
        self.radiance_regen_cooldown = 0

    def update(self, keys, walls):
        # Movement
        dx, dy = 0, 0
        if keys[pygame.K_LEFT]:
            dx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            dx = PLAYER_SPEED
        if keys[pygame.K_UP]:
            dy = -PLAYER_SPEED
        if keys[pygame.K_DOWN]:
            dy = PLAYER_SPEED
        
        # Move and check collision with walls
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.x -= dx
                break
        
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.y -= dy
                break

        # Radiance regen
        if self.radiance_regen_cooldown > 0:
            self.radiance_regen_cooldown -= 1
        elif self.radiance < MAX_RADIANCE:
            self.radiance += RADIANCE_REGEN_RATE
            self.radiance = min(self.radiance, MAX_RADIANCE)

        # Keep on screen
        self.rect.clamp_ip(screen.get_rect())

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        # Radiance bar
        bar_width = (self.radiance / MAX_RADIANCE) * PLAYER_SIZE
        pygame.draw.rect(screen, YELLOW, (self.rect.x, self.rect.y - 10, bar_width, 5))
        pygame.draw.rect(screen, WHITE, (self.rect.x, self.rect.y - 10, PLAYER_SIZE, 5), 1)

class LightBullet:
    def __init__(self, x, y, direction, owner_id):
        self.rect = pygame.Rect(x, y, BULLET_SIZE, BULLET_SIZE)
        self.direction = direction
        self.owner_id = owner_id
        self.speed = BULLET_SPEED

    def update(self):
        self.rect.x += self.direction[0] * self.speed
        self.rect.y += self.direction[1] * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, YELLOW, self.rect.center, BULLET_SIZE // 2)

class Wall:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)

    def draw(self, screen):
        pygame.draw.rect(screen, DARK_GRAY, self.rect)

# --- AI for Single-Player Mode ---
class AIPlayer:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.radiance = 50
        self.radiance_regen_cooldown = 0

    def update(self, target_rect, walls, bullets):
        # Move towards player
        dx = target_rect.centerx - self.rect.centerx
        dy = target_rect.centery - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist != 0:
            dx = dx / dist * PLAYER_SPEED
            dy = dy / dist * PLAYER_SPEED
        
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.x -= dx
                break
        
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                self.rect.y -= dy
                break

        # AI shooting
        if random.random() < 0.02:
            direction = (target_rect.centerx - self.rect.centerx, target_rect.centery - self.rect.centery)
            dist = math.hypot(direction[0], direction[1])
            if dist != 0:
                direction = (direction[0] / dist, direction[1] / dist)
                bullets.append(LightBullet(self.rect.centerx, self.rect.centery, direction, "ai"))

        # Radiance regen
        if self.radiance_regen_cooldown > 0:
            self.radiance_regen_cooldown -= 1
        elif self.radiance < MAX_RADIANCE:
            self.radiance += RADIANCE_REGEN_RATE
            self.radiance = min(self.radiance, MAX_RADIANCE)

        self.rect.clamp_ip(screen.get_rect())

    def draw(self, screen):
        pygame.draw.rect(screen, BLUE, self.rect)
        bar_width = (self.radiance / MAX_RADIANCE) * PLAYER_SIZE
        pygame.draw.rect(screen, YELLOW, (self.rect.x, self.rect.y - 10, bar_width, 5))
        pygame.draw.rect(screen, WHITE, (self.rect.x, self.rect.y - 10, PLAYER_SIZE, 5), 1)

# --- Helper Functions ---
def handle_collisions(players, bullets, walls):
    for bullet in bullets[:]:
        if not screen.get_rect().colliderect(bullet.rect):
            bullets.remove(bullet)
            continue
        
        for wall in walls:
            if bullet.rect.colliderect(wall):
                bullets.remove(bullet)
                break
        
        for player in players:
            if bullet.rect.colliderect(player.rect) and bullet.owner_id != player.id:
                steal = 10
                player.radiance -= steal
                for p in players:
                    if p.id == bullet.owner_id:
                        p.radiance += steal
                        p.radiance = min(p.radiance, MAX_RADIANCE)
                        p.radiance_regen_cooldown = 30
                bullets.remove(bullet)
                break

def draw_ui(players, score_display_timer):
    for i, p in enumerate(players):
        text = font.render(f"P{p.id+1} Radiance: {int(p.radiance)}", True, p.color)
        screen.blit(text, (10, 10 + i * 30))
    if score_display_timer > 0:
        score_text = font.render("+10 Radiance Stolen!", True, YELLOW)
        text_rect = score_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        screen.blit(score_text, text_rect)

def game_mode_selection():
    selection = "menu"
    while selection == "menu":
        screen.fill(BLACK)
        title = font.render("Lightfall Royale - Capture the Light", True, YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, 100))
        screen.blit(title, title_rect)
        
        ai_text = font.render("1. Single Player (vs AI)", True, WHITE)
        ai_rect = ai_text.get_rect(center=(SCREEN_WIDTH//2, 200))
        screen.blit(ai_text, ai_rect)
        
        multi_text = font.render("2. Two Player (Local Co-op)", True, WHITE)
        multi_rect = multi_text.get_rect(center=(SCREEN_WIDTH//2, 250))
        screen.blit(multi_text, multi_rect)
        
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "ai"
                if event.key == pygame.K_2:
                    return "two_player"
        clock.tick(60)
    return None

# --- Main Game Function ---
def main():
    mode = game_mode_selection()
    if mode is None:
        return
    
    players = []
    bullets = []
    walls = [
        Wall(200, 150, 20, 300),
        Wall(600, 200, 20, 300),
        Wall(300, 400, 200, 20),
    ]
    
    if mode == "two_player":
        players.append(Player(100, 300, RED, 0))
        players.append(Player(700, 300, BLUE, 1))
        ai = None
    else:
        players.append(Player(100, 300, RED, 0))
        ai = AIPlayer(700, 300)
    
    running = True
    score_display_timer = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    direction = (1, 0)
                    bullets.append(LightBullet(players[0].rect.centerx, players[0].rect.centery, direction, players[0].id))
        
        keys = pygame.key.get_pressed()
        
        if mode == "two_player":
            p1_keys = {
                pygame.K_LEFT: keys[pygame.K_LEFT],
                pygame.K_RIGHT: keys[pygame.K_RIGHT],
                pygame.K_UP: keys[pygame.K_UP],
                pygame.K_DOWN: keys[pygame.K_DOWN]
            }
            players[0].update(p1_keys, walls)
            p2_keys = {
                pygame.K_a: keys[pygame.K_a],
                pygame.K_d: keys[pygame.K_d],
                pygame.K_w: keys[pygame.K_w],
                pygame.K_s: keys[pygame.K_s]
            }
            players[1].update(p2_keys, walls)
        else:
            players[0].update(keys, walls)
            if ai:
                ai.update(players[0].rect, walls, bullets)
        
        for bullet in bullets[:]:
            bullet.update()
        
        if mode == "two_player":
            handle_collisions(players, bullets, walls)
        else:
            if ai:
                handle_collisions(players, bullets, walls)
                for bullet in bullets[:]:
                    if ai.rect.colliderect(bullet.rect) and bullet.owner_id != "ai":
                        steal = 10
                        ai.radiance -= steal
                        for p in players:
                            if p.id == bullet.owner_id:
                                p.radiance += steal
                                p.radiance = min(p.radiance, MAX_RADIANCE)
                                p.radiance_regen_cooldown = 30
                        bullets.remove(bullet)
                        score_display_timer = 30
                    elif bullet.rect.colliderect(players[0].rect) and bullet.owner_id == "ai":
                        steal = 10
                        players[0].radiance -= steal
                        ai.radiance += steal
                        ai.radiance = min(ai.radiance, MAX_RADIANCE)
                        ai.radiance_regen_cooldown = 30
                        bullets.remove(bullet)
                        score_display_timer = 30
        
        # Drawing
        screen.fill(BLACK)
        for wall in walls:
            wall.draw(screen)
        for player in players:
            player.draw(screen)
        if ai:
            ai.draw(screen)
        for bullet in bullets:
            bullet.draw(screen)
        
        if mode == "two_player":
            draw_ui(players, score_display_timer)
        else:
            draw_ui(players, score_display_timer)
            if ai:
                ai_text = font.render(f"AI Radiance: {int(ai.radiance)}", True, BLUE)
                screen.blit(ai_text, (10, 70))
        
        if score_display_timer > 0:
            score_display_timer -= 1
        
        # Win conditions
        if mode == "two_player":
            if players[0].radiance <= 0:
                win = font.render("Player 2 Wins!", True, BLUE)
                screen.blit(win, (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
            elif players[1].radiance <= 0:
                win = font.render("Player 1 Wins!", True, RED)
                screen.blit(win, (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
        else:
            if players[0].radiance <= 0:
                win = font.render("AI Wins!", True, BLUE)
                screen.blit(win, (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
            elif ai and ai.radiance <= 0:
                win = font.render("Player Wins!", True, RED)
                screen.blit(win, (SCREEN_WIDTH//2 - 50, SCREEN_HEIGHT//2))
                pygame.display.flip()
                pygame.time.wait(2000)
                running = False
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()