import sys, os
# sys.path.append(os.getcwd() +"\custom_nodes\Comfyui-save-image")
sys.path.append(os.path.join(os.path.dirname(__file__)))
# print(sys.path)
from image_save_encrypted import SaveImage_Encrypted 
from image_save_encrypted import PreviewImage_Nosave
from image_save_encrypted import LoadImage_Encrypted

module_root_directory = os.path.dirname(os.path.realpath(__file__))
module_js_directory = os.path.join(module_root_directory, "js")

NODE_CLASS_MAPPINGS = {
    "PreviewImage_nosave": PreviewImage_Nosave,
    "SaveImage_Encrypted": SaveImage_Encrypted,
    "LoadImage_Encrypted": LoadImage_Encrypted,
}

WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "WEB_DIRECTORY"]