import cv2
import mediapipe as mp
from pyparsing import one_of
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

import socket
import time
from sympy import Abs, capture, false, true

import numpy as np
from sympy import degree
import math

UDP_IP = '127.0.0.1'
UDP_PORT = 5065
socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)

def justremap(input, input_domain=(0,1), output_domain=(0,1)):
    return (input - input_domain[0])*(output_domain[1]-output_domain[0])/(input_domain[1]-input_domain[0]) + output_domain[0]

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return math.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))


a_one_last = 0
a_one_f = 0
a_three_last = 0
a_three_f = 0

cap = cv2.VideoCapture(0)
with mp_pose.Pose(
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5) as pose:
  while cap.isOpened():
    success, image = cap.read()
    if not success:
      print("Ignoring empty camera frame.")
      continue

    image.flags.writeable = False
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = pose.process(image)

    image.flags.writeable = True
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    mp_drawing.draw_landmarks(
        image,
        results.pose_landmarks,
        mp_pose.POSE_CONNECTIONS,
        landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())

    if(results.pose_landmarks != None):  
        keypoints = ''
        keypoints_list = []
        for data_point in results.pose_landmarks.landmark:

            x_ = justremap(data_point.x,(0,1),(1,0))
            y_ = justremap(data_point.y,(0,1),(1,0))
            point_list = []
            point_list.append(round(float(x_),3))
            point_list.append(round(float(y_),3))
            point_list.append(round(float(data_point.z),3))
            point_list.append(round(float(data_point.visibility),3))
            keypoints_list.append(point_list)
        send_switch = 0    
        shoulder_vec = (keypoints_list[12][0]-keypoints_list[11][0],
        keypoints_list[12][1]-keypoints_list[11][1],
        keypoints_list[12][2]-keypoints_list[11][2])
        vec_ = (shoulder_vec[0]+10,0,0)
          
        if keypoints_list[12][2]>keypoints_list[11][2]:
          shoulder_angle_ = round(math.degrees(angle(vec_,shoulder_vec))*-1,2)
        else:
          shoulder_angle_ = round(math.degrees(angle(vec_,shoulder_vec)),2)
          
        if(shoulder_angle_>-90 and shoulder_angle_<90):
          a_one = round(justremap(shoulder_angle_,(-90,90),(-60,-30)),2)
          if abs(abs(a_one)-abs(a_one_last)) <= 0.5:
              pass
          else:
              a_one_f = a_one
              send_switch += 1
          a_one_last = a_one

        if keypoints_list[11][3] > 0.9 and keypoints_list[13][3] > 0.9:
          waist_vec = (keypoints_list[11][0]-keypoints_list[13][0],
          keypoints_list[11][1]-keypoints_list[13][1],
          keypoints_list[11][2]-keypoints_list[13][2])
          vec_2 = (waist_vec[0],0,waist_vec[2])
          
          if keypoints_list[11][1]>keypoints_list[13][1]:
              waist_angle_ = round(math.degrees(angle(vec_2,waist_vec))*-1,2)
          else:
              waist_angle_ = round(math.degrees(angle(vec_2,waist_vec)),2)
          if waist_angle_>-70 and waist_angle_<70:
            a_three = round(justremap(waist_angle_,(-70,70),(-50,-15)),2)
            if abs(abs(a_three)-abs(a_three_last)) <= 0.5:
                pass
            else:
                a_three_f = a_three
                send_switch += 1
            a_three_last = a_three

        if a_three_f == 0:
          a_three_f = -32.5

        send_ = str(a_one_f)+'?'+str(a_three_f)
        print(send_)
        if send_switch>0:
          socket.sendto((str(send_)).encode(),(UDP_IP,UDP_PORT))
        time.sleep(0.1)

    cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
    if cv2.waitKey(1) & 0xFF == ord('q'):
      break
cap.release()