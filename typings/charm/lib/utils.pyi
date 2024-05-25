
import importlib.resources as pkg_resources

import pyglet.image

# Fix for @cache not hashing Packages
def pyglet_img_from_resource(package: pkg_resources.Package, resource: pkg_resources.Resource) -> pyglet.image.AbstractImage:
    ...
