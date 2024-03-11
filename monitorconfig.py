import obspython as obs
from itertools import count
import json 
import os.path

template_file : str = script_path() + "/monitor_template.json"
html_file : str = script_path() + "/monitor.html"
config_file : str = script_path() + "/config.json"

def script_defaults(settings):
    obs.obs_data_set_default_array(settings, "_filters", obs.obs_data_array_create())
    obs.obs_data_set_default_string(settings, "_pass", "secret-password")
    obs.obs_data_set_default_bool(settings, "_use_pass", False)
    obs.obs_data_set_default_string(settings, "_address", "127.0.0.1")
    obs.obs_data_set_default_int(settings, "_port", 4455)
    obs.obs_data_set_default_string(settings, "_color", "#6f6b6f")

def script_load(settings):
    pass

def callback(props, prop, *args, **kwargs):  # pass settings implicitly
    p = obs.obs_properties_get(props, "button")
    print(obs.obs_data_get_string(props, "_source"))
    print(obs.obs_data_get_string(props, "_filter"))
    return True


def toggled(props, prop, *args, **kwargs):
    print(obs.obs_properties_get(props, "_bool"))
    obs.obs_properties_get(props, "_bool")
    obs.obs_source_get_filter_by_name(obs.obs_properties_get)


def script_description():
    return "Add or remove filters from the filter monitor."


def script_properties():

    props = obs.obs_properties_create()
    obs.obs_properties_add_list(props, "_filters", "Filters: ", obs.OBS_COMBO_TYPE_LIST, obs.OBS_COMBO_FORMAT_STRING)
    obs.obs_properties_add_button(props, "remove_button", "Remove", remove_filter)

    obs.obs_properties_add_text(props, "_source", "Source: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "_filter", "Filter: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "_name", "Display Name: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_color(props, "_color", "Active Color: ")
    obs.obs_properties_add_button(props, "add_button", "Add", add_filter_callback)

    obs.obs_properties_add_text(props, "_address", "Address: ", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_int(props, "_port", "Port: ", 0, 65535, 1)

    obs.obs_properties_add_text(props, "_pass", "Password: ", obs.OBS_TEXT_PASSWORD)
    obs.obs_properties_add_bool(props, "_use_pass", "Use Password")

    obs.obs_properties_add_button(props, "apply_button", "Apply Settings", create_monitor_html)

    return props


def save_config():
    mode : str = "w" if os.path.exists(html_file) else "x"
    with open(config_file, mode) as file:
        file.write(json.dumps(settings_as_dict()))

def settings_as_dict() -> dict:
    return { "hostAddress":hostAddress,
            "port":port,
            "obsPassword":obsPassword,
            "filtersList": filters }

def load_config() :
    if not os.path.exists(config_file): raise FileNotFoundError("Unable to locate config file: %s" % os.path.abspath(config_file))
    with open(config_file, "r") as file:
        json_str : str = file.read()
    config : dict = json.loads(s=file.read())
    filters = config["filtersList"]
    hostAddress = config["hostAddress"]
    port = config["port"]
    obsPassword = config["obsPassword"]

def add_filter_callback(props, prop, *args, **kwargs):
    add_filter(
        props,
        filterName=obs.obs_data_get_string(props, "_filter"),
        sourceName=obs.obs_data_get_string(props, "_source"),
        displayName=obs.obs_data_get_string(props, "_name"),
        onColor=obs.obs_data_get_string(props, "_color")
    )

def add_filter(props, filterName: str, sourceName: str, displayName: str = None, onColor: str = None):
    new_filter = {"filterName": filterName, "sourceName": sourceName}
    if displayName != None: new_filter["displayName"] = displayName
    if onColor != None: new_filter["onColor"] = onColor
    filters = obs.obs_properties_get(props, "_filters")
    obs.obs_property_list_add_string(filters, str(new_filter))


def remove_filter(data):
    filters = obs.obs_properties_get(data, "_filters")
    index = obs.obs_data_get_int(data, "_filters")
    obs.obs_property_list_item_remove(filters, index)


def create_monitor_html(settings):
    if not os.path.exists(template_file): raise FileNotFoundError("Unable to locate monitor template file: %s" % template_file)
    json_str : str
    with open(template_file, "r") as file:
        json_str = file.read()


    filters : list = obs.obs_data_get_array(settings, "_filters")

    hostAddress : str = obs.obs_data_get_string(settings, "_address")
    port : str = obs.obs_data_get_int(settings, "_port")
    obsPassword : str = obs.obs_data_get_string(settings, "_pass")

    json_str.replace("[{\"filterName\": \"filter1\", \"sourceName\": \"source1\", \"displayName\": \"Filter\", \"onColor\": \"hexValue\"}]", json.dumps(filters))
    json_str.replace("127.0.0.1:4455", json.dumps(f"{hostAddress}:{port}"))
    json_str.replace("secret-password", json.dumps(f"{obsPassword}"))
    
    mode : str = "w" if os.path.exists(html_file) else "x"
    with open(html_file, mode) as file:
        file.write(json_str)