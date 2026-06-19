import cv2
import numpy as np
import HandTracking as ht
import time
from pynput.mouse import Controller, Button
import pyautogui
################################
pyautogui.FAILSAFE = False
wCam, hCam = 620, 480
framR = 100 # Frame Reduction
smoothe = 5
clickFlag = False
scrollFlag = False
dragFlag = False

################################

pTime= 0
plocX, plocY = 0,0
clocX, clocY = 0,0

################################

cap = cv2.VideoCapture(0)
cap.set(3, wCam)
cap.set(4, hCam)
detector = ht.handDetector(maxHands=1)
wScr, hScr = pyautogui.size()
mouse = Controller()


while True:
    #1. Find Hand landmark
    success, img = cap.read()
    img= detector.findHands(img)
    lmList, bbox = detector.findPosition(img, draw=False)

    
    #2. Get the tip of index and middle fingers
    if len(lmList)!= 0:
        x1,y1= lmList[8][1:]     # Index finger tip
        x2, y2= lmList[12][1:]   # Middle finger tip
        x3, y3 = lmList[16][1:]  # Ring finger tip
        x4, y4 = lmList[20][1:]  # Pinky finger tip

    #3. Check which fingers are up
    fingers = detector.fingersUp()
    cv2.rectangle(img, (framR, framR), (wCam-framR, hCam-framR),
                          (255,0,255), 2)
    
    if fingers != []:

        #4. Only Index finger: Moving mode
        if fingers[1] == 1 and fingers[2] == 0:


            #5. Convert coordinates
            x3 = np.interp(x1, (framR,wCam-framR), (0,wScr))
            y3 = np.interp(y1, (framR,hCam-framR), (0,hScr))


            #6. Smoothen Value
            clocX = plocX +(x3 - plocX) / smoothe
            clocY = plocY +(y3 - plocY) / smoothe
            

            #7. Move mouse
            mouse.position = (wScr-clocX, clocY)
            cv2.circle(img,(x1,y1), 15, (255, 0, 0), cv2.FILLED)
            plocX, plocY = clocX, clocY



        #8. Both index and middle fingers up: Clicking Mode
        if fingers[1] == 1 and fingers[2] == 1:


            #9. Find distance between fingers
            length, img, lineInfo =detector.findDistance(8, 12, img)

            #10. Click mouse if distance is short
            if length < 40 and not clickFlag:
                cv2.circle(img,(lineInfo[4], lineInfo[5]), 15, (0, 255, 0), cv2.FILLED)
                mouse.click(Button.left, 1)
                clickFlag = True
            elif length > 40:
                clickFlag = False
        
        # 11. Right Click Mode: Index + Middle + Ring fingers up
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 0:
            
            # 12. Right Click Mode: Middle + Ring finger pinch
            length, img, lineInfo = detector.findDistance(12, 16, img)  # Middle to Ring
            if fingers[2] == 1 and fingers[3] == 1:  # Middle and Ring fingers up
                if length < 40 and not clickFlag:
                    cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 0, 255), cv2.FILLED)
                    mouse.click(Button.right, 1)
                    clickFlag = True
                    #print("Right Click (Middle + Ring)")
                elif length >= 40:
                    clickFlag = False




        # 14. Scrolling Gesture: Both index & middle fingers up and moved up/down
        if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 1 and fingers[4] == 1:
            if not scrollFlag:
                scrollFlag = True  # Activate scrolling mode

                # Scroll Up
            if y2 < hCam // 2 - 30:
                pyautogui.scroll(40)  # Scroll Up
                #print("Scrolling Up")

                # Scroll Down
            elif y2 > hCam // 2 + 30:
                pyautogui.scroll(-40)  # Scroll Down
                #print("Scrolling Down")
            else:
                scrollFlag = False  # Reset scrolling mode when fingers change

        
        #15. Drag and Drop Mode: Thumb + Index pinch
        if fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
            length, img, lineInfo = detector.findDistance(4, 8, img)  # Thumb to Index

            if length < 40 and not dragFlag:
                cv2.circle(img, (lineInfo[4], lineInfo[5]), 15, (0, 100, 255), cv2.FILLED)
                mouse.press(Button.left)
                dragFlag = True
                #print("Drag Started") 

            elif length >= 40 and dragFlag:
                mouse.release(Button.left)
                dragFlag = False
                #print("Drop")





    #XX.FPS
    cTime= time.time()
    fps= 1/(cTime-pTime)
    pTime = cTime
    cv2.putText(img, str(int(fps)), (20,50), cv2.FONT_HERSHEY_COMPLEX, 1,
                (255,0,255), 3)


    #XX. Display
    cv2.imshow("Image", img)
    cv2.waitKey(1)
