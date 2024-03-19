import os
import obspython as obs
import json 
import os.path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
import time

# TODO : Implements saving and loading settings to a json file (backup settings)

class GlobalData:
    def __init__(self) -> None:
        self.http_service : TCPServer = None
        self.server_running : bool = False
        self.obs_properties = None
        self.obs_data = None
        self.debug : bool = True
        self.shutdown_requested : bool = False


    def serve_settings(self):
        try:
            self.server_running = True
            with TCPServer(("", PORT), SettingsRequestHandler) as service:
                self.http_service = service
                self.debug_message(f"Serving on port {PORT}")
                service.serve_forever(0.5)
                self.debug_message('Server shutdown.')
        finally:
            self.server_running = False
            if self.http_service:
                self.http_service.server_close()
                self.http_service = None


    def start_server_asynch(self, retry_freq : float = 0.5, tiemout : float = 10.0):
        server_thread : Thread = Thread(name="HTTP Server", target=lambda: self.start_server(retry_freq, tiemout), daemon=False)
        server_thread.start()

    
    def start_server(self, retry_freq : float = 0.5, tiemout : float = 10.0):
        self.shutdown_requested = False
        start_time : float = time.process_time()
        while tiemout == None or (time.process_time() - start_time) < tiemout:
            if self.shutdown_requested: break
            try:
                self.debug_message('Starting settings server...')
                self.serve_settings()
            except BaseException as error:
                self.debug_message(f'Unable to start server: {error}')
                if self.shutdown_requested or retry_freq == None: break
                time.sleep(retry_freq)
            

    def debug_message(self, msg : str):
        if self.debug: print(msg)

    def shutdown_server(self):
        self.shutdown_requested = True
        if self.server_running:
            self.http_service.shutdown()
    
    def dereference_data(self):
        self.obs_properties = None
        self.obs_data = None
        
    def shutdown_server_async(self):
        # TODO: Results in deadlock; No idea how fix.
        watcher_thread : Thread = Thread(name="Server Shutdown Watcher", target=self.shutdown_server, daemon=False)
        watcher_thread.start()




class SettingsRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        GLOBAL_DATA.debug_message("Received request: " + self.path)

        query_param = self.path

        if query_param == '/?settings':
            self.handle_settings_request()
        else:
            self.send_error(404, "Invalid Request.", "Monitor config only supports settings requests.")
            GLOBAL_DATA.debug_message("Request rejected.")

    def handle_settings_request(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        settings_data = json.dumps(settings_as_dict(GLOBAL_DATA.obs_data))
        GLOBAL_DATA.debug_message(settings_data)
        self.wfile.write(settings_data.encode())
        GLOBAL_DATA.debug_message("Request handled.")
    
    def log_message(self, format: str, *args) -> None:
        if GLOBAL_DATA.debug: super().log_message(format, *args)




GLOBAL_DATA : GlobalData = GlobalData()
RETRY_FREQUENCY : float = 0.5
PORT = 6005
CONFIG_FILE : str = os.path.relpath(__file__) + os.path.sep + "config.json"




def script_load(settings):
    script_unload()
    GLOBAL_DATA.obs_data = settings
    GLOBAL_DATA.start_server_asynch(RETRY_FREQUENCY)




def script_unload():
    GLOBAL_DATA.shutdown_server_async()
    GLOBAL_DATA.dereference_data()




def script_defaults(settings):
    obs.obs_data_set_default_array(settings, "_filters", obs.obs_data_array_create())
    obs.obs_data_set_default_string(settings, "_pass", "secret-password")
    obs.obs_data_set_default_bool(settings, "_use_pass", False)
    obs.obs_data_set_default_string(settings, "_address", "127.0.0.1")
    obs.obs_data_set_default_int(settings, "_port", 4455)
    obs.obs_data_set_default_int(settings, "_color", int("ff32Cd32", 16))




def script_description():
    return "Add or remove filters from the filter monitor."




def on_debug_toggled(props, prop, *args, **kwargs):
    GLOBAL_DATA.debug = not GLOBAL_DATA.debug
    debug_btn = obs.obs_properties_get(props, "_debug")
    obs.obs_property_set_description(debug_btn, f'Debug {"Enabled" if GLOBAL_DATA.debug else "Disabled"}')
    return True




def script_properties():

    props = obs.obs_properties_create()
    obs.obs_properties_add_editable_list(props, "_filters", "Filters: ", obs.OBS_EDITABLE_LIST_TYPE_STRINGS, "", "")

    obs.obs_properties_add_text(props, "_source", "Source: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "_filter", "Filter: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "_name", "Display Name: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_color(props, "_color", "Active Color: ")
    obs.obs_properties_add_button(props, "add_button", "Add Filter", add_filter_callback)

    obs.obs_properties_add_text(props, "_address", "Address: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "_port", "Port: ", 0, 65535, 1)

    obs.obs_properties_add_text(props, "_pass", "Password: ", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_button(props, "_debug", "Debug Disabled", on_debug_toggled)

    #obs.obs_properties_add_button(props, "save_button", "Save Settings", save_config)

    GLOBAL_DATA.obs_properties = props

    return props




def save_config():
    mode : str = "w" if os.path.exists(CONFIG_FILE) else "x"
    with open(CONFIG_FILE, mode) as file:
        file.write(json.dumps(settings_as_dict()))




def settings_as_dict(settings) -> dict:
    hostAddress = obs.obs_data_get_string(settings, "_address")
    port = obs.obs_data_get_int(settings, "_port")
    obsPassword = obs.obs_data_get_string(settings, "_pass")

    return { "obsHost": f'{hostAddress}:{port}',
            "obsPassword":obsPassword,
            "filterlist": get_filters(settings) }




def get_filters(settings):
    swing_array = obs.obs_data_get_array(settings, "_filters")
    array_size = obs.obs_data_array_count(swing_array)
    filters : list[dict] = []
    for i in range(array_size):
        swing_item = obs.obs_data_array_item(swing_array, i)
        filters.append(item_to_dict(swing_item))
    return filters




def item_to_dict(swing_array_item) -> dict:
    obj = obs.obs_data_get_json(swing_array_item)
    return json.loads(json.loads(obj)["value"])



## TODO : remove or integrate
def load_config() :
    if not os.path.exists(CONFIG_FILE): raise FileNotFoundError("Unable to locate config file: %s" % os.path.abspath(CONFIG_FILE))
    with open(CONFIG_FILE, "r") as file:
        json_str : str = file.read()
    config : dict = json.loads(s=file.read())
    filters = config["filterlist"]
    hostAddress = config["hostAddress"]
    port = config["port"]
    obsPassword = config["obsPassword"]




def add_filter_callback(props, prop, *args, **kwargs):
    data = GLOBAL_DATA.obs_data
    add_filter(
        data,
        filterName=obs.obs_data_get_string(data, "_filter"),
        sourceName=obs.obs_data_get_string(data, "_source"),
        displayName=obs.obs_data_get_string(data, "_name"),
        onColor=f'#{hex(obs.obs_data_get_int(data, "_color"))[4:]}'
    )
    return True




def add_filter(data, filterName : str, sourceName : str, displayName : str = None, onColor : str = None):
    swing_data = obs.obs_data_get_array(data, "_filters")
    item_as_json = create_list_item_json(filterName, sourceName, displayName, onColor)
    item = obs.obs_data_create_from_json(item_as_json)
    GLOBAL_DATA.debug_message(item)
    obs.obs_data_array_push_back(swing_data, item)
    obs.obs_data_set_array(data, "_filters", swing_data)




def create_list_item_json(filterName : str, sourceName : str, displayName : str = None, onColor : str = None) -> str:
    filter = '{\\\"filterName\\\": \\\"%s\\\", \\\"sourceName\\\": \\\"%s\\\"' % (filterName, sourceName)
    if displayName != None: filter += f', \\\"displayName\\\": \\\"{displayName}\\\"'
    if onColor != None: filter += f', \\\"onColor\\\": \\\"{onColor}\\\"'
    filter += "}"
    return '{"value":"%s","selected":false,"hidden":false}' % filter