import yaml
from lwx_project.const import *


def get_yaml_conf(scene: str, conf_key=None):
    conf_path = os.path.join(CONF_PATH, scene+".yaml")
    with open(conf_path) as f:
        result = yaml.safe_load(f.read())
    if conf_key is None:
        return result
    return result.get(conf_key)


def set_yaml_conf(scene: str, conf_key: str, conf_value):
    conf_path = os.path.join(CONF_PATH, scene+".yaml")
    conf_data = get_yaml_conf(scene)
    conf_data[conf_key] = conf_value
    with open(conf_path, 'w') as yaml_file:
        yaml_file.write(yaml.dump(conf_data, default_flow_style=False, allow_unicode=True))


def get_txt_conf(path, type_=str):
    if type_ == str:
        with open(path) as f:
            result = f.read()
        return result
    elif type_ == list:
        with open(path) as f:
            result = [i.strip("\n") for i in f.readlines() if i]
        return result


def set_txt_conf(path, value):
    with open(path, "w") as f:
        f.write(value)


if __name__ == '__main__':
    print(get_yaml_conf("system", "window"))
    set_yaml_conf("system", "developer", "fuyao.cookiee")
    print(get_yaml_conf("system", "developer"))
