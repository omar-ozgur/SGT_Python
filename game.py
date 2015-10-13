import pygame
import ctypes
import time
import random
import sys
from AppKit import NSScreen

# Create a class to save screen variables
if sys.platform == 'win32':
    class Screen:
        user32 = ctypes.windll.user32
        width = user32.GetSystemMetrics(0)
        height = user32.GetSystemMetrics(1)
else:
    class Screen:
        width = NSScreen.mainScreen().frame().size.width
        height = NSScreen.mainScreen().frame().size.height

class Window:
    width = Screen.width / 2
    height = Screen.height / 3

class Sound:
    pygame.mixer.pre_init(44000, -16, 2, 2048)
    pygame.mixer.init()

    musicPlaying = False
    muted = False
    muteButton = False

    pygame.mixer.music.load('sounds/music.ogg')
    pygame.mixer.music.set_volume(0.2)
    hit = pygame.mixer.Sound('sounds/hit.wav')
    jump = pygame.mixer.Sound('sounds/jump.wav')

class Obstacle:
    def __init__(self):
        self.image = pygame.image.load("images/obstacle.png")
        self.obj = self.image.get_rect()

class Background:
    def __init__(self):
        self.image = pygame.image.load("images/background.png")
        self.obj = self.image.get_rect()

class Floor:
    def __init__(self):
        self.grassImage = pygame.image.load("images/grass.png")
        self.dirtImage = pygame.image.load("images/dirt.png")
        self.isDirt = True
        self.dirtObj = self.dirtImage.get_rect()
        self.grassObj = self.grassImage.get_rect()

class Player:
    image = pygame.image.load("images/player.png")
    obj = image.get_rect()
    obj.left = Window.width / 2 - Window.width / 5

class Env:
    backgroundImage = pygame.image.load("images/background.png")
    backgroundObj = backgroundImage.get_rect()

    obstacles = []
    floorTiles = []
    backgroundTiles = []

    # "Public" variables
    speed = 7
    backgroundSpeed = speed / 2
    scoreSpeed = 1
    acceleration = 0.005
    gravity = 7000
    jumpHeight = 1500
    floorHeight = 7
    maxObstacleHeight = 5
    minSpawnTime = 0.5

    # "Private" variables
    startY = 0
    startJump = time.time()
    floorWidth = 0
    backgroundWidth = 0
    lastSpawn = time.time()
    startSpeed = speed
    score = 0
    highScore = 0
    timeScale = 1
    canSpawn = True
    white = 255, 255, 255
    fontSize = Window.width / 20
    smallFontSize = Window.width / 40
    fontMargin = 32

# The main game class
class Game:

    # Initialize variables
    def __init__(self):
        self.running = True
        self.window = None
        self.floor = Floor()
        self.size = self.width, self.height = Window.width, Window.height
        self.clock = pygame.time.Clock()
 
    # Initialize pygame
    def on_init(self):
        pygame.init()
        self.window = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        self.running = True
        self.font = pygame.font.SysFont("monospace", Env.fontSize)
        self.smallFont = pygame.font.SysFont("monospace", Env.smallFontSize)

    def reset(self):

        # Reset variables
        Env.speed = 0.0
        Env.score = 0
        Env.timeScale = 0
        Env.floorWidth = 0
        Env.obstacles = []
        Env.floorTiles = []
        Env.backgroundTiles = []
        Env.backgroundWidth = 0
        Env.startY = Window.height - (self.floor.dirtObj.height * (Env.floorHeight + 1))
        Player.obj.bottom = Env.startY

        # Create the floor
        self.createFloor()

        # Create the background
        self.createBackground()
 
    # Deal with events (key presses)
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:

            # "m" pressed
            if event.key == 109:
                if Sound.musicPlaying:
                    pygame.mixer.music.pause()
                    Sound.musicPlaying = False
                    Sound.muted = True
                else:
                    pygame.mixer.music.play(-1)
                    Sound.musicPlaying = True
                    Sound.muted = False

            # "space" pressed
            elif event.key == 32:

                # Start the game if it was stopped
                if Env.timeScale == 0:
                    Env.timeScale = 1
                    Env.speed = Env.startSpeed

                # Make the player jump
                else:

                    # Play jump sound effect
                    if Sound.muted == False:
                        Sound.jump.play()

                    if Player.obj.bottom >= Env.startY:
                    
                        # Set the time that the jump started
                        Env.startJump = time.time()

                        # Move the player off of the ground
                        Player.obj.bottom -= 1

    # Update game variables
    def on_loop(self):
        if Sound.musicPlaying == False and Sound.muted == False and pygame.mixer.get_init() != None:
            pygame.mixer.music.play(-1) 
            Sound.musicPlaying = True

        # Increase the score and speed
        Env.score += Env.scoreSpeed * Env.timeScale

        # Change the high score if needed
        if Env.score > Env.highScore:
            Env.highScore = Env.score

        if Env.score % 200 == 0 and Env.timeScale > 0:
            Env.speed += 1

        if Player.obj.bottom < Env.startY:
            Player.obj.bottom = (0.5 * Env.gravity * ((time.time() - Env.startJump) ** 2)) - Env.jumpHeight * (time.time() - Env.startJump) + (Env.startY - 1)
    
        # If the player is not in the air, set it on the ground
        else:
            Player.obj.bottom = Env.startY

        # Check collisions
        self.checkCollisions()

        self.createObstacles()

        # Delete obstacles if they go out of bounds
        for i in range(len(Env.obstacles)):
            if Env.obstacles[i].obj.right - Env.obstacles[i].obj.width / 2 <= 0:
                del Env.obstacles[i]
                break

    # Render the game
    def on_render(self):

        # Clear the screen
        self.window.fill(Env.white)

        # Draw the background
        for  i in range(len(Env.backgroundTiles)):
            Env.backgroundTiles[i].obj.left -= Env.backgroundSpeed;
            self.window.blit(Env.backgroundTiles[i].image, Env.backgroundTiles[i].obj)

            # Reset tile position if it goes out of bounds
            if Env.backgroundTiles[i].obj.left + Env.backgroundObj.width < 0:
                Env.backgroundTiles[i].obj.left += Env.backgroundWidth * Env.backgroundObj.width

        # Draw the floor
        for i in range(len(Env.floorTiles)):

            # Draw dirt tile
            if Env.floorTiles[i].isDirt:
                # Reset tile position if it goes out of bounds
                if Env.floorTiles[i].dirtObj.left + Env.floorTiles[i].dirtObj.width < 0:
                    Env.floorTiles[i].dirtObj.left += Env.floorWidth * Env.floorTiles[i].dirtObj.width
                Env.floorTiles[i].dirtObj.left -= Env.speed
                self.window.blit(Env.floorTiles[i].dirtImage, Env.floorTiles[i].dirtObj)

            # Draw grass tile
            else:
                if Env.floorTiles[i].grassObj.left + Env.floorTiles[i].grassObj.width < 0:
                    Env.floorTiles[i].grassObj.left += Env.floorWidth * Env.floorTiles[i].grassObj.width;
                Env.floorTiles[i].grassObj.left -= Env.speed
                self.window.blit(Env.floorTiles[i].grassImage, Env.floorTiles[i].grassObj)

        # Draw obstacles
        for i in range(len(Env.obstacles)):

            # Draw obstacle
            self.window.blit(Env.obstacles[i].image, Env.obstacles[i].obj)

            # Constantly move obstacle to the left
            Env.obstacles[i].obj.left -= Env.speed

        self.window.blit(Player.image, Player.obj)

        self.drawText()

        pygame.display.flip()

    # Cleanup variables
    def on_cleanup(self):
        pygame.quit()

    def drawText(self):
        score = self.font.render("Score: " + str(int(Env.score)), 1, (0,0,0))
        self.window.blit(score, (Env.fontMargin, Env.fontMargin))

        highScore = self.font.render("High Score: " + str(int(Env.highScore)), 1, (0,0,0))
        self.window.blit(highScore, (Window.width - highScore.get_rect().width - Env.fontMargin, Env.fontMargin))

        if Env.timeScale == 0:
            start = self.font.render("Press Space To Start", 1, (0,0,0))
            self.window.blit(start, (Window.width / 2 - start.get_rect().width / 2, Window.height / 2 - start.get_rect().height / 2))

        mute = self.smallFont.render("Press 'm' to mute", 1, (0,0,0))
        self.window.blit(mute, (Env.fontMargin, Window.height - Env.fontMargin))

    def checkCollisions(self):
        # Check for collisions with any obstacle
        for i in range(len(Env.obstacles)):

            # Reset the game if a collision was detected
            if Player.obj.colliderect(Env.obstacles[i].obj):
                if Sound.muted == False:
                    Sound.hit.play()

                self.reset()
                break

    def createFloor(self):

        # Set floor width and height
        width = Window.width + self.floor.dirtObj.width
        height = Env.floorHeight

        while height > -self.floor.dirtObj.height:
            while width >= -self.floor.dirtObj.width:

                # Create grass tiles
                if height == Env.floorHeight:

                    # Create new grass object
                    newGrass = Floor()

                    # Set grass variables
                    newGrass.grassObj.left = width
                    newGrass.grassObj.bottom = Window.height - height * self.floor.grassObj.height
                    newGrass.isDirt = False

                    # Push the grass tile to the floor tiles array
                    Env.floorTiles.append(newGrass)

                    # Get ready to place the next tile to the left
                    width -= self.floor.grassObj.width

                    # floorWidth will tell how many tiles are in one row of the floor
                    Env.floorWidth = Env.floorWidth + 1

                # Create dirt tiles
                else:

                    # Create new dirt object
                    newDirt = Floor()

                    # Set dirt variables
                    newDirt.dirtObj.left = width
                    newDirt.dirtObj.bottom = Window.height - height * self.floor.dirtObj.height

                    # Push the dirt tile to the floor tiles array
                    Env.floorTiles.append(newDirt)

                    # Get ready to place the next tile to the left
                    width -= self.floor.dirtObj.width

            # Reset the horizontal tile position
            width = Window.width + self.floor.dirtObj.width

            # Move on to the next row
            height = height - 1

    def createObstacles(self):

        # Create random obstacles
        newObstacle = Obstacle()
        if time.time() - Env.lastSpawn > Env.minSpawnTime and random.random() > 0.98 and Env.timeScale > 0:

            # Save the time that the obstacle was created
            Env.lastSpawn = time.time()

            # Create a new obstacle
            newObstacle = Obstacle()
            newObstacle.obj.left = Window.width
            newObstacle.obj.bottom = Env.startY
            Env.obstacles.append(newObstacle)

            # Randomly create obstacles on top of the initial obstacle
            for i in range(Env.maxObstacleHeight - 1):
                if random.random() > 0.7:

                    # Save position of previous obstacle
                    lastX = newObstacle.obj.left
                    lastY = newObstacle.obj.bottom

                    # Create a new obstacle on top of the previous obstacle
                    newObstacle = Obstacle()
                    newObstacle.obj.left = lastX
                    newObstacle.obj.bottom = lastY - newObstacle.obj.height
                    Env.obstacles.append(newObstacle)

            # Randomly create a new stack of obstacles next to the previous stack
            if random.random() > 0.5:

                # Create a new obstacle
                newObstacle = Obstacle()
                newObstacle.obj.left = Window.width + newObstacle.obj.width
                newObstacle.obj.bottom = Env.startY
                Env.obstacles.append(newObstacle)

                # Randomly create obstacles on top of the initial obstacle
                for i in range(Env.maxObstacleHeight - 1):
                    if random.random() > 0.7:

                        # Save position of previous obstacle
                        lastX = newObstacle.obj.left
                        lastY = newObstacle.obj.bottom

                        # Create a new obstacle on top of the previous obstacle
                        newObstacle = Obstacle()
                        newObstacle.obj.left = lastX
                        newObstacle.obj.bottom = lastY - newObstacle.obj.height
                        Env.obstacles.append(newObstacle)

    def createBackground(self):
        backgroundWidth = 0

        # Set floor width and height
        width = Window.width + Env.backgroundObj.width

        while width >= -Env.backgroundObj.width:

            newBackground = Background()

            # Set background variables
            newBackground.obj.left = width
            newBackground.obj.top = 0

            # Push the background tile to the floor tiles array
            Env.backgroundTiles.append(newBackground)

            # Get ready to place the next tile to the left
            width -= Env.backgroundObj.width

            # Keep track of number of background tiles used
            Env.backgroundWidth += 1
 
    # Start the main game loop
    def on_execute(self):
        if self.on_init() == False:
            self.running = False

        self.reset()
 
        # Main game loop
        while( self.running ):

            # For each iteration, deal with events, then update variables, then render the game
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()

        # Cleanup the game
        self.on_cleanup()
 
if __name__ == "__main__" :
    game = Game()
    game.on_execute()