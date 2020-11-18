#!/usr/bin/env python

from __future__ import division
import cv2
import numpy as np
import socket
import struct
import face_recognition
from src.hand_tracker import HandTracker
import vptree
from sklearn.preprocessing import normalize

MAX_DGRAM = 2**16

WINDOW = "Hand Tracking"
PALM_MODEL_PATH = "models/palm_detection_without_custom_op.tflite"
LANDMARK_MODEL_PATH = "models/hand_landmark.tflite"
ANCHORS_PATH = "models/anchors.csv"
MULTIHAND = True
HULL = True
POINT_COLOR = (0, 255, 0)
CONNECTION_COLOR = (255, 0, 0)
HULL_COLOR = (0, 0, 255)
THICKNESS = 2
HULL_THICKNESS = 2

indexes = ['swing', 'ok', 'index', 'three', 'thumbs',
           'palm_closed', 'palm_opened', 'peace', 'smile', 'fist']
poseData = np.array(
    [[0.18647491, 0.22245079, 0.1426551, 0.21015471, 0.10659113, 0.17722285, 0.07597828, 0.14441899, 0.04117138, 0.12755607, 0.13508488, 0.12111125, 0.12516799, 0.09906237, 0.13493404, 0.13594537, 0.14436085, 0.16026148, 0.16782215, 0.11746154, 0.15590905, 0.10302253, 0.1628355, 0.14403075, 0.16621838, 0.16670691, 0.1954005, 0.11966107, 0.18288804, 0.10100616, 0.18230077, 0.14286134, 0.18251303, 0.16901286, 0.22006123, 0.12585712, 0.21669258, 0.09424948, 0.21802386, 0.08854462, 0.22061957, 0.08287658],
     [0.18434688, 0.23973041, 0.14691995, 0.22440134, 0.10763994, 0.19372458, 0.08462718, 0.15996101, 0.0919741, 0.13386023, 0.14644286, 0.13712727, 0.12869465, 0.10208318, 0.11398955, 0.10302045, 0.1063617, 0.11758749, 0.17654136, 0.12364753, 0.17334996,
         0.08817116, 0.16406605, 0.06903247, 0.15090216, 0.05939158, 0.2042279, 0.12392038, 0.20935623, 0.0892418, 0.20847576, 0.06383019, 0.20308884, 0.04911344, 0.22908612, 0.13730193, 0.23782973, 0.10968894, 0.24331368, 0.08895545, 0.24093, 0.07055891],
        [0.20574305, 0.24668849, 0.17556497, 0.22605193, 0.16709151, 0.18426183, 0.1565399, 0.13807951, 0.14085615, 0.10864406, 0.13268977, 0.12998907, 0.10006527, 0.09176336, 0.07787868, 0.0682522, 0.06510728, 0.04197233, 0.16696938, 0.11354819, 0.1544783,
            0.08169002, 0.15741036, 0.12510934, 0.16674335, 0.15652471, 0.19831311, 0.11199987, 0.18993277, 0.09362093, 0.18439568, 0.13545503, 0.18726359, 0.16281337, 0.22629688, 0.1143615, 0.21396741, 0.09988577, 0.20127536, 0.12347081, 0.19796878, 0.13589683],
        [0.17428913, 0.22340391, 0.14914798, 0.20840863, 0.15048555, 0.18228617, 0.17473708, 0.1608064, 0.19158579, 0.14686246, 0.14201826, 0.13200931, 0.12749632, 0.10153376, 0.12069826, 0.07668609, 0.11883414, 0.05552163, 0.16612802, 0.1266895, 0.15665322,
            0.08347182, 0.14908728, 0.0534117, 0.1459203, 0.03266382, 0.18750041, 0.13434874, 0.19842204, 0.1047664, 0.20909921, 0.07691436, 0.21895828, 0.05321266, 0.20351892, 0.15110564, 0.2007541, 0.13908943, 0.19469448, 0.15677244, 0.19387661, 0.17648656],
        [0.18318445, 0.19968832, 0.14287076, 0.18600786, 0.11637019, 0.16152485, 0.08647456, 0.14779573, 0.05557882, 0.14432782, 0.14192424, 0.12375153, 0.13563914, 0.09971043, 0.14532968, 0.13380753, 0.15298971, 0.15120736, 0.1698368, 0.12254469, 0.16546489,
            0.09175989, 0.17154135, 0.12940182, 0.17324638, 0.14299075, 0.19456672, 0.12514232, 0.19334476, 0.09510231, 0.19214967, 0.13037139, 0.19076402, 0.1456383, 0.21474029, 0.13218189, 0.21210906, 0.10960651, 0.20567045, 0.13224842, 0.20259804, 0.14286903],
        [0.18403882, 0.24353707, 0.14810409, 0.22914967, 0.12417554, 0.18973013, 0.12259782, 0.14893835, 0.11102115, 0.11358896, 0.15214691, 0.1311901, 0.14718324, 0.08699801, 0.14754051, 0.06110825, 0.15094065, 0.04055923, 0.18231844, 0.12787095, 0.17720394,
            0.07999649, 0.17626061, 0.0497845, 0.17944943, 0.02243138, 0.2067777, 0.13276722, 0.20279329, 0.08606274, 0.20236166, 0.05536058, 0.20367333, 0.02794368, 0.23090097, 0.14432277, 0.22738936, 0.10891946, 0.22557151, 0.08665721, 0.22383213, 0.06285533],
        [0.17631676, 0.23708939, 0.14418184, 0.23419264, 0.10796663, 0.207165, 0.07474618, 0.1834449, 0.04238176, 0.17242876, 0.13524102, 0.14036904, 0.11232554, 0.10297773, 0.0953594, 0.07710497, 0.08513111, 0.05016499, 0.16541265, 0.13140274, 0.15476162,
            0.08412453, 0.14449899, 0.05059239, 0.13948139, 0.02597261, 0.19627573, 0.1354175, 0.2089023, 0.09828945, 0.21755092, 0.06708373, 0.22629108, 0.03850894, 0.22214781, 0.15227182, 0.23576951, 0.12703479, 0.24628387, 0.10898917, 0.25998274, 0.08610159],
        [0.15809512, 0.21386635, 0.13883535, 0.19705718, 0.13926474, 0.17525064, 0.16078032, 0.15910315, 0.18392389, 0.15248496, 0.13396172, 0.12849582, 0.12214344, 0.0915025, 0.11687374, 0.06437053, 0.11331773, 0.04076419, 0.15858937, 0.13062589, 0.17076254,
            0.08365408, 0.17719568, 0.0519051, 0.181212, 0.02521239, 0.17802356, 0.1422498, 0.19014316, 0.12382668, 0.18559735, 0.14721359, 0.18039312, 0.16166485, 0.19397253, 0.15961269, 0.20374444, 0.15435946, 0.1943716, 0.16737686, 0.18299277, 0.17574173],
        [0.18620316, 0.20848493, 0.1534262, 0.21623465, 0.1260341, 0.19782164, 0.09503594, 0.19968312, 0.06283229, 0.20630055, 0.13811894, 0.12506329, 0.11950041, 0.08752148, 0.11655949, 0.06574876, 0.11584203, 0.04994573, 0.167047, 0.11787352, 0.17084832,
            0.07968003, 0.16905089, 0.10314258, 0.16184104, 0.12502938, 0.19173373, 0.12087494, 0.1971879, 0.08911833, 0.19370474, 0.116432, 0.185174, 0.13954724, 0.21385323, 0.12904313, 0.22037847, 0.1107641, 0.21645382, 0.12715677, 0.20674225, 0.14231086],
        [0.16870468, 0.23211507, 0.12977799, 0.20814243, 0.09943, 0.16382496, 0.1123175, 0.12978834, 0.14672848, 0.13607521, 0.13753864, 0.13317615, 0.14097033, 0.09809432, 0.14065007, 0.12935257, 0.14333271, 0.14504507, 0.16329045, 0.12753517, 0.16547387, 0.08546145, 0.16095263, 0.12244097, 0.15828503, 0.13600505, 0.18647549, 0.13310245, 0.19047755, 0.09372779, 0.18434687, 0.12874961, 0.18357106, 0.14497022, 0.20711118, 0.14537352, 0.20915552, 0.11293839, 0.20329643, 0.13409531, 0.20128276, 0.14754838]])

max_size = 400


def get_pose(kp, box):

    x0, y0 = 0, 0
    box_width = np.linalg.norm(box[1] - box[0])
    box_height = np.linalg.norm(box[3] - box[0])

    x1 = ((kp[:, 0] - x0) * max_size) / box_width
    y1 = ((kp[:, 1] - y0) * max_size) / box_height

    a = np.array([x1, y1])
    v = a.transpose().flatten()

    return normalize([v], norm='l2')[0]


def similarity(v1, v2):
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))


def cosineDistanceMatching(poseVector1, poseVector2):
    cosineSimilarity = similarity(poseVector1, poseVector2)
    distance = 2 * (1 - cosineSimilarity)
    return np.sqrt(distance)


idx_m = np.mean(poseData, axis=1)
tree = vptree.VPTree(poseData, cosineDistanceMatching)

#        8   12  16  20
#        |   |   |   |
#        7   11  15  19
#    4   |   |   |   |
#    |   6   10  14  18
#    3   |   |   |   |
#    |   5---9---13--17
#    2    \         /
#     \    \       /
#      1    \     /
#       \    \   /
#        ------0-
connections = [

    (5, 6), (6, 7), (7, 8),
    (9, 10), (10, 11), (11, 12),
    (13, 14), (14, 15), (15, 16),
    (0, 5), (5, 9), (9, 13), (13, 17), (0, 9), (0, 13)
]
pseudo_hull_connections = [
    (0, 17), (17, 18), (18, 19), (19, 20), (0, 1), (1, 2), (2, 3), (3, 4)]
hull_connections = [(4, 8), (8, 12), (12, 16), (16, 20)]
if HULL:
    hull_connections += pseudo_hull_connections
else:
    connections += pseudo_hull_connections
detector = HandTracker(
    PALM_MODEL_PATH,
    LANDMARK_MODEL_PATH,
    ANCHORS_PATH,
    box_shift=0.2,
    box_enlarge=1.3
)


def handgesture(frame):
    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    hand = detector(image)
    if hand[0] is not None and len(hand) > 0:
        points = hand[0]
        box = hand[2]
        bkp = hand[4]
        kp = get_pose(bkp, box)

        res = tree.get_n_nearest_neighbors(kp, 1)[0]
        a = np.mean(res[1])
        #print(res[0], np.where(idx_m == a)[0][0])
        idx = np.where(idx_m == a)[0][0]
        if res[0] < 0.2:
            idx = np.where(idx_m == a)[0][0]
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(frame, indexes[idx], (20, 100),
                        font, 2, (255, 0, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, str(res[0]), (20, 30),
                        font, 1, (255, 0, 0), 2, cv2.LINE_AA)

        if points is not None:
            for point in points:
                x, y = point
                cv2.circle(frame, (int(x), int(y)), THICKNESS *
                           2, POINT_COLOR, THICKNESS)
            for connection in connections:
                x0, y0 = points[connection[0]]
                x1, y1 = points[connection[1]]
                cv2.line(frame, (int(x0), int(y0)), (int(x1), int(y1)),
                         CONNECTION_COLOR, THICKNESS)
    return frame, idx


known_face_encodings = []
known_face_names = []
face_locations = []
face_encodings = []

for i in range(5):
    image = face_recognition.load_image_file(str(i)+".jpg")
    face_encoding = face_recognition.face_encodings(image)[0]
    known_face_encodings.append(face_encoding)
    known_face_names.append(str(i))


def facerecognition(frame):
    # Resize frame of video to 1/4 size for faster face recognition processing
    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

    # Convert the image from BGR color (which OpenCV uses) to RGB color (which face_recognition uses)
    rgb_small_frame = small_frame[:, :, ::-1]

    # Find all the faces and face encodings in the current frame of video
    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(
        rgb_small_frame, face_locations)

    face_names = []
    for face_encoding in face_encodings:
        # See if the face is a match for the known face(s)
        matches = face_recognition.compare_faces(
            known_face_encodings, face_encoding)
        name = "Unknown"

        face_distances = face_recognition.face_distance(
            known_face_encodings, face_encoding)
        best_match_index = np.argmin(face_distances)
        if matches[best_match_index]:
            name = known_face_names[best_match_index]

        face_names.append(name)

    flag = 0
    # Display the results
    for (top, right, bottom, left), name in zip(face_locations, face_names):
        # Scale back up face locations since the frame we detected in was scaled to 1/4 size
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Draw a box around the face
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

        # Draw a label with a name below the face
        cv2.rectangle(frame, (left, bottom - 35),
                      (right, bottom), (0, 0, 255), cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6),
                    font, 1.0, (255, 255, 255), 1)
        flag = 1

    return frame, flag


def main():
    cap = cv2.VideoCapture(0)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(('192.168.100.134', 50007))
        while True:
            _, frame = cap.read()
            try:
                frame, flag = facerecognition(frame)
                frame, idx = handgesture(frame)
                cv2.imshow('frame', frame)
                if flag:
                    s.sendall(b'Face Detected')
                    flag = 0
                else:
                    s.sendall(b'No Detected')

                if indexes[idx] == 'palm_opened':
                    s.sendall(b'Pause')
                elif indexes[idx] == 'peace':
                    s.sendall(b'Play')
                else:
                    s.sendall(b'No Detected')

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except:
                pass

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
