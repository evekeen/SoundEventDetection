import os
import sys
import av
import cv2


def split_video_by_reader(path, output_dir, frame_nums):
    i = 1
    images = []

    def on_frame(frame):
        nonlocal i
        img = frame.to_image()
        rgb_im = img.convert('RGB')
        img_path = os.path.join(output_dir, '{:08d}.jpg'.format(i))
        rgb_im.save(img_path, quality=100)
        i = i + 1
        images.append(img_path)

    read_frames(path, frame_nums, on_frame)
    return images


def read_frames(file_path, frame_nums, callback):
    container = av.open(file_path)

    frame_num = -1
    processed = 0
    skipped = 0
    for packet in container.demux():
        if packet.stream.type == 'video':
            for image in packet.decode():
                frame_num += 1
                if frame_nums is not None and frame_num not in frame_nums:
                    skipped += 1
                    continue
                if frame_nums is not None and frame_nums[-1] < frame_num:
                    container.close()
                    print('finished reading #{} frames, skipped {}'.format(processed, skipped))
                    return
                if packet.stream.metadata.get('rotate'):
                    old_image = image
                    image = av.VideoFrame().from_ndarray(
                        rotate_image(
                            image.to_ndarray(format='bgr24'),
                            360 - int(container.streams.video[0].metadata.get('rotate'))
                        ),
                        format='bgr24'
                    )
                    image.pts = old_image.pts
                callback(image)
                processed += 1
    print('finished reading all #{} frames, skipped {}'.format(processed, skipped))



def rotate_image(image, angle):
    height, width = image.shape[:2]
    image_center = (width / 2, height / 2)
    matrix = cv2.getRotationMatrix2D(image_center, angle, 1.)
    abs_cos = abs(matrix[0, 0])
    abs_sin = abs(matrix[0, 1])
    bound_w = int(height * abs_sin + width * abs_cos)
    bound_h = int(height * abs_cos + width * abs_sin)
    matrix[0, 2] += bound_w / 2 - image_center[0]
    matrix[1, 2] += bound_h / 2 - image_center[1]
    matrix = cv2.warpAffine(image, matrix, (bound_w, bound_h))
    return matrix


if __name__ == '__main__':
    path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else '.'
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    split_video_by_reader(path, out_dir, None)