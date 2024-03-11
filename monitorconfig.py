import obspython as obs
from itertools import count
import json 
import os.path

counter = count()

filters : list[str] = []

config_file : str = "./config.json"

def refresh_pressed(props, prop):
    print("refresh pressed")


def callback(props, prop, *args, **kwargs):  # pass settings implicitly
    p = obs.obs_properties_get(props, "button")
    n = next(counter)
    obs.obs_property_set_description(p, f"refresh pressed {n} times")
    print(obs.obs_data_get_string(props, "_source"))
    print(obs.obs_data_get_string(props, "_filter"))
    return True

def toggled(props, prop, *args, **kwargs):
    print(obs.obs_properties_get(props, "_bool"))
    obs.obs_properties_get(props, "_bool")
    obs.obs_source_get_filter_by_name(obs.obs_properties_get)


def script_description():
    return "Modify property "


def script_properties():
    props = obs.obs_properties_create()
    b = obs.obs_properties_add_button(
        props, "add_button", "refresh pressed 0 times", refresh_pressed
    )
    obs.obs_properties_add_text(props, "_source", "Source :", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_text(props, "_filter", "Filter :", obs.OBS_TEXT_DEFAULT)
    
    obs.obs_property_set_modified_callback(b, callback)
    return props

def save_config():
    if os.path.exists(config_file): os.remove(config_file)
    with open(config_file, "w") as file:
        for filter in filters:
            file.write(json.dumps(filters))
        
def load_config() -> list:
    if not os.path.exists(config_file): return []
    with open(config_file, "r") as file:
        json_str : str = file.read()
        return json.loads(s=file.read(), cls= type[list[str]])

