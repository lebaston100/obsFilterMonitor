import os
import obspython as obs
import json 
import os.path
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
from threading import Thread



class GlobalData:
    def __init__(self) -> None:
        self.httpService : TCPServer = None
        self.obsProperties = None
        self.obsData = None
        self.debug : bool = False
    
    def debug_message(self, msg : str):
        if self.debug: print(msg)

    def shutdown_server(self):
        if self.httpService: self.httpService.shutdown()




class SettingsRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        GLOBAL_DATA.debug_message("Received request: " + self.path)

        # Extract any query parameters (e.g., 'imsi') from the URL
        query_param = self.path
        
        if query_param != '/?settings':
            self.send_error(404, "Invalid Request.", "Monitor config only supports settings requests.")
            GLOBAL_DATA.debug_message("Request rejected.")
            return

        # Send a response back to the client
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        settings_data = json.dumps(settings_as_dict(GLOBAL_DATA.obsData))
        GLOBAL_DATA.debug_message(settings_data)
        self.wfile.write(settings_data.encode())
        GLOBAL_DATA.debug_message("Request handled.")
    
    def log_message(self, format: str, *args) -> None:
        if GLOBAL_DATA.debug: super().log_message(format, *args)




GLOBAL_DATA : GlobalData = GlobalData()

PORT = 6005
CONFIG_FILE : str = os.path.relpath(__file__) + os.path.sep + "config.json"




def serve_settings():
    with TCPServer(("", PORT), SettingsRequestHandler) as service:
        GLOBAL_DATA.httpService = service
        GLOBAL_DATA.debug_message(f"Serving on port {PORT}")
        service.serve_forever()




def script_load(settings):
    GLOBAL_DATA.obsData = settings
    GLOBAL_DATA.debug_message('Starting settings server...')
    server_thread = Thread(name="HTTP server", target=serve_settings)
    server_thread.start()




def script_unload():
    GLOBAL_DATA.shutdown_server()




def script_defaults(settings):
    obs.obs_data_set_default_array(settings, "_filters", obs.obs_data_array_create())
    obs.obs_data_set_default_string(settings, "_pass", "secret-password")
    obs.obs_data_set_default_bool(settings, "_use_pass", False)
    obs.obs_data_set_default_string(settings, "_address", "127.0.0.1")
    obs.obs_data_set_default_int(settings, "_port", 4455)
    obs.obs_data_set_default_int(settings, "_color", int("32Cd32", 16))




def script_description():
    return "Add or remove filters from the filter monitor."



def on_debug_toggled(props, prop, *args, **kwargs):
    print(GLOBAL_DATA.debug)
    GLOBAL_DATA.debug = not GLOBAL_DATA.debug
    print(GLOBAL_DATA.debug)
    debug_btn = obs.obs_properties_get(props, "_debug")
    obs.obs_property_set_description(debug_btn, f'Debug {"Enabled" if GLOBAL_DATA.debug else "Disabled"}')
    print("Done")
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

    #obs.obs_properties_add_button(props, "apply_button", "Apply Settings", create_monitor_html)

    GLOBAL_DATA.obsProperties = props

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
    data = GLOBAL_DATA.obsData
    add_filter(
        data,
        filterName=obs.obs_data_get_string(data, "_filter"),
        sourceName=obs.obs_data_get_string(data, "_source"),
        displayName=obs.obs_data_get_string(data, "_name"),
        onColor=f'#{hex(obs.obs_data_get_int(data, "_color"))[4:]}'
    )




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