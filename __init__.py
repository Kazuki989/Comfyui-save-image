import sys, os
# sys.path.append(os.getcwd() +"\custom_nodes\Comfyui-save-image")
sys.path.append(os.path.join(os.path.dirname(__file__)))
# print(sys.path)
from image_save_encrypted import SaveImage_Encrypted 
from image_save_encrypted import PreviewImage_Nosave

NODE_CLASS_MAPPINGS = {
    "PreviewImage_nosave": PreviewImage_Nosave,
    "SaveImage_Encrypted": SaveImage_Encrypted,
}

__all__ = ['NODE_CLASS_MAPPINGS']