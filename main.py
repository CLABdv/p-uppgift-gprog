#!/usr/bin/python
import pygame
import pygame.freetype
import random
import sys
import numpy as np


class Button:
    # if you're using create_button_surface just call with position = (0,0) or something
    def __init__(self, position, name, font, action):
        self.position = position
        text_surf, rect = font.render(name, (0, 0, 0))
        (_, _, w, h) = rect
        w = w + 2
        h = h + 2
        (x, y) = position
        self.rect = pygame.Rect(x, y, w, h)
        self.surface = pygame.Surface((w, h))
        self.surface.fill((255, 255, 255))
        self.surface.blit(text_surf, (1, 1))
        # action is function pointer to function to perform onclick
        self.action = action

    def onclick(self, mousepos):
        if self.rect.collidepoint(mousepos):
            self.action()


def set_button_positions(buttons, spacing, topleft):
    wsum = 0
    for i in range(len(buttons)):
        position = (topleft[0] + wsum, topleft[1])
        buttons[i].position = position
        buttons[i].rect.x = position[0]
        buttons[i].rect.y = position[1]
        wsum += buttons[i].rect.w + 20


class Textbox:
    def __init__(self, position, max_width, tag, font, onlynum):
        self.position = position
        self.tag = tag
        self.font = font
        self.current_text = ""
        text_surf, rect = font.render(tag, (0, 0, 0))
        (_, _, _, h) = rect
        w = max_width
        h = h + 2
        (x, y) = position
        self.rect = pygame.Rect(x, y, w, h)
        self.surface = pygame.Surface((w, h))
        self.surface.fill((180, 180, 180))
        self.surface.blit(text_surf, (1, 1))
        self.selected = False
        self.onlynum = onlynum

    def handle_inp(self, key):
        if (not self.selected):
            return
        if (key == pygame.K_BACKSPACE):
            self.current_text = self.current_text[:-1]
            return
        if (key == pygame.K_ESCAPE):
            self.selected = False
            return
        tmp = ""
        try:
            tmp = chr(key)
        except:
            pass
        if (tmp.isnumeric()):
            self.current_text += tmp
        if (not self.onlynum and tmp.isalpha()):
            self.current_text += tmp

    def update_surf(self):
        text_surf, _ = self.font.render(
            self.tag + self.current_text, (0, 0, 0))
        if (self.selected):
            self.surface.fill((255, 255, 255))
        else:
            self.surface.fill((190, 190, 190))
        self.surface.blit(text_surf, (1, 1))


class Game:
    def __init__(self, board, font, background_colour):
        pygame.init()
        self.font = font
        self.board = board
        self.board_next_state = 0
        self.window = pygame.display.set_mode(
            (800, 1000))
        pygame.display.set_caption("Livet hos matematiska organismer")
        self.w, self.h = pygame.display.get_surface().get_size()
        self.surface = pygame.Surface((board.side, board.side))
        self.scale_factor = min(self.w, self.h) // board.side
        self.to_be_blitted = pygame.Surface(
            (board.side*self.scale_factor, board.side*self.scale_factor))
        self.clock = pygame.time.Clock()
        self.ticks = 0
        self.paused = False
        self.background_colour = background_colour

        # this prevents us from manually needing to set all the positions
        tmp = (0, 0)

        # set up buttons
        def pause():
            self.paused = not self.paused
        pause_button = Button(
            tmp, "Pause  Play", font, pause)

        def clear():
            self.board.state = 0
        clear_button = Button(tmp, "Clear", font, clear)

        def manual_next():
            self.next_board()
        manual_next_button = Button(
            tmp, "Next", font, manual_next)

        def save():
            file = open("savefile", "wb")
            file.write(self.board.state . to_bytes(
                board.side * (board.side // 8 + 1), byteorder="little"))
            file.close
        save_button = Button(tmp, "Save", font, save)

        def load():
            try:
                file = open("savefile", "rb")
                data = file.read()
                board.state = int.from_bytes(data, byteorder="little")
                file.close()
            except:
                board.state = 0
        load_button = Button(tmp, "Load", font, load)

        def randstate():
            self.board.state = random.randint(0, 2**(self.board.side*self.board.side))
        rand_button = Button(tmp, "Random", font, randstate)
        self.buttons = [pause_button,
                        clear_button, manual_next_button, save_button, load_button, rand_button]
        set_button_positions(self.buttons,
                             20, (20, self.board.side*self.scale_factor + 20))

        self.textbox = Textbox(
            (20, self.board.side*self.scale_factor + 50), self.board.side*self.scale_factor - 40, "Generations  between  draw  ", font, True)

    def next_board(self):
        generations = 1
        try:
            generations = int(self.textbox.current_text)
        except:
            pass
        mask_getter = self.board.state
        to_be_iterated = self.board.state
        for i in range(generations):
            # untouched during the loop, we need for alive_next
            tmp_state = to_be_iterated
            while (mask_getter):
                rightmost_bit = mask_getter & (~mask_getter + 1)
                # number of trailing 0's
                idx = (rightmost_bit - 1).bit_count()
                # makes the adjacent bits set, this is since these bits may change
                to_be_iterated |= self.board.lookup[idx]
                # painting here since we know that this bit was set last gen
                # (our drawing is kinda delayed with one generation)
                mask_getter &= ~rightmost_bit
            while (to_be_iterated):
                rightmost_bit = to_be_iterated & (~to_be_iterated + 1)
                idx = (rightmost_bit - 1).bit_count()
                if (alive_next(tmp_state, self.board.lookup, idx)):
                    self.board_next_state |= rightmost_bit
                to_be_iterated &= ~rightmost_bit
            mask_getter = self.board_next_state
            to_be_iterated = mask_getter
            self.board_next_state = 0
        self.board.state = mask_getter

    # the draw logic is kinda intermixed with the game logic but it works
    def draw(self):
        # just a var to cycle all set bits in board
        tmp = self.board.state
        # only go to next generation every 20 ticks
        if (not self.ticks % 20 and not self.paused):
            self.next_board()
        while (tmp):
            rightmost_bit = tmp & (~tmp + 1)
            idx = (rightmost_bit - 1).bit_count()
            x = idx % self.board.side
            y = idx // self.board.side
            tmp &= ~rightmost_bit
            self.surface.set_at((x, y), (255, 255, 255))
        pygame.transform.scale_by(
            self.surface, self.scale_factor, self.to_be_blitted)
        self.window.fill(self.background_colour)
        self.window.blit(self.to_be_blitted, (0, 0))
        for b in self.buttons:
            self.window.blit(b.surface, b.position)
        self.textbox.update_surf()
        self.window.blit(self.textbox.surface, self.textbox.position)
        pygame.display.update()
        self.surface.fill((0, 0, 0))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                # if inside the board
                if x < self.scale_factor*self.board.side and y < self.scale_factor*self.board.side:
                    bit = 1 << (x // self.scale_factor +
                                (y // self.scale_factor) * self.board.side)
                    self.board.state ^= bit
                self.textbox.selected = self.textbox.rect.collidepoint((x, y))
                for b in self.buttons:
                    b.onclick(pygame.mouse.get_pos())
            if event.type == pygame.KEYDOWN:
                self.textbox.handle_inp(event.key)

    def game_loop(self):
        while True:
            self.clock.tick(100)
            self.ticks += 1
            self.handle_events()
            self.draw()


# state is just an int with n_bits = side * side
class Board:
    # note that the board state has furthest down to the right as position 0.
    def __init__(self, side, initial):
        self.state = initial
        self.side = side
        # this is mask for (1,1)
        self.default_mask = 0x7 | (0x5 << side) | (
            0x7 << side*2)
        self.x_border_mask = 1 | 1 << side | 1 << 2*side

        # top left mask, top right mask, bottom left mask, bottom right mask
        # the numbers are the magic ones which do the right thing
        self.tlm = 0x2 | 0x3 << side | 0x3 << (
            side*(side-1)) | 1 << (side-1) | 1 << (2*side - 1) | 1 << (side*side - 1) | 1 << (side*side - 1)
        self.trm = 1 << (side - 2) | 0x3 << (2*side -
                                             2) | 1 | 1 << side | 0x3 << (side*side-2) | 1 << (side*(side-1))
        self.blm = 0x3 | 0x1 << (
            side - 1) | 0x5 << (side*(side-1)-1) | 1 << (side*side-1) | 0x3 << (side*(side-2))
        self.brm = 1 | 0x3 << (side - 2) | (1 << (side-2)
                                            | 1) << side*(side-1) | (0x3 << (side - 2) | 1) << side*(side-2)
        # i feel mean to my laptop when i create a lookup table of this size
        # if we have a 256*256 board, the largest ints in the list are 6 kb (256 * 256 bytes)
        # the funny part is that each int only has 8 bits set
        self.lookup = np.array([create_mask(self, y, x) for x in range(
            0, self.side) for y in range(0, self.side)])


def shift(num, places):
    if (places < 0):
        return num >> -places
    return num << places

# create_mask fetches a number where the bits of adjacent coordinates (including diagonally adjacent board-squares)
# are set in the corresponding integer


def create_mask(board, x, y):
    window = board.default_mask
    y_border_mask = 0x7
    t = x-1 + (y-1)*board.side
    if (x != 0 and x != board.side - 1 and y != 0 and y != board.side-1):
        return shift(window, t)
    if (x == 0):
        if (y == 0):
            return board.tlm
        elif (y == board.side-1):
            return board.blm
        window &= ~board.x_border_mask
        window = shift(window, t)
        window |= shift(board.x_border_mask, y*board.side-1)
    elif (x == board.side - 1):
        if (y == 0):
            return board.trm
        elif (y == board.side - 1):
            return board.brm
        window &= ~(board.x_border_mask << 2)
        window = shift(window, t)
        window |= shift(board.x_border_mask, (y-1)*board.side)
    if (y == 0):
        window &= ~y_border_mask
        window = shift(window, t)
        window |= shift(y_border_mask, board.side*(board.side-1) + x - 1)
    elif (y == board.side - 1):
        window &= ~(y_border_mask << 2*board.side)
        window = shift(window, t)
        window |= shift(y_border_mask,  x - 1)
    return window


def alive_next(state, lookup, idx):
    t = 1 << idx  # could just pass rightmost bit as arg since i already have calc'd it
    currently_alive = state & t
    surround_pop = (state & lookup[idx]) .bit_count()
    if (currently_alive):
        if (surround_pop == 2 or surround_pop == 3):
            return 1
    else:
        if (surround_pop == 3):
            return 1
    return 0


def main():
    side = 32
    board = Board(side, 0)
    assert (board.side >= 4)
    pygame.freetype.init()
    font = pygame.freetype.Font("arcadeclassic.ttf", 32)
    game = Game(board, font, (80, 80, 80))
    game.game_loop()


main()
