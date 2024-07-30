"""
May not be compatible with current design. need minor fix to return dict
from mtcnn.mtcnn import MTCNN

# Create an MTCNN detector
detector = MTCNN()

def detect_faces(img):
    faces = detector.detect_faces(img)
    return [(result['box'][0], result['box'][1], result['box'][0] + result['box']
             [2], result['box'][1] + result['box'][3]) for result in faces]
 """
