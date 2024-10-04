from pathlib import Path
import importlib.resources as pkg_resources

import charm.data.shaders as shaders


__all__ = (
    'get_shader_raw_str',
)

def get_shader_raw_str(name: str) -> str:
    file = f'{name}.glsl'
    return pkg_resources.read_text(shaders, file)

def get_shader_path(name: str) -> Path:
    file = f'{name}.glsl'
    with pkg_resources.as_file(pkg_resources.files(shaders).joinpath(file)) as p:
        return p
