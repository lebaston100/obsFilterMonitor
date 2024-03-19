import os
import obspython as obs
import json 
import os.path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread
import time

# TODO : Implement saving and loading settings to a json file (backup settings)
# TODO : Implement retry/cancel craete server (UI Button and functions)


class ReusableServer(TCPServer):
    allow_reuse_address = True
    allow_reuse_port = True




class ScriptContext:
    def __init__(self) -> None:
        self.http_service : TCPServer = None
        self.server_running : bool = False
        self.obs_properties = None
        self.obs_data = None
        self.debug : bool = False
        self.shutdown_requested : bool = False


    def serve_settings(self):
        try:
            self.server_running = True
            with ReusableServer(("", PORT), SettingsRequestHandler) as service:
                self.http_service = service
                self.debug_message(f"Serving on port {PORT}")
                service.serve_forever(0.5)
                self.debug_message('Server shutdown.')
        finally:
            self.server_running = False
            if self.http_service:
                self.http_service.server_close()
                self.http_service = None


    def start_server_asynch(self, retry_delay : float = None, tiemout : float = None):
        server_thread : Thread = Thread(name="HTTP Server", target=lambda: self.start_server(retry_delay, tiemout), daemon=True)
        server_thread.start()

    
    def start_server(self, retry_delay : float = None, tiemout : float = None):
        self.shutdown_requested = False
        start_time : float = time.process_time()
        while tiemout == None or (time.process_time() - start_time) < tiemout:
            if self.shutdown_requested: break
            try:
                self.debug_message('Starting settings server...')
                self.serve_settings()
            except BaseException as error:
                self.debug_message(f'Unable to start server: {error}')
                if self.shutdown_requested or retry_delay == None: break
                time.sleep(retry_delay)
            

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
        watcher_thread : Thread = Thread(name="Server Shutdown Watcher", target=self.shutdown_server, daemon=True)
        watcher_thread.start()




class SettingsRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        SCRIPT_CONTEXT.debug_message("Received request: " + self.path)

        query_param = self.path

        if query_param == '/?settings':
            self.handle_settings_request()
        else:
            self.send_error(404, "Invalid Request.", "Monitor config only supports settings requests.")
            SCRIPT_CONTEXT.debug_message("Request rejected.")

    def handle_settings_request(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        settings_data = json.dumps(settings_as_dict(SCRIPT_CONTEXT.obs_data))
        SCRIPT_CONTEXT.debug_message(settings_data)
        self.wfile.write(settings_data.encode())
        SCRIPT_CONTEXT.debug_message("Request handled.")
    
    def log_message(self, format: str, *args) -> None:
        if SCRIPT_CONTEXT.debug: super().log_message(format, *args)




SCRIPT_CONTEXT : ScriptContext = ScriptContext()
DEFAULT_RETRY_FREQUENCY : float = 0.5
DEFAULT_RETRY_DURATION : float = 10.0
PORT = 6005
CONFIG_FILE : str = os.path.relpath(__file__) + os.path.sep + "config.json"




def script_load(settings):
    script_unload()
    SCRIPT_CONTEXT.obs_data = settings
    SCRIPT_CONTEXT.start_server_asynch(DEFAULT_RETRY_FREQUENCY, DEFAULT_RETRY_DURATION)




def script_unload():
    SCRIPT_CONTEXT.shutdown_server_async()
    SCRIPT_CONTEXT.dereference_data()




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
    SCRIPT_CONTEXT.debug = not SCRIPT_CONTEXT.debug
    debug_btn = obs.obs_properties_get(props, "_debug")
    obs.obs_property_set_description(debug_btn, f'Debug {"Enabled" if SCRIPT_CONTEXT.debug else "Disabled"}')
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

    SCRIPT_CONTEXT.obs_properties = props

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
    data = SCRIPT_CONTEXT.obs_data
    add_filter(
        data,
        filterName=obs.obs_data_get_string(data, "_filter"),
        sourceName=obs.obs_data_get_string(data, "_source"),
        displayName=obs.obs_data_get_string(data, "_name"),
        onColor=int_to_color_hex(obs.obs_data_get_int(data, "_color"))
    )
    return True




def int_to_color_hex(num : int) -> str:
    hex_str = hex(num) # 0xAABBGGRR (The obs_data_get_int color format)
    
    r = hex_str[8:10]
    g = hex_str[6:8]
    b = hex_str[4:6]
    
    return "".join(('#', r, g, b))



def add_filter(data, filterName : str, sourceName : str, displayName : str = None, onColor : str = None):
    swing_data = obs.obs_data_get_array(data, "_filters")
    item_as_json = create_list_item_json(filterName, sourceName, displayName, onColor)
    item = obs.obs_data_create_from_json(item_as_json)
    SCRIPT_CONTEXT.debug_message(item)
    obs.obs_data_array_push_back(swing_data, item)
    obs.obs_data_set_array(data, "_filters", swing_data)




def create_list_item_json(filterName : str, sourceName : str, displayName : str = None, onColor : str = None) -> str:
    filter = '{\\\"filterName\\\": \\\"%s\\\", \\\"sourceName\\\": \\\"%s\\\"' % (filterName, sourceName)
    if displayName != None: filter += f', \\\"displayName\\\": \\\"{displayName}\\\"'
    if onColor != None: filter += f', \\\"onColor\\\": \\\"{onColor}\\\"'
    filter += "}"
    return '{"value":"%s","selected":false,"hidden":false}' % filter