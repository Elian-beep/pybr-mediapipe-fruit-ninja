from sre_constants import SUCCESS
from tkinter import Frame
import pygame
import cv2
import numpy as np
from game_states.try_again import try_again
from models.Knife import Knife
from utils.add_bombs import add_bombs
from utils.collision_handler import collision_handler
from utils.configs import (
    BACKGROUND_PATH,
    FPS,
    IMG_PATH,
    WINDOW_HEIGHT,
    WINDOW_SIZE,
    WINDOW_WIDTH,
)
from utils.fruits_behavior import fruits_behavior
from utils.throw_fruits import throw_fruits
from utils.is_pointing_finger import is_pointing_gesture

import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_hands = mp.solutions.hands

pygame.display.set_icon(pygame.image.load(IMG_PATH + "icon.png"))
pygame.display.set_caption("Fruit Ninja With Mediapipe Hands!")


def game_loop():

    # INITIAL SETTINGS AND LOADING FONTS
    pygame.init()
    font = pygame.font.Font("./font/go3v2.ttf", 100)
    font_small = pygame.font.Font("./font/go3v2.ttf", 50)

    # GET VIDEO CAPTURE FROM WEBCAM
    cap =cv2.VideoCapture(1)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, WINDOW_HEIGHT)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WINDOW_WIDTH)

    # GAME VARIABLES
    run = True
    exploding = False

    # GAME WINDOW
    win = pygame.display.set_mode(WINDOW_SIZE)

    # BACKGROUND IMAGE
    background = pygame.image.load(BACKGROUND_PATH)
    background_cv2 = cv2.imread(BACKGROUND_PATH)

    # GLOBAL VARIABLES FOR GAME OBJECTS
    knf = Knife(win)
    fruits = []

        # Main loop
    with mp_hands.Hands(
        #configurações
        model_complexity=0,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
        max_num_hands=1
    ) as hands:
        while run and cap.isOpened():
            # NEW ROUND
            if not exploding:
                # CREATE BOMBS AND FRUITS
                throw_fruits(fruits, win)
                add_bombs(fruits, win)

                # ROUND START
                while fruits != [] and run:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            run = False

                        elif event.type == pygame.MOUSEBUTTONDOWN:
                            knf.enable_cutting()

                        elif event.type == pygame.MOUSEBUTTONUP:
                            knf.disable_cutting()

                    pygame.time.delay(FPS)

                    # LENDO IMAGEM DA CAMERA
                    success, frame = cap.read()
                    if not success:
                        continue

                    # TRATAMENTO DE IMG
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame = cv2.flip(frame, 1)
                    frame.flags.writeable = False

                    bg_with_hands = background_cv2.copy()

                    # APLICANDO O MODELO NA IMAGEM
                    results = hands.process(frame)


                    finger_coord = None
                    # DESENHO DAS MÃOS ENCONTRADAS
                    if results.multi_hand_landmarks != None:
                        for hand_landmarks in results.multi_hand_landmarks:
                            mp_drawing.draw_landmarks(
                                bg_with_hands,
                                hand_landmarks,
                                mp_hands.HAND_CONNECTIONS
                            )
                            finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                            finger_coord = mp_drawing._normalized_to_pixel_coordinates(
                                finger_tip.x,
                                finger_tip.y,
                                WINDOW_WIDTH,
                                WINDOW_HEIGHT
                            )
                            if is_pointing_gesture(hand_landmarks):
                                knf.enable_cutting()
                            else:
                                knf.disable_cutting()

                    # RECONVERSÃO DE BG PARA O FORMATO REAL DE HAND PARA PYGAME

                    # FORMATO CV2
                    bg_with_hands = cv2.cvtColor(bg_with_hands, cv2.COLOR_BGR2RGB)
                    bg_with_hands = cv2.flip(bg_with_hands, 1)
                    bg_with_hands = cv2.resize(
                        bg_with_hands,
                        (WINDOW_WIDTH, WINDOW_HEIGHT),
                        interpolation=cv2.INTER_LINEAR
                    )

                    bg_with_hands = np.rot90(bg_with_hands)


                    # FORMATO PYGAMESA
                    bg_with_hands = pygame.surfarray.make_surface(
                        bg_with_hands
                    )

                    # DISPLAY BACKGROUND IMAGE
                    win.blit(
                        pygame.transform.scale(
                            bg_with_hands, (WINDOW_WIDTH, WINDOW_HEIGHT)
                        ),
                        (0, 0),
                    )

                    # UPDATE KNIFE POSITION
                    if finger_coord:
                        knf.update(finger_coord)
                        

                    # CHECK FOR KNIFE COLLISIONS AND UPDATE FRUITS
                    state = fruits_behavior(knf, fruits)
                    if state == "explode":
                        exploding = True
                        break

                    pygame.display.flip()
            # GAME OVER STATE
            else:
                try_again(win, font, font_small)
                exploding = False
                fruits = []

            if not run:
                pygame.quit()
                break
    cap.release()


if __name__ == "__main__":
    game_loop()
