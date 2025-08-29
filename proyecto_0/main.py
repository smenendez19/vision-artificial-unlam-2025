import cv2
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

try:
    with mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5) as hands:

        cap = cv2.VideoCapture(0)

        print("Presiona Q para salir")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            height, width, _ = frame.shape
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            results = hands.process(frame_rgb)

            counts = {"Left": 0, "Right": 0}

            if results.multi_hand_landmarks and results.multi_handedness:
                for hand_landmarks, handedness in zip(results.multi_hand_landmarks, results.multi_handedness):
                    label = handedness.classification[0].label  # "Left" o "Right"

                    lm_list = [(int(lm.x * width), int(lm.y * height)) for lm in hand_landmarks.landmark]

                    for tip_id in [8, 12, 16, 20]:
                        if lm_list[tip_id][1] < lm_list[tip_id - 2][1]:
                            counts[label] += 1

                    # Pulgar
                    if label == "Right":
                        if lm_list[4][0] > lm_list[3][0]:
                            counts[label] += 1
                    else:
                        if lm_list[4][0] < lm_list[3][0]:
                            counts[label] += 1

                    # mp_drawing.draw_landmarks(
                    #    frame,
                    #    hand_landmarks,
                    #    mp_hands.HAND_CONNECTIONS,
                    #    mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=2, circle_radius=3),
                    #    mp_drawing.DrawingSpec(color=(255, 0, 255), thickness=2, circle_radius=3),
                    # )

            cv2.putText(frame, f"Izq: {counts['Left']}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
            cv2.putText(frame, f"Der: {counts['Right']}", (400, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

            cv2.imshow("Frame", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
finally:
    cap.release()
    cv2.destroyAllWindows()
