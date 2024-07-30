import os
import time
import subprocess
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import messagebox, filedialog
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Define the paths to the audio and video files on the device
media_files = {
    "audio_mp3": "/sdcard/test_audio.mp3",
    "video_mp4": "/sdcard/test_video.mp4",
    "streaming_video": "https://www.youtube.com/watch?v=TQc64TTI0Ic&t=14s"
}

def execute_adb_command(command):
    result = os.popen(command).read()
    return result

def check_device_connection():
    devices = execute_adb_command("adb devices")
    if "device" in devices:
        return True
    return False

def get_cpu_memory_usage():
    cpu_usage = execute_adb_command("adb shell top -n 1 -b | grep -i 'cpu'")
    mem_usage = execute_adb_command("adb shell dumpsys meminfo")
    return cpu_usage, mem_usage

def play_media(file_path, media_type):
    print(f"Playing {media_type}...")
    start_time = time.time()
    if media_type == "streaming_video":
        execute_adb_command(f"adb shell am start -a android.intent.action.VIEW -d {file_path}")
    elif media_type == "audio_mp3":
        execute_adb_command(f"adb shell am start -a android.intent.action.VIEW -d file://{file_path} -t audio/mpeg")
    elif media_type == "video_mp4":
        execute_adb_command(f"adb shell am start -a android.intent.action.VIEW -d file://{file_path} -t video/mp4")
    time.sleep(10)  # Wait for 10 seconds to simulate playback
    execute_adb_command("adb shell input keyevent 4")  # Stop playback
    end_time = time.time()
    duration = end_time - start_time
    cpu_usage, mem_usage = get_cpu_memory_usage()
    print(f"{media_type.capitalize()} playback completed.")
    return {"duration": duration, "cpu": cpu_usage, "memory": mem_usage}

def play_media_with_recovery(file_path, media_type):
    try:
        return play_media(file_path, media_type)
    except Exception as e:
        print(f"Error during {media_type} playback: {e}")
        # Attempt recovery
        time.sleep(5)
        try:
            return play_media(file_path, media_type)
        except Exception as e:
            print(f"Failed to recover {media_type} playback: {e}")
            return {"duration": None, "cpu": None, "memory": None}

def collect_logs():
    print("Collecting logs...")
    try:
        logs = subprocess.check_output("adb logcat -d", shell=True, encoding='utf-8', errors='ignore')
        log_summary = summarize_logs(logs)
        with open("device_logs.txt", "w", encoding='utf-8') as log_file:
            log_file.write(log_summary + "\n\nFull Logs:\n\n" + logs)
        print("Logs collected.")
    except Exception as e:
        print(f"Error collecting logs: {e}")

def categorize_log(log):
    if " E " in log or " ERROR " in log:
        severity = "Critical"
    elif " W " in log or " WARN " in log:
        severity = "Major"
    else:
        severity = "Minor"

    if "media" in log.lower():
        module = "Media Playback"
    elif "camera" in log.lower():
        module = "Camera"
    elif "sensor" in log.lower():
        module = "Sensors"
    else:
        module = "General"

    return severity, module

def summarize_logs(logs):
    lines = logs.split('\n')
    categorized_logs = {"Critical": [], "Major": [], "Minor": []}

    for line in lines:
        if " E " in line or " W " in line or " I " in line:
            severity, module = categorize_log(line)
            categorized_logs[severity].append((module, line))

    summary = "Log Summary:\n"
    summary += f"- Total Logs: {len(lines)}\n"
    summary += f"- Critical Errors: {len(categorized_logs['Critical'])}\n"
    summary += f"- Major Warnings: {len(categorized_logs['Major'])}\n"
    summary += f"- Minor Info: {len(categorized_logs['Minor'])}\n\n"
    
    for severity in ["Critical", "Major", "Minor"]:
        summary += f"{severity} Logs:\n"
        for module, log in categorized_logs[severity][:10]:
            summary += f"[{module}] {log}\n"
        summary += "\n"
    summary += "(Showing first 10 entries of each category)\n"
    
    return summary

def train_log_analyzer():
    # Enhanced training data with more examples
    training_data = [
        (" E ", "error"),
        (" W ", "warning"),
        (" I ", "info"),
        ("ERROR", "error"),
        ("WARN", "warning"),
        ("INFO", "info")
    ]
    vectorizer = CountVectorizer()
    X_train = vectorizer.fit_transform([log[0] for log in training_data])
    y_train = [log[1] for log in training_data]
    model = MultinomialNB()
    model.fit(X_train, y_train)
    return vectorizer, model

def analyze_logs(log_file_path):
    vectorizer, model = train_log_analyzer()
    with open(log_file_path, 'r', encoding='utf-8') as log_file:
        logs = log_file.readlines()
    if not logs:
        return 0, 0
    X_logs = vectorizer.transform(logs)
    predictions = model.predict(X_logs)
    error_count = list(predictions).count("error")
    warning_count = list(predictions).count("warning")
    return error_count, warning_count

def analyze_video_performance(file_path):
    # Implement frame rate analysis using a tool like FFmpeg
    frame_rate = subprocess.check_output(f"ffmpeg -i {file_path} 2>&1 | grep -o '[0-9]\\+ fps'", shell=True)
    return frame_rate

def analyze_audio_quality(file_path):
    # Implement audio quality analysis using a tool like SoX
    audio_quality = subprocess.check_output(f"sox {file_path} -n stat 2>&1 | grep 'RMS Pk dB'", shell=True)
    return audio_quality

def generate_report(metrics, error_count, warning_count, sensor_data):
    print("Generating report...")
    report_content = "Multimedia System Testing Report\n\n"

    report_content += "Media Playback Results:\n"
    for media_type, metric in metrics.items():
        report_content += f"\n{media_type.capitalize()} Playback:\n"
        report_content += f"- Duration: {metric['duration']} seconds\n"
        report_content += f"- CPU Usage: {metric['cpu']}\n"
        report_content += f"- Memory Usage: {metric['memory']}\n"
        if 'frame_rate' in metric:
            report_content += f"- Frame Rate: {metric['frame_rate']}\n"
        if 'quality' in metric:
            report_content += f"- Audio Quality: {metric['quality']}\n"
    
    report_content += f"\nErrors: {error_count}\nWarnings: {warning_count}\n"

    report_content += "\nSensor Data:\n"
    for sensor, data in sensor_data.items():
        report_content += f"\n{sensor.capitalize()} Data:\n{data}\n"
    
    with open("test_report.txt", "w") as report_file:
        report_file.write(report_content)
    
    print("Report generated.")
    
    # Plotting performance metrics
    durations = [metric['duration'] for metric in metrics.values()]
    plt.figure(figsize=(10, 6))
    plt.bar(metrics.keys(), durations, color=['blue', 'green', 'red', 'purple', 'orange'])
    plt.xlabel('Media Type')
    plt.ylabel('Playback Duration (seconds)')
    plt.title('Playback Duration for Various Media Types')
    plt.savefig('playback_duration.png')
    plt.close()
    
    # Plotting error and warning counts
    plt.figure(figsize=(10, 6))
    plt.bar(['Errors', 'Warnings'], [error_count, warning_count], color=['red', 'orange'])
    plt.xlabel('Log Type')
    plt.ylabel('Count')
    plt.title('Error and Warning Counts')
    plt.savefig('log_summary.png')
    plt.close()

def capture_image():
    print("Capturing image...")
    execute_adb_command("adb shell am start -a android.media.action.IMAGE_CAPTURE")
    time.sleep(5)  # Wait for the image to be captured
    image_path = "/sdcard/DCIM/Camera/captured_image.jpg"
    execute_adb_command(f"adb pull {image_path} ./captured_image.jpg")
    print("Image captured and saved locally.")

def record_video(duration=10):
    print("Recording video...")
    execute_adb_command("adb shell am start -a android.media.action.VIDEO_CAPTURE")
    time.sleep(duration)  # Record video for the specified duration
    execute_adb_command("adb shell input keyevent 4")  # Stop recording
    video_path = "/sdcard/DCIM/Camera/captured_video.mp4"
    execute_adb_command(f"adb pull {video_path} ./captured_video.mp4")
    print("Video recorded and saved locally.")

def test_sensors():
    print("Testing sensors...")
    sensors = ["accelerometer", "gyroscope", "proximity"]
    sensor_data = {}
    for sensor in sensors:
        data = execute_adb_command(f"adb shell dumpsys sensorservice {sensor}")
        sensor_data[sensor] = data
        print(f"{sensor.capitalize()} data:", data)
    return sensor_data

def run_tests():
    metrics = {}
    for media_type, file_path in media_files.items():
        metrics[media_type] = play_media_with_recovery(file_path, media_type)
    
    capture_image()
    record_video()
    sensor_data = test_sensors()
    collect_logs()
    error_count, warning_count = analyze_logs("device_logs.txt")
    generate_report(metrics, error_count, warning_count, sensor_data)
    print("Multimedia System Testing completed.")
    return sensor_data, metrics, error_count, warning_count

def main():
    sensor_data, metrics, error_count, warning_count = run_tests()
    print(sensor_data, metrics, error_count, warning_count)

if __name__ == "__main__":
    main()

# Tkinter GUI
class MultimediaSystemTestingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multimedia System Testing Framework")
        
        # Instructions
        instructions = (
            "1. Enable Developer Mode on your Android device:\n"
            "   - Go to Settings > About phone > Tap Build number 7 times.\n"
            "2. Enable USB Debugging:\n"
            "   - Go to Settings > Developer options > Enable USB debugging.\n"
            "3. Connect your device to the computer via USB.\n"
        )
        
        self.instructions_label = tk.Label(root, text=instructions, justify="left")
        self.instructions_label.pack(pady=10)
        
        self.check_button = tk.Button(root, text="Check Device Connection", command=self.check_connection)
        self.check_button.pack(pady=10)
        
        self.run_button = tk.Button(root, text="Run Tests", command=self.run_tests_gui, state="disabled")
        self.run_button.pack(pady=20)
        
        self.status_label = tk.Label(root, text="")
        self.status_label.pack(pady=10)

    def check_connection(self):
        if check_device_connection():
            self.status_label.config(text="Device connected successfully.", fg="green")
            self.run_button.config(state="normal")
        else:
            self.status_label.config(text="No device connected. Please follow the instructions.", fg="red")
    
    def run_tests_gui(self):
        self.status_label.config(text="Running tests...", fg="blue")
        self.root.update()
        sensor_data, metrics, error_count, warning_count = run_tests()
        self.save_sensor_data_plots(sensor_data)
        self.status_label.config(text="Tests completed. Check the generated images for details.", fg="green")
        messagebox.showinfo("Test Results", "Tests completed. Check the generated images for details.")

    def save_sensor_data_plots(self, sensor_data):
        # Save sensor data visualization
        for sensor, data in sensor_data.items():
            data_lines = data.split('\n')
            values = [float(line.split()[-1]) for line in data_lines if len(line.split()) > 1 and line.split()[-1].replace('.', '', 1).isdigit()]
            
            plt.figure(figsize=(10, 4))
            plt.plot(values)
            plt.title(f"{sensor.capitalize()} Data")
            plt.xlabel('Time')
            plt.ylabel('Value')
            plt.savefig(f'{sensor}_data.png')
            plt.close()

            # Adding description and annotations
            description = f"The above graph represents the {sensor} sensor data. The X-axis shows the time intervals, and the Y-axis shows the sensor readings. This sensor data helps in determining the functionality and performance of the {sensor} sensor."
            with open(f'{sensor}_data_description.txt', 'w') as file:
                file.write(description)

root = tk.Tk()
app = MultimediaSystemTestingApp(root)
root.mainloop()
