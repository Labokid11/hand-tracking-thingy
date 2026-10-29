import cv2
import mediapipe as mp
import time
import math
import ctypes


# ============================================================
# WINDOWS MOUSE CONTROL
# ============================================================

user32 = ctypes.windll.user32

SCREEN_WIDTH = user32.GetSystemMetrics(0)
SCREEN_HEIGHT = user32.GetSystemMetrics(1)

# Mouse buttons
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

# Mouse wheel
MOUSEEVENTF_WHEEL = 0x0800


def move_mouse(x, y):

    user32.SetCursorPos(
        int(x),
        int(y)
    )


def left_click():

    user32.mouse_event(
        MOUSEEVENTF_LEFTDOWN,
        0,
        0,
        0,
        0
    )

    user32.mouse_event(
        MOUSEEVENTF_LEFTUP,
        0,
        0,
        0,
        0
    )


def right_click():

    user32.mouse_event(
        MOUSEEVENTF_RIGHTDOWN,
        0,
        0,
        0,
        0
    )

    user32.mouse_event(
        MOUSEEVENTF_RIGHTUP,
        0,
        0,
        0,
        0
    )


def scroll(amount):

    user32.mouse_event(
        MOUSEEVENTF_WHEEL,
        0,
        0,
        int(amount),
        0
    )


# ============================================================
# MEDIAPIPE
# ============================================================

BaseOptions = mp.tasks.BaseOptions

HandLandmarker = (
    mp.tasks.vision.HandLandmarker
)

HandLandmarkerOptions = (
    mp.tasks.vision.HandLandmarkerOptions
)

VisionRunningMode = (
    mp.tasks.vision.RunningMode
)


options = HandLandmarkerOptions(

    base_options=BaseOptions(
        model_asset_path=(
            "models/hand_landmarker.task"
        )
    ),

    running_mode=VisionRunningMode.VIDEO,

    num_hands=2
)


# ============================================================
# HAND CONNECTIONS
# ============================================================

HAND_CONNECTIONS = [

    # Thumb
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),

    # Index
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),

    # Middle
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),

    # Ring
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),

    # Pinky
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),

    # Palm
    (0, 17)
]


# ============================================================
# HAND FUNCTIONS
# ============================================================

def distance(point1, point2):

    return math.sqrt(
        (point1.x - point2.x) ** 2
        +
        (point1.y - point2.y) ** 2
    )


def detect_fingers(hand):

    fingers = {

        "Thumb": False,

        "Index":
            hand[8].y < hand[6].y,

        "Middle":
            hand[12].y < hand[10].y,

        "Ring":
            hand[16].y < hand[14].y,

        "Pinky":
            hand[20].y < hand[18].y
    }


    fingers["Thumb"] = (
        distance(
            hand[4],
            hand[5]
        )
        >
        distance(
            hand[3],
            hand[5]
        ) * 1.15
    )


    return fingers


def detect_pinch(hand):

    return (
        distance(
            hand[4],
            hand[8]
        )
        < 0.05
    )


def get_palm_position(hand):

    palm_x = (
        hand[0].x
        + hand[5].x
        + hand[9].x
        + hand[13].x
        + hand[17].x
    ) / 5


    palm_y = (
        hand[0].y
        + hand[5].y
        + hand[9].y
        + hand[13].y
        + hand[17].y
    ) / 5


    return palm_x, palm_y


# ============================================================
# GESTURE RECOGNITION
# ============================================================

def is_open_palm(fingers):

    return (
        fingers["Index"]
        and fingers["Middle"]
        and fingers["Ring"]
        and fingers["Pinky"]
    )


def is_fist(fingers):

    return not (
        fingers["Index"]
        or fingers["Middle"]
        or fingers["Ring"]
        or fingers["Pinky"]
    )


def is_index_only(fingers):

    return (
        fingers["Index"]
        and not fingers["Middle"]
        and not fingers["Ring"]
        and not fingers["Pinky"]
    )


def is_two_fingers(fingers):

    return (
        fingers["Index"]
        and fingers["Middle"]
        and not fingers["Ring"]
        and not fingers["Pinky"]
    )


# ============================================================
# ACTIVATION SETTINGS
# ============================================================

ACTIVATION_TIME = 0.40

activation_start = None

mouse_control_active = False


# ============================================================
# MOUSE SETTINGS
# ============================================================

smooth_x = SCREEN_WIDTH // 2
smooth_y = SCREEN_HEIGHT // 2

SMOOTHING = 0.20


# ============================================================
# GESTURE COOLDOWN
# ============================================================

GESTURE_COOLDOWN = 0.70

last_gesture_time = 0


def gesture_ready():

    return (
        time.time() - last_gesture_time
        >= GESTURE_COOLDOWN
    )


def register_gesture():

    global last_gesture_time

    last_gesture_time = time.time()


# ============================================================
# PINCH / RIGHT CLICK STATE
# ============================================================

pinch_previous = False
index_previous = False
fist_previous = False


# ============================================================
# SCROLL
# ============================================================

previous_scroll_y = None

scroll_accumulator = 0.0

SCROLL_SENSITIVITY = 1400


# ============================================================
# CAMERA
# ============================================================

camera = cv2.VideoCapture(0)


if not camera.isOpened():

    print("Could not open webcam.")

    exit()


# ============================================================
# TIMING
# ============================================================

start_time = time.time()


# ============================================================
# MAIN LOOP
# ============================================================

with HandLandmarker.create_from_options(
    options
) as landmarker:

    try:

        while True:

            success, frame = camera.read()


            if not success:

                print(
                    "Could not read webcam frame."
                )

                break


            # ------------------------------------------------
            # MEDIAPIPE
            # ------------------------------------------------

            rgb_frame = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )


            mp_image = mp.Image(
                image_format=(
                    mp.ImageFormat.SRGB
                ),
                data=rgb_frame
            )


            timestamp_ms = int(
                (
                    time.time()
                    - start_time
                )
                * 1000
            )


            result = (
                landmarker.detect_for_video(
                    mp_image,
                    timestamp_ms
                )
            )


            hand_found = False

            gesture_name = "NONE"


            # ------------------------------------------------
            # PROCESS HANDS
            # ------------------------------------------------

            for hand_index, hand in enumerate(
                result.hand_landmarks
            ):

                # Only first hand controls mouse
                if hand_index != 0:
                    continue


                hand_found = True


                # ------------------------------------------------
                # DRAW SKELETON
                # ------------------------------------------------

                points = []


                for landmark in hand:

                    px = int(
                        landmark.x
                        * frame.shape[1]
                    )

                    py = int(
                        landmark.y
                        * frame.shape[0]
                    )

                    points.append(
                        (px, py)
                    )


                for start, end in (
                    HAND_CONNECTIONS
                ):

                    cv2.line(
                        frame,
                        points[start],
                        points[end],
                        (0, 255, 0),
                        3
                    )


                for px, py in points:

                    cv2.circle(
                        frame,
                        (px, py),
                        5,
                        (0, 255, 0),
                        -1
                    )


                # ------------------------------------------------
                # FINGERS
                # ------------------------------------------------

                fingers = detect_fingers(hand)

                pinching = detect_pinch(hand)

                finger_count = sum(
                    fingers.values()
                )


                # ------------------------------------------------
                # GESTURE STATES
                # ------------------------------------------------

                open_palm = is_open_palm(
                    fingers
                )

                fist = is_fist(
                    fingers
                )

                index_only = is_index_only(
                    fingers
                )

                two_fingers = is_two_fingers(
                    fingers
                )


                # =================================================
                # NOT ACTIVE
                # =================================================

                if not mouse_control_active:

                    if open_palm:

                        gesture_name = (
                            "OPEN PALM - ACTIVATING"
                        )


                        if activation_start is None:

                            activation_start = (
                                time.time()
                            )


                        activation_elapsed = (
                            time.time()
                            - activation_start
                        )


                        if (
                            activation_elapsed
                            >= ACTIVATION_TIME
                        ):

                            mouse_control_active = True

                            activation_start = None

                            pinch_previous = False
                            index_previous = False
                            fist_previous = False

                            previous_scroll_y = None
                            scroll_accumulator = 0


                    else:

                        activation_start = None

                        gesture_name = (
                            "OPEN PALM TO ACTIVATE"
                        )


                # =================================================
                # ACTIVE
                # =================================================

                else:

                    # ------------------------------------------------
                    # FIST = EMERGENCY STOP
                    # ------------------------------------------------

                    if fist:

                        gesture_name = (
                            "FIST - MOUSE PAUSED"
                        )


                        if (
                            not fist_previous
                            and gesture_ready()
                        ):

                            mouse_control_active = False

                            register_gesture()

                            previous_scroll_y = None

                            scroll_accumulator = 0


                    # ------------------------------------------------
                    # PALM POSITION
                    # ------------------------------------------------

                    palm_x, palm_y = (
                        get_palm_position(hand)
                    )


                    # ------------------------------------------------
                    # PINCH = LEFT CLICK
                    # ------------------------------------------------

                    if pinching:

                        gesture_name = (
                            "PINCH - LEFT CLICK"
                        )


                        if (
                            not pinch_previous
                            and gesture_ready()
                        ):

                            left_click()

                            register_gesture()


                    # ------------------------------------------------
                    # INDEX ONLY = RIGHT CLICK
                    # ------------------------------------------------

                    elif index_only:

                        gesture_name = (
                            "INDEX - RIGHT CLICK"
                        )


                        if (
                            not index_previous
                            and gesture_ready()
                        ):

                            right_click()

                            register_gesture()


                    # ------------------------------------------------
                    # TWO FINGERS = SCROLL
                    # ------------------------------------------------

                    elif two_fingers:

                        gesture_name = (
                            "TWO FINGERS - SCROLL"
                        )


                        if previous_scroll_y is not None:

                            delta_y = (
                                palm_y
                                - previous_scroll_y
                            )


                            scroll_accumulator += (
                                -delta_y
                                * SCROLL_SENSITIVITY
                            )


                            while (
                                abs(
                                    scroll_accumulator
                                )
                                >= 120
                            ):

                                if (
                                    scroll_accumulator
                                    > 0
                                ):

                                    scroll(120)

                                    scroll_accumulator -= 120

                                else:

                                    scroll(-120)

                                    scroll_accumulator += 120


                        previous_scroll_y = palm_y


                    else:

                        previous_scroll_y = None

                        scroll_accumulator = 0


                    # =================================================
                    # OPEN PALM = MOUSE CONTROL
                    # =================================================

                    if open_palm:

                        gesture_name = (
                            "OPEN PALM - MOUSE"
                        )


                    # =================================================
                    # PALM MOUSE MOVEMENT
                    # =================================================

                    # Mouse movement happens for all active
                    # gestures except the fist.

                    if not fist:

                        margin = 0.10


                        normalized_x = (
                            palm_x
                            - margin
                        ) / (
                            1
                            - margin * 2
                        )


                        normalized_y = (
                            palm_y
                            - margin
                        ) / (
                            1
                            - margin * 2
                        )


                        # Mirror horizontal direction

                        normalized_x = (
                            1.0
                            - normalized_x
                        )


                        # Clamp

                        normalized_x = max(
                            0.0,
                            min(
                                1.0,
                                normalized_x
                            )
                        )


                        normalized_y = max(
                            0.0,
                            min(
                                1.0,
                                normalized_y
                            )
                        )


                        target_x = (
                            normalized_x
                            * SCREEN_WIDTH
                        )


                        target_y = (
                            normalized_y
                            * SCREEN_HEIGHT
                        )


                        smooth_x += (
                            target_x
                            - smooth_x
                        ) * SMOOTHING


                        smooth_y += (
                            target_y
                            - smooth_y
                        ) * SMOOTHING


                        move_mouse(
                            smooth_x,
                            smooth_y
                        )


                # ------------------------------------------------
                # UPDATE PREVIOUS STATES
                # ------------------------------------------------

                pinch_previous = pinching

                index_previous = index_only

                fist_previous = fist


                # =================================================
                # DEBUG DISPLAY
                # =================================================

                y_base = 30


                cv2.putText(
                    frame,
                    "Hand detected",
                    (20, y_base),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2
                )


                for i, (
                    finger,
                    is_up
                ) in enumerate(
                    fingers.items()
                ):

                    state = (
                        "UP"
                        if is_up
                        else "DOWN"
                    )


                    cv2.putText(
                        frame,
                        f"{finger}: {state}",
                        (
                            20,
                            y_base
                            + 30
                            + i * 25
                        ),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 255, 255),
                        2
                    )


                cv2.putText(
                    frame,
                    f"Fingers: {finger_count}",
                    (
                        20,
                        y_base + 160
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )


                cv2.putText(
                    frame,
                    (
                        "Pinch: "
                        + (
                            "YES"
                            if pinching
                            else "NO"
                        )
                    ),
                    (
                        20,
                        y_base + 195
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),
                    2
                )


                # =================================================
                # STATUS
                # =================================================

                if mouse_control_active:

                    status = (
                        "MOUSE: ACTIVE"
                    )

                    status_colour = (
                        0,
                        255,
                        0
                    )

                else:

                    status = (
                        "MOUSE: PAUSED"
                    )

                    status_colour = (
                        0,
                        0,
                        255
                    )


                cv2.putText(
                    frame,
                    status,
                    (
                        20,
                        frame.shape[0] - 55
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    status_colour,
                    2
                )


                cv2.putText(
                    frame,
                    gesture_name,
                    (
                        20,
                        frame.shape[0] - 20
                    ),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 255, 255),
                    2
                )


            # ====================================================
            # NO HAND
            # ====================================================

            if not hand_found:

                activation_start = None

                mouse_control_active = False

                pinch_previous = False
                index_previous = False
                fist_previous = False

                previous_scroll_y = None
                scroll_accumulator = 0

                gesture_name = (
                    "NO HAND"
                )


            # ====================================================
            # SHOW CAMERA
            # ====================================================

            cv2.imshow(
                "Palm Mouse",
                frame
            )


            # ====================================================
            # ESC = EXIT
            # ====================================================

            if (
                cv2.waitKey(1)
                & 0xFF
            ) == 27:

                break


    finally:

        camera.release()

        cv2.destroyAllWindows()
