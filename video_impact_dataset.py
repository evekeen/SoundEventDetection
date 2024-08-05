import sys
import cv2
from impact_detector import ImpactDetector


def prepare_dataset(video_path):
    ckpt_path = "networks/dcase_pool_1/iteration_21600.pth"
    impact_time = ImpactDetector(ckpt_path).detect_impact(video_path)
    print(f"Impact detected at {impact_time} seconds.")
    fps = get_fps(video_path)
    print(f"Video has {fps:.2f} frames per second.")
    frame_double = impact_time * fps
    frame_int = int(frame_double)
    preview_image = get_frame(video_path, frame_int)
    cv2.imshow("Preview frame", preview_image)
    cv2.waitKey(0)
    # cv2.imshow("Preview frame + 1", get_frame(video_path, frame_int + 1))
    # cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    
def get_fps(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    return fps


def get_frame(video_path, frame_num):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
    _, frame = cap.read()
    # Rotate the frame according to the transformation in the video
    transformation_matrix = cv2.getRotationMatrix2D((frame.shape[1] / 2, frame.shape[0] / 2), 180, 1)
    transformed_frame = cv2.warpAffine(frame, transformation_matrix, (frame.shape[1], frame.shape[0]))
    return transformed_frame


if __name__ == '__main__':
    video_path = sys.argv[1]
    prepare_dataset(video_path)