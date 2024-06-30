import pandas as pd

from lwx_project.const import *


def get_yaml_conf(scene: str, conf_key=None):
    import yaml
    conf_path = os.path.join(CONF_PATH, scene+".yaml")
    with open(conf_path) as f:
        result = yaml.safe_load(f.read())
    if conf_key is None:
        return result
    return result.get(conf_key)


def set_yaml_conf(scene: str, conf_key: str, conf_value):
    import yaml
    conf_path = os.path.join(CONF_PATH, scene+".yaml")
    conf_data = get_yaml_conf(scene)
    conf_data[conf_key] = conf_value
    with open(conf_path, 'w') as yaml_file:
        yaml_file.write(yaml.dump(conf_data, default_flow_style=False, allow_unicode=True))


def get_txt_conf(path, type_=str):
    if type_ == str:
        with open(path, encoding="utf8") as f:
            result = f.read()
        return result
    elif type_ == list:
        with open(path, encoding="utf8") as f:
            result = [i.strip("\n") for i in f.readlines() if i.strip("\n")]
        return result


def set_txt_conf(path, value):
    with open(path, "w", encoding="utf8") as f:
        f.write(value)


def get_csv_conf(path):
    return pd.read_csv(path, encoding="utf-8")


def set_csv_conf(path, value: pd.DataFrame):
    value.to_csv(path, encoding="utf-8", index=False)


if __name__ == '__main__':
    print(get_yaml_conf("system", "window"))
    set_yaml_conf("system", "developer", "fuyao.cookiee")
    print(get_yaml_conf("system", "developer"))
