import tkinter as tk
from tkinter import *
from PIL import Image, ImageTk, ImageDraw, ImageSequence
import time
import requests
import threading
import os
import pyttsx3
import queue
from geopy.geocoders import Photon

root = tk.Tk()
root.title("MK Weather")
root.geometry('405x455')
root.resizable(False, False)
root.configure(bg="#EEF7FF")
icon_image = ImageTk.PhotoImage(file='logo.png')  # Replace with the actual path to your .png file
root.iconphoto(False, icon_image)

engine = pyttsx3.init()
speech_queue = queue.Queue()

# Load the GIF using PIL
gif_path = "loading2.gif"  # Replace with your GIF file path
image = Image.open(gif_path)

# Create a list to hold the frames
frames = [ImageTk.PhotoImage(frame.copy()) for frame in ImageSequence.Iterator(image)]

# Create a label to display the GIF
loading_frame = tk.Label(root, bg="#7AB2B2")
loading_frame.place(x=145, y=115)  # Adjust to overlap with no_data label
loading_frame.place_forget()  # Hide it initially

def update_gif(frame_index):
    if loading_frame.winfo_ismapped():  # Only update if the frame is visible
        loading_frame.config(image=frames[frame_index])
        frame_index = (frame_index + 1) % len(frames)
        root.after(50, update_gif, frame_index)  # Slight delay to prevent lag

# Start the GIF update
update_gif(0)

# Load the logo image
logo = tk.PhotoImage(file='MkWeather Logo.png')
logo_label = tk.Label(root, image=logo, bg="#eef7ff")
logo_label.place(x=136, y=280)  # Corrected placement


# Error message label
error = tk.PhotoImage(file="caution-sign.png")
error_label = tk.Label(root , image = error, bg="#7ab2b2")
error_label.place(x=165, y=135)
error_label.place_forget()

city_not_found = tk.PhotoImage(file="no-location.png")
city_not_foundlabel = tk.Label(root, image=city_not_found, bg="#7ab2b2")
city_not_foundlabel.place(x=165, y=135)
city_not_foundlabel.place_forget()

no_internet= tk.PhotoImage(file="no-internet.png")
no_internetlabel = tk.Label(root , image = no_internet, bg="#7ab2b2")
no_internetlabel.place(x=165, y=135)
no_internetlabel.place_forget()

def speak_weather(city, temp):
    def speak():
        # Create a string that contains the weather information including the city
        weather_info = (
            f"The current temperature in {city} is {temp} degrees Celsius."
        )
        # Use the text-to-speech engine to speak the weather information
        engine.say(weather_info)
        engine.runAndWait()

    # Run the speak function in a separate thread
    threading.Thread(target=speak).start()

def map_condition_to_image(weather_description):
    # Define groups of weather descriptions that share a single image
    condition_mapping = {
        "thunderstorm": "thunderstorm.png",
        "mist": "haze.png",
        "haze": "haze.png",
        "drizzle": "rain.png",
        "few clouds": "few_clouds.png",
        "broken clouds":"broken_clouds.png",
        "overcast clouds":"broken_clouds.png",
        "rain": "rain.png",
        "snow": "snowflake.png",
        "clear sky": "sunny.png",
        "clouds": "cloud.png",
        "thunderstorm": "thunderstorm.png"
        
    }

    # Map the description to a generalized condition
    for condition in condition_mapping:
        if condition in weather_description:
            return condition_mapping[condition]
    
    return "sunny.png"  # Default image if no match

weather_icon_label = tk.Label(root, bg="#7AB2B2")
weather_icon_label.place(x=245, y=135)
weather_icon_label.place_forget()

feelslike=tk.Label(root,text="FEELS LIKE:", font=("Arial",10,"bold"),fg="#EEF7FF", bg="#7AB2B2")
feelslike.place(x=76, y=180)
feelslike.place_forget()


def hide_all_data():
    widgets_to_hide = [t, f, weather_icon_label, feelslike]
    
    for widget in widgets_to_hide:
        widget.place_forget()


def create_rounded_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1 + radius, y1,
              x1 + radius, y1,
              x2 - radius, y1,
              x2 - radius, y1,
              x2, y1,
              x2, y1 + radius,
              x2, y1 + radius,
              x2, y2 - radius,
              x2, y2 - radius,
              x2, y2,
              x2 - radius, y2,
              x2 - radius, y2,
              x1 + radius, y2,
              x1 + radius, y2,
              x1, y2,
              x1, y2 - radius,
              x1, y2 - radius,
              x1, y1 + radius,
              x1, y1 + radius,
              x1, y1]

    return canvas.create_polygon(points, **kwargs, smooth=True)


import asyncio
import aiohttp

async def fetch_weather_data_async(city):
    try:
        error_label.place_forget()  
        city_not_foundlabel.place_forget()
        no_internetlabel.place_forget()
        
        loading_frame.place(x=145, y=115)
        loading_frame.lift()

        update_gif(0)

        geolocator = Photon(user_agent="geoapiExercises")
        location = geolocator.geocode(city, timeout=10)

        if location is None:
            raise ValueError("City not found!")

        api_key = "81120648e9e5b99bdad49fe4ba26230d"
        api_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=10) as response:
                data = await response.json()

        if response.status != 200:
            error_message = data.get('Error!')
            raise ValueError(error_message.capitalize())

        update_sliding_windows(data)
        
        
        temp = data['main']['temp']
        weather_description = data['weather'][0]['description'].lower()
        feels_like = data['main']['feels_like']
        weather_pressure= data['main']['pressure']
        weather_wind=data['wind']['speed']
        weather_humidity=data['main']['humidity']
        # Map weather description to image
        image_path = map_condition_to_image(weather_description)
        weather_icon = ImageTk.PhotoImage(Image.open(image_path))

        # Update temperature label
        t.config(text=f"{temp}°       ")
        t.place(x=85, y=130)
        t.lift()
        f.config(text=f"{feels_like}°C       ")
        f.place(x=160, y=180)
        f.lift()
      
        h.config(text=(weather_humidity, "%"))
        p.config(text=(weather_pressure, 'hPa'))
        w.config(text=(weather_wind, 'm/s'))
        d.config(text=(weather_description))

        feelslike.place(x=76, y=180)
        feelslike.lift()
        # Display the weather icon
        weather_icon_label.config(image=weather_icon)
        weather_icon_label.image = weather_icon
        weather_icon_label.place(x=245, y = 135)
        weather_icon_label.lift()

        
        loading_frame.place_forget()
        root.after(0, speak_weather, city, temp)

    except aiohttp.ClientError:
        if not no_internetlabel.winfo_ismapped():
            no_internetlabel.place(x=165, y=135)
            no_internetlabel.lift()
            root.after(5000, no_internetlabel.place_forget)
            
        loading_frame.place_forget()

    except ValueError:
        if not city_not_foundlabel.winfo_ismapped():
            city_not_foundlabel.place(x=165, y=135)
            city_not_foundlabel.lift()
            root.after(5000, city_not_foundlabel.place_forget)
        
        loading_frame.place_forget()

    except Exception as e:
        if not error_label.winfo_ismapped():
            error_label.place(x=165, y=135)
            error_label.lift()
            root.after(5000, error_label.place_forget)

        loading_frame.place_forget()

def fetch_weather_data(city):
    asyncio.run(fetch_weather_data_async(city))


def slide_window(window, start_x, end_x, speed=5):
    current_x = start_x
    step = (end_x - start_x) / abs(end_x - start_x) * speed
    
    def perform_slide():
        nonlocal current_x
        current_x += step
        
        # Check if the window has reached or surpassed the end position
        if (step > 0 and current_x >= end_x) or (step < 0 and current_x <= end_x):
            window.place(x=end_x, y=window.winfo_y())  # Place at the exact end position
        else:
            window.place(x=current_x, y=window.winfo_y())
            window.after(10, perform_slide)
    
    perform_slide()


def update_sliding_windows(data):
    # Extract data for sliding windows
    temperature = f"Temperature: {data['main']['temp']}°C"
    min_temp = f"Min: {data['main']['temp_min']}°C"
    max_temp = f"Max: {data['main']['temp_max']}°C"
    feels_like = f"Feels Like: {data['main']['feels_like']}°C"
    pressure = f"Pressure: {data['main']['pressure']} hPa"
    
    wind_speed = f"Wind Speed: {data['wind']['speed']} m/s"
    wind_dir = f"Wind Direction: {data['wind']['deg']}°"
    humidity = f"Humidity: {data['main']['humidity']}%"
    uv_index = "UV Index: N/A"  # Placeholder
    visibility = f"Visibility: {data['visibility']} m"
    
    left_window_bg_color = "#cde8e5"
    right_window_bg_color = "#cde8e5"
    
    # Update the left window content and background color
    left_window_content = [temperature, min_temp, max_temp, feels_like, pressure]
    update_canvas_content(left_window, left_window_content, left_window_bg_color)

    # Update the right window content and background color
    right_window_content = [wind_speed, wind_dir, humidity, uv_index, visibility]
    update_canvas_content(right_window, right_window_content, right_window_bg_color)

    # Perform the sliding effect
    slide_window(left_window, start_x=-70, end_x=5)  # Slide left window to the right
    slide_window(right_window, start_x=300, end_x=230)  # Slide right window to the left

def update_canvas_content(canvas, content, bg_color):
    # Clear existing content
    canvas.delete("all")
    canvas.config(bg=bg_color or "#cde8e5")
    logo_label.place_forget()    
    # Add new content inside the canvas
    for i, text in enumerate(content):
        canvas.create_text(20, 20 + i*25, anchor="nw", text=text, font=("poppins", 10), fill="#4d869c")

def speak_from_queue():
    while not speech_queue.empty():
        # Get the next message from the queue
        message = speech_queue.get()

        # Stop any ongoing speech
        engine.stop()

        # Speak the new message
        engine.say(message)
        engine.runAndWait()

        # Sleep for a short period to ensure speech completes
        time.sleep(1)

def speak_weather_details():
    city = textfield.get()

    if not city:
        # If city name is not entered, show an error message
        city_not_foundlabel.winfo_ismapped()  # Only show if not already visible
        city_not_foundlabel.place(x=165, y=135)
        city_not_foundlabel.lift()
        root.after(5000, city_not_foundlabel.place_forget)
        return

    # Check if weather data is available (checking the temperature label as an example)
    if not t.cget('text'):
        # If weather data is not available, show an error message
        error_label.winfo_ismapped()
        error_label.place(x=165, y=135)
        error_label.lift()
        root.after(5000, error_label.place_forget)
        return

    # Extract and format the details from the labels
    feels_like_text = f"Feels like: {f.cget('text')}."
    humidity_text = f"Humidity: {h.cget('text')}."
    pressure_text = f"Pressure: {p.cget('text')}."
    wind_text = f"Wind speed: {w.cget('text')[0]} meters per second."
    description_text = f"Description: {d.cget('text')}"

    # Combine the details into a single string
    weather_details = (
        f"{feels_like_text} {humidity_text} {pressure_text} {wind_text} {description_text}"
    )

    # Clear any previous error message
    

    # Add the weather details to the speech queue
    speech_queue.put(weather_details)

    # Start the speech synthesis in a separate thread
    threading.Thread(target=speak_from_queue).start()
def getweather(event=None):
    city = textfield.get().strip()

    if city and city.lower() != 'Enter City!':
        # Start a new thread to fetch data without blocking the UI
        t.config(text="")
        f.config(text="")
        hide_all_data()
       
        threading.Thread(target=fetch_weather_data, args=(city,)).start()
    else:
        
        hide_all_data()
        city_not_foundlabel.place(x=165, y=135)
        city_not_foundlabel.lift()
       
        root.after(5000, city_not_foundlabel.place_forget) 


def process_image(file_path, convert_to_rgba=True):
    image = Image.open(file_path)
    if convert_to_rgba:
        image = image.convert("RGBA")
    datas = image.getdata()
    new_data = [(255, 255, 255, 0) if item[0] in range(200, 256) and item[1] in range(200, 256) and item[2] in range(200, 256) else item for item in datas]
    image.putdata(new_data)
    return ImageTk.PhotoImage(image)

image_tk = process_image("Search_box.png")
myimage = tk.Label(root, image=image_tk, bg="#EEF7FF")
myimage.place(x=9, y=12)

textfield = tk.Entry(root, justify="center", font=("poppins", 18, "bold"), bg="#4D869C", border=0, fg="#ffd89c")
textfield.place(x=37, y=19, height=40, width=195)
textfield.insert(0, 'Enter City!')
textfield.bind('<FocusIn>', lambda e: textfield.delete(0, "end") if textfield.get() == 'Enter City!' else None)
textfield.bind('<FocusOut>', lambda e: textfield.insert(0, 'Enter City!') if textfield.get() == '' else None)
textfield.bind("<Return>", getweather)


Search_icon = tk.PhotoImage(file="Search_icon.png")
myimage_icon = tk.Button(image=Search_icon, borderwidth=0, cursor="hand2", bg="#4d869c", activebackground="#4d869c", command= getweather)
myimage_icon.place(x=245, y=26)


voice_icon = tk.PhotoImage(file="speaking (4).png")
voice_button = tk.Button(root, image=voice_icon, borderwidth=0, cursor="hand2", bg="#eef7ff", activebackground="#eef7ff", command=speak_weather_details)
voice_button.place(x=285, y=7)

def round_corners(image, radius):
    mask = Image.new('L', (image.size[0] * 2, image.size[1] * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, mask.size[0], mask.size[1]), radius=radius * 2, fill=255)
    mask = mask.resize(image.size, Image.LANCZOS)
    rounded_image = Image.new('RGBA', image.size)
    rounded_image.paste(image, (0, 0), mask=mask)
    return rounded_image

rounded_pil_image1 = round_corners(Image.open("Current_weather.png"), radius=20)
my_image1 = ImageTk.PhotoImage(rounded_pil_image1)
tk.Label(root, image=my_image1, bg="#EEF7FF").place(x=49, y=85)

tk.Label(root, text="CURRENT WEATHER", font=("arial", 15, "bold"), fg="#EEF7FF", bg="#7AB2B2").place(x=93, y=92)
no_data = PhotoImage(file="nodata.png")
no_data_label = Label(root, image=no_data, font=("arial", 19, "bold"), fg="#ffd89c", bg="#7AB2B2").place(x=165, y=140)


t = tk.Label(root, font=("Arial", 30, "bold"), fg="#ffd89c", bg="#7ab2b2")
t.place(x=85, y=130)
f = tk.Label(root, font=("Arial", 10, "bold"), fg = "#ffd89c", bg="#7ab2b2")
f.place(x=160, y=180)
p = tk.Label(root, font=("Arial", 10, "bold"), fg = "#ffd89c", bg="#7ab2b2")
p.place_forget()
h = tk.Label(root, font=("Arial", 10, "bold"), fg = "#ffd89c", bg="#7ab2b2")
h.place_forget()
d = tk.Label(root, font=("Arial", 10, "bold"), fg = "#ffd89c", bg="#7ab2b2")
d.place_forget()
w = tk.Label(root, font=("Arial", 10, "bold"), fg = "#ffd89c", bg="#7ab2b2")
w.place_forget()



def focus_search(event):
    global last_space_time
    current_time = time.time()
    
    # Check if the time between two spacebar presses is less than 0.5 seconds
    if current_time - last_space_time < 0.5:
        textfield.focus_set()  # Set focus to the textfield
    last_space_time = current_time

root.bind('<space>', focus_search)


def create_sliding_window(side, start_x, target_x, label_content, corner_radius=20):
    frame_width = 170
    frame_height = 170
    
    # Create a Canvas for rounded rectangle
    canvas = tk.Canvas(root, width=frame_width, height=frame_height, bg="#EEF7FF", highlightthickness=0)
    canvas.place(x=start_x, y=270)
    create_rounded_rectangle(canvas, 0, 0, frame_width, frame_height, radius=corner_radius, fill="#cde8e5")

    def animate_window(target_x):
        step_size = 10
        current_x = canvas.winfo_x()

        if current_x < target_x:
            canvas.place(x=current_x + step_size)
        elif current_x > target_x:
            canvas.place(x=current_x - step_size)

        if abs(current_x - target_x) > step_size:
            root.after(10, animate_window, target_x)
        else:
            canvas.place(x=target_x)  # Ensure final position is set correctly

    def toggle_window():
        if not hasattr(canvas, 'is_open'):
            canvas.is_open = False
        
        if canvas.is_open:
            animate_window(start_x)
        else:
            animate_window(target_x)
        canvas.is_open = not canvas.is_open

    # Place labels inside the canvas
    for i, text in enumerate(label_content):
        canvas.create_text(20, 20 + i*25, anchor="nw", text=text, font=("poppins", 10), fill="#4d869c")

    canvas.bind('<Button-1>', lambda e: toggle_window())

    return canvas


left_content =  [
    "Temperature: --°C",
    "Min: --°C",
    "Max: --°C",
    "Feels Like: --°C",
    "Pressure: -- hPa"
]
right_content = [
    "Wind Speed: -- km/h",
    "Wind Direction: --°",
    "Humidity: --%",
    "UV Index: N/A",
    "Visibility: N/A m"
]
left_window = create_sliding_window('left', start_x=-70, target_x=5, label_content=left_content)
right_window = create_sliding_window('right', start_x=300, target_x=230, label_content=right_content)

def open_shortcut_file():
    # Open the shortcut.txt file directly
    file_path = "information.txt"  # Replace with the actual path to your shortcut.txt
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Create a new Toplevel window to display the file content
        view_window = tk.Toplevel(root, bg="#EEF7FF")
        view_window.title("More Info.")
        view_window.geometry('380x270')
        icon_image1 = ImageTk.PhotoImage(file='logo.png') 
        view_window.iconphoto(False, icon_image1)
        
        # Create a Text widget and insert the content
        text_widget = tk.Text(view_window, wrap='word', width=100, height=20, bg="#EEF7FF", fg="#345b45", borderwidth=0)
        text_widget.insert('1.0', content)
        text_widget.configure(state='disabled')  # Set to read-only mode
        text_widget.pack(expand=True, fill='both', padx=10, pady=10)

# canvas and info frame setup
canvas_height = 70
canvas_width = 255
canvas = Canvas(root, width=canvas_width, height=canvas_height, bg="#cde8e5", highlightthickness=0)
canvas.place(x=510, y=7)

info_frame = tk.Frame(canvas, width=canvas_width, bg="#cde8e5")
canvas.create_window((0, 0), window=info_frame, anchor="nw")
info_frame.lift()

feature_image = ImageTk.PhotoImage(Image.open("features.png"))  # Replace with your image file path
feature_button = tk.Button(info_frame, image=feature_image, borderwidth=0, cursor="hand2", bg="#cde8e5", activebackground="#cde8e5", command=open_shortcut_file)
feature_button.pack(pady=1, padx=1)

feature_label= Button(canvas, text='Click here for more', font=("poppins", 10, "bold"), bg="#cde8e5", fg = "#4d869c",activeforeground="#ffd89c",activebackground="#cde8e5", borderwidth=0, command = open_shortcut_file)
feature_label.place(x=60, y = 14)

feature_label1= Button(canvas, text="Info.", font=("poppins", 10, "bold"), bg="#cde8e5", fg = "#4d869c",activeforeground="#ffd89c",activebackground="#cde8e5", borderwidth=0, command=open_shortcut_file)
feature_label1.place(x=60, y = 32)



# Animation function
def animate_info_frame(target_x, zoom_in):
    step_size = 30
    zoom_step = 0.2
    
    def update_frame():
        nonlocal target_x
        
        scale = 1 + zoom_step if zoom_in else 1 - zoom_step
        canvas.scale('all', 0, 0, scale, scale)
        
        current_x = canvas.winfo_x()
        if zoom_in and current_x > target_x:
            canvas.place(x=current_x - step_size)
            root.after(5, update_frame)
        elif not zoom_in and current_x < target_x:
            canvas.place(x=current_x + step_size)
            root.after(5, update_frame)
    
    update_frame()

def toggle_info_frame():
    if canvas.winfo_x() >= 405:
        info_button.config(bg="#cde8e5", activebackground="#cde8e5")
        animate_info_frame(405 - canvas_width, zoom_in=True)
    else:
        info_button.config(bg="#EEF7FF", activebackground="#EEF7FF")
        animate_info_frame(405, zoom_in=False)
# Bind the function to a button
info_icon = tk.PhotoImage(file="information-button.png")
info_button = tk.Button(root, image=info_icon, borderwidth=0, cursor="hand2", bg="#EEF7FF", activebackground="#EEF7FF", command=toggle_info_frame)
info_button.place(x=340, y=7)

last_space_time = 0

root.mainloop()
