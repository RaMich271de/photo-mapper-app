import os
import folium
import threading
import webbrowser
import http.server
import socketserver
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.core.clipboard import Clipboard
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
import base64
from io import BytesIO

MAP_FILE = "fotokarte.html"
PORT = 8000


# <<< HIER IST DER FIX FÜR DEN PC-SERVER
# Wir erstellen eine eigene Server-Klasse, die die Wiederverwendung der Adresse erlaubt.
class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True


class PhotoMapperLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 10
        self.map_file_path = None
        self.httpd = None

        self.status_label = Label(
            text="Willkommen!\n\nOrdner mit Fotos auswählen,\num eine Karte zu erstellen.",
            font_size='18sp', halign='center', valign='middle', size_hint_y=0.6
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.add_widget(self.status_label)

        self.progress_bar = ProgressBar(max=100, size_hint_y=0.05, opacity=0)
        self.add_widget(self.progress_bar)

        self.open_button = Button(
            text="Ordner auswählen & Karte erstellen", font_size='20sp', size_hint_y=0.1
        )
        self.open_button.bind(on_press=self.show_file_chooser)
        self.add_widget(self.open_button)

        if platform == 'android':
            self.result_button = Button(
                text="Anleitung & Pfad kopieren", font_size='20sp', size_hint_y=0.1, disabled=True,
                background_color=(0.5, 0.5, 0.5, 1)
            )
            self.result_button.bind(on_press=self.copy_path_and_show_instructions)
        else:
            self.result_button = Button(
                text="Karte im Browser anzeigen", font_size='20sp', size_hint_y=0.1, disabled=True,
                background_color=(0.5, 0.5, 0.5, 1)
            )
            self.result_button.bind(on_press=self.start_server_and_open_browser)

        self.add_widget(self.result_button)

        self.quit_button = Button(
            text="App beenden",
            font_size='20sp',
            size_hint_y=0.1,
            background_color=(0.9, 0.3, 0.3, 1)
        )
        self.quit_button.bind(on_press=self.quit_app)
        self.add_widget(self.quit_button)

    # --- ÜBERARBEITETE SERVER-LOGIK ---
    def start_server_and_open_browser(self, instance):
        if not self.map_file_path: return
        # Wir starten den Server nur, wenn er nicht bereits läuft.
        if self.httpd is None:
            threading.Thread(target=self.run_server_once, daemon=True).start()
        else:
            print("Server läuft bereits, öffne nur den Browser.")

        # Das Öffnen des Browsers geschieht sicher im Haupt-Thread.
        Clock.schedule_once(self.open_browser_url, 0.2)

    def run_server_once(self, *args):
        map_dir = os.path.dirname(self.map_file_path)

        class MyHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=map_dir, **kwargs)

        # Verwende unsere neue, wiederverwendbare Server-Klasse
        self.httpd = ReusableTCPServer(("localhost", PORT), MyHandler)
        print(f"Server gestartet auf http://localhost:{PORT}")
        self.httpd.handle_request()
        self.stop_server()

    def open_browser_url(self, dt):
        url = f"http://localhost:{PORT}/{os.path.basename(self.map_file_path)}"
        self.status_label.text = f"Öffne {url}"
        webbrowser.open(url)

    def stop_server(self):
        if self.httpd:
            server = self.httpd
            self.httpd = None
            server.server_close()  # Schließt den Socket sofort
            print("Server wurde gestoppt.")

    def quit_app(self, instance):
        self.stop_server()
        App.get_running_app().stop()

    # --- Rest des Codes ist unverändert ---
    def copy_path_and_show_instructions(self, instance):
        if self.map_file_path and os.path.exists(self.map_file_path):
            Clipboard.copy(self.map_file_path)
            instructions = (
                "[b]Pfad zur Karte kopiert![/b]\n\n"
                "ANLEITUNG:\n"
                "1. Öffne deine 'Dateien'-App.\n"
                "2. Füge den Pfad in die Suche ein.\n"
                "3. Öffne die Karte mit 'HTML Viewer'."
            )
            self.status_label.markup = True
            self.status_label.text = instructions
        else:
            self.status_label.text = "Kartendatei nicht gefunden."

    def show_file_chooser(self, instance):
        start_path = os.path.expanduser('~') if platform != 'android' else "/storage/emulated/0/"
        filechooser = FileChooserListView(path=start_path)
        popup_layout = BoxLayout(orientation='vertical')
        popup_layout.add_widget(filechooser)
        btn_layout = BoxLayout(size_hint_y=0.1)
        select_btn = Button(text="Diesen Ordner wählen")
        cancel_btn = Button(text="Abbrechen")
        btn_layout.add_widget(cancel_btn)
        btn_layout.add_widget(select_btn)
        popup_layout.add_widget(btn_layout)
        popup = Popup(title="Wähle den Ordner mit deinen Fotos", content=popup_layout, size_hint=(0.9, 0.9))

        def select_folder(instance):
            folder_path = filechooser.path
            if os.path.isdir(folder_path):
                self.start_processing(folder_path)
                popup.dismiss()

        select_btn.bind(on_press=select_folder)
        cancel_btn.bind(on_press=popup.dismiss)
        popup.open()

    def start_processing(self, folder_path):
        self.status_label.text = f"Analysiere Ordner:\n{folder_path}"
        self.open_button.disabled = True
        self.result_button.disabled = True
        self.result_button.background_color = (0.5, 0.5, 0.5, 1)
        self.progress_bar.value = 0
        self.progress_bar.opacity = 1
        threading.Thread(target=self.process_images_thread, args=(folder_path,)).start()

    @mainthread
    def update_progress(self, value):
        self.progress_bar.value = value

    @mainthread
    def update_status(self, text):
        self.status_label.text = text

    @mainthread
    def processing_finished(self, result_message, map_path=None):
        self.status_label.text = result_message
        self.open_button.disabled = False
        self.progress_bar.opacity = 0
        if map_path:
            self.map_file_path = map_path
            self.result_button.disabled = False
            self.result_button.background_color = (0.2, 0.6, 0.2, 1)
        else:
            self.map_file_path = None
            self.result_button.disabled = True
            self.result_button.background_color = (0.5, 0.5, 0.5, 1)

    def get_exif_data(self, image_path):
        try:
            image = Image.open(image_path)
            exif_data = image._getexif()
            if not exif_data: return None
            decoded_exif = {TAGS.get(t, t): v for t, v in exif_data.items()}
            gps_info_raw = decoded_exif.get("GPSInfo")
            if not gps_info_raw: return None
            decoded_gps = {GPSTAGS.get(t, t): v for t, v in gps_info_raw.items()}
            lat_dms = decoded_gps.get("GPSLatitude")
            lon_dms = decoded_gps.get("GPSLongitude")
            lat_ref = decoded_gps.get("GPSLatitudeRef")
            lon_ref = decoded_gps.get("GPSLongitudeRef")
            if lat_dms and lon_dms and lat_ref and lon_ref:
                lat = (lat_dms[0] + lat_dms[1] / 60.0 + lat_dms[2] / 3600.0) * (-1 if lat_ref in ['S', 's'] else 1)
                lon = (lon_dms[0] + lon_dms[1] / 60.0 + lon_dms[2] / 3600.0) * (-1 if lon_ref in ['W', 'w'] else 1)
                return {"lat": lat, "lon": lon}
        except Exception:
            return None

    def create_thumbnail_html(self, image_path):
        try:
            img = Image.open(image_path)
            img.thumbnail((200, 200))
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            filename = os.path.basename(image_path)
            return f'<img src="data:image/jpeg;base64,{img_str}"><br><b>{filename}</b>'
        except Exception:
            return os.path.basename(image_path)

    def process_images_thread(self, root_dir):
        locations = []
        self.update_status("Suche nach Fotos mit GPS-Daten...")
        all_files = [os.path.join(s, f) for s, _, files in os.walk(root_dir) for f in files if
                     f.lower().endswith(('.jpg', '.jpeg'))]

        for i, image_path in enumerate(all_files):
            self.update_status(f"Prüfe Bild {i + 1}/{len(all_files)}...")
            coords = self.get_exif_data(image_path)
            if coords:
                locations.append({"path": image_path, "coords": coords})

        if not locations:
            self.update_status("Keine Fotos mit GPS-Daten gefunden.\nErstelle eine leere Deutschland-Karte.")
            photo_map = folium.Map(location=[51.16, 10.45], zoom_start=6)
        else:
            self.update_status(f"Erstelle Karte mit {len(locations)} Fotos...")
            total_steps = len(locations) + 1
            photo_map = folium.Map()

            for i, loc in enumerate(locations):
                popup_html = self.create_thumbnail_html(loc["path"])
                popup = folium.Popup(popup_html, max_width=250)
                folium.Marker(location=[loc["coords"]["lat"], loc["coords"]["lon"]], popup=popup,
                              icon=folium.Icon(color='blue', icon='camera', prefix='fa')).add_to(photo_map)
                progress_value = ((i + 1) / total_steps) * 100
                self.update_progress(progress_value)

            bounds = [[loc['coords']['lat'], loc['coords']['lon']] for loc in locations]
            photo_map.fit_bounds(bounds, padding=(20, 20))

        self.update_status("Karte wird gespeichert...")
        save_path = os.path.join(root_dir, MAP_FILE)
        photo_map.save(save_path)
        self.update_progress(100)

        result_message = f"Fertig! Klicke unten, um fortzufahren."
        self.processing_finished(result_message, map_path=save_path)


class PhotoMapApp(App):
    def build(self):
        self.layout = PhotoMapperLayout()
        return self.layout

    def on_stop(self):
        self.layout.stop_server()


if __name__ == "__main__":
    PhotoMapApp().run()