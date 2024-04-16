import cv2
import os
import imageio.v2 as imageio
from pytube import YouTube
from googleapiclient.discovery import build
import isodate
from scenedetect import VideoManager
from scenedetect import SceneManager
from scenedetect.detectors import ContentDetector
from config import YOUTUBE_API_KEY
import easyocr
import PySimpleGUI as sg

def search_youtube(query):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=20,
        videoDuration='medium',
        order='viewCount'
    )
    response = request.execute()

    for item in response.get('items', []):
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_details = youtube.videos().list(
            part="contentDetails,statistics",
            id=video_id
        ).execute()

        if not video_details['items']:
            continue

        duration = video_details['items'][0]['contentDetails']['duration']
        duration_seconds = convert_duration(duration)
        views = video_details['items'][0]['statistics']['viewCount']

        if duration_seconds < 600:
            return video_id, video_title, duration_seconds, views
    return None, None, None, None

def convert_duration(duration):
    return isodate.parse_duration(duration).total_seconds()

def createWatermark(image):
    font = cv2.FONT_HERSHEY_SIMPLEX
    watermark_text = "Gilad Twili"
    text_size = cv2.getTextSize(watermark_text, font, 1, 2)[0]
    text_x = image.shape[1] - text_size[0] - 10
    text_y = image.shape[0] - 10
    cv2.putText(image, watermark_text, (text_x, text_y), font, 1, (255, 0, 0), 2, cv2.LINE_AA)

def find_scenes(video_path, threshold):
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector(threshold=threshold))
    try:
        video_manager.start()
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list(base_timecode=video_manager.get_base_timecode())
        return scene_list
    finally:
        video_manager.release()

def save_images(video_path, scene_list, max_images=100):
    save_dir = "images"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    image_files = []
    video_capture = cv2.VideoCapture(video_path)
    count = 0
    text_accumulator = ""  # Initialize text accumulator
    reader = easyocr.Reader(['en'])
    for start_time, _ in scene_list:
        if count >= max_images:
            break
        video_capture.set(cv2.CAP_PROP_POS_MSEC, start_time.get_seconds() * 1000)
        success, image = video_capture.read()
        if success:
            results = reader.readtext(image)
            for (_, text, _) in results:
                text_accumulator += text + " "  # Append text with a space
            createWatermark(image)
            filename = os.path.join(save_dir, f'frame_at_{start_time.get_seconds()}.jpg')
            cv2.imwrite(filename, image)
            image_files.append(filename)
            count += 1
    video_capture.release()
    print("Accumulated text from frames:", text_accumulator)
    return image_files, text_accumulator

def download_and_detect_scenes(video_id, title):
    yt = YouTube(f'https://www.youtube.com/watch?v={video_id}')
    stream = yt.streams.filter(file_extension='mp4').first()
    video_path = stream.download()
    print(f'Downloaded {title}')
    scene_list = find_scenes(video_path, threshold=27)
    image_files, detected_text = save_images(video_path, scene_list)
    process_and_display_gif(image_files)
    return detected_text  # Return the accumulated text for further use or display

def create_gif(image_files, output_path='output.gif'):
    # Limit the number of images to 100 to ensure the GIF is no longer than 10 seconds at 0.1s per frame
    with imageio.get_writer(output_path, mode='I', duration=0.1) as writer:
        for image_file in image_files[:100]:  # Only take the first 100 images
            image = imageio.imread(image_file)
            writer.append_data(image)
    return output_path

def process_and_display_gif(image_files):
    gif_path = create_gif(image_files)
    print(f"Creating GIF at {gif_path}")
    layout = [[sg.Image(key='-IMAGE-')]]
    window = sg.Window('Display GIF', layout, finalize=True)
    gif = imageio.mimread(gif_path)
    frame_duration = 100  # Duration each frame is displayed in milliseconds

    # Display each frame in the GIF
    while True:
        for frame in gif:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            imgbytes = cv2.imencode('.png', frame_rgb)[1].tobytes()
            window['-IMAGE-'].update(data=imgbytes)
            event, values = window.read(timeout=frame_duration)
            if event == sg.WIN_CLOSED:
                break
        if event == sg.WIN_CLOSED:
            break

    window.close()

def main():
    subject = sg.popup_get_text('Please enter a subject for the video:', 'Input Required')
    if not subject:
        sg.popup("You did not enter a subject.", "Exiting")
        return

    video_id, title, duration, views = search_youtube(subject)
    if video_id:
        sg.popup(f'Top video: {title} ({duration} seconds, {views} views)')
        detected_text = download_and_detect_scenes(video_id, title)
        sg.popup(f"Detected Text: {detected_text}")  # Display detected text in a popup
    else:
        sg.popup("No suitable video found.")

if __name__ == "__main__":
    main()
