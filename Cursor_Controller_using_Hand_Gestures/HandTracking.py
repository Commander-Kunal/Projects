import cv2
import mediapipe as mp
import time
import math
import numpy as np

class handDetector():
    def __init__(self, mode=False, maxHands=2, detectConfi=0.5, trackConfi=0.5):
        self.mode = mode
        self.maxHands = int(maxHands)
        self.detectConfi = detectConfi
        self.trackConfi = trackConfi

        # Try a direct import if mp.solutions fails
        try:
            import mediapipe.python.solutions.hands as mp_hands
            import mediapipe.python.solutions.drawing_utils as mp_draw
            self.mpHands = mp_hands
            self.mpDraw = mp_draw
        except ImportError:
            # Fallback for different versions
            import mediapipe.solutions.hands as mp_hands
            import mediapipe.solutions.drawing_utils as mp_draw
            self.mpHands = mp_hands
            self.mpDraw = mp_draw

        self.hands = self.mpHands.Hands(static_image_mode=self.mode, 
                                        max_num_hands=self.maxHands,
                                        min_detection_confidence=self.detectConfi, 
                                        min_tracking_confidence=self.trackConfi)
        self.tipIds = [4, 8, 12, 16, 20]
        self.lmList = []

    def findHands(self, img, draw=True):
        if img is None:
            return None  # Prevents errors if the image is not available
        
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)

        if self.results.multi_hand_landmarks:
            for landMark in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(img, landMark, self.mpHands.HAND_CONNECTIONS)
        return img

    def findPosition(self, img, handNo=0, draw=True):
        xList, yList, self.lmList = [], [], []
        bbox = []

        if self.results.multi_hand_landmarks:
            if handNo >= len(self.results.multi_hand_landmarks):
                return self.lmList, bbox  # Prevents IndexError if handNo is out of range

            myHand = self.results.multi_hand_landmarks[handNo]
            h, w, c = img.shape  # Get image dimensions

            for id, lm in enumerate(myHand.landmark):
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmList.append([id, cx, cy])

                if draw:
                    cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = (xmin, ymin, xmax, ymax)

            if draw:
                cv2.rectangle(img, (xmin - 20, ymin - 20), (xmax + 20, ymax + 20), (0, 255, 0), 2)

        return self.lmList, bbox
    
    def fingersUp(self):
        if not self.lmList:
            return []  # Prevents IndexError if no hand is detected

        fingers = []
        # Thumb (check if thumb tip is to the right/left of thumb base depending on hand)
        if self.lmList[self.tipIds[0]][1] > self.lmList[self.tipIds[0] - 1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other four fingers (check if tip is higher than second knuckle)
        for id in range(1, 5):
            if self.lmList[self.tipIds[id]][2] < self.lmList[self.tipIds[id] - 2][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def findDistance(self, p1, p2, img, draw=True, r=15, t=3):
        if len(self.lmList) <= max(p1, p2): 
            return 0, img, []  # Prevents IndexError

        x1, y1 = self.lmList[p1][1:]
        x2, y2 = self.lmList[p2][1:]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        if draw:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), t)
            cv2.circle(img, (x1, y1), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), r, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), r, (0, 0, 255), cv2.FILLED)
        
        length = math.hypot(x2 - x1, y2 - y1)

        return length, img, [x1, y1, x2, y2, cx, cy]


def main():
    cTime, pTime = 0, 0
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return

    detector = handDetector()

    while True:
        success, img = cap.read()
        if not success or img is None:
            continue  # Skip this frame if there's an error

        img = detector.findHands(img)
        lmList, bbox = detector.findPosition(img)

        if lmList:
            print(lmList[4])  # Print coordinates of the thumb tip if available

        cTime = time.time()
        fps = 1 / (cTime - pTime) if cTime - pTime > 0 else 0
        pTime = cTime

        cv2.putText(img, f'FPS: {int(fps)}', (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 3, (255, 0, 255), 3)
        cv2.imshow("Image", img)

        if cv2.waitKey(1) & 0xFF == 27:  # Exit on pressing 'ESC'
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
