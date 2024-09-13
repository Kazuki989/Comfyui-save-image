import time
import folder_paths
from PIL import Image
from PIL.PngImagePlugin import PngInfo
import json
import numpy as np
import comfy.utils
import os
from comfy.cli_args import args
import folder_paths
import base64
import io
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad


class SaveImage_Encrypted:
    """
    A example node

    Class methods
    -------------
    INPUT_TYPES (dict):
        Tell the main program input parameters of nodes.
    IS_CHANGED:
        optional method to control when the node is re executed.

    Attributes
    ----------
    RETURN_TYPES (`tuple`):
        The type of each element in the output tuple.
    RETURN_NAMES (`tuple`):
        Optional: The name of each output in the output tuple.
    FUNCTION (`str`):
        The name of the entry-point method. For example, if `FUNCTION = "execute"` then it will run Example().execute()
    OUTPUT_NODE ([`bool`]):
        If this node is an output node that outputs a result/image from the graph. The SaveImage node is an example.
        The backend iterates on these output nodes and tries to execute all their parents if their parent graph is properly connected.
        Assumed to be False if not present.
    CATEGORY (`str`):
        The category the node should appear in the UI.
    DEPRECATED (`bool`):
        Indicates whether the node is deprecated. Deprecated nodes are hidden by default in the UI, but remain
        functional in existing workflows that use them.
    EXPERIMENTAL (`bool`):
        Indicates whether the node is experimental. Experimental nodes are marked as such in the UI and may be subject to
        significant changes or removal in future versions. Use with caution in production workflows.
    execute(s) -> tuple || None:
        The entry point method. The name of this method must be the same as the value of property `FUNCTION`.
        For example, if `FUNCTION = "execute"` then this method's name must be `execute`, if `FUNCTION = "foo"` then it must be `foo`.
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": ("STRING", {"default": "ComfyUI", "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width% to include values from nodes."})
            },
            "hidden": {
                "prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    #RETURN_NAMES = ("image_output_name",)

    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "BetterImage"
    DESCRIPTION = "Saves the input images encoded in Base64 to your ComfyUI output directory."



    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):

        """
        Saves a list of images to the output directory, with the given filename prefix.

        Args:
            images: A list of tensors, where each tensor is a 3D image (HxWxC)
            filename_prefix: A string prefix to be used for the filename of each image.
            prompt: A string prompt to be saved as metadata in the PNG file.
            extra_pnginfo: A dictionary of extra metadata to be saved in the PNG file.

        Returns:
            A dictionary with a single key "ui", which contains a list of dictionaries, each containing the filename, subfolder, and type of each image saved.
        """

        
        def encrypt_data(data, key):
            cipher = AES.new(key, AES.MODE_ECB)
            encrypted_data = cipher.encrypt(pad(data, AES.block_size))
            return encrypted_data
        
                # AES encryption settings
        key = "QWERasdf87654321".encode('utf-8') # 16 bytes key for AES-128
        
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])
        results = list()

        for (batch_number, image) in enumerate(images):
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            metadata = None
            if not args.disable_metadata:
                metadata = PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for x in extra_pnginfo:
                        metadata.add_text(x, json.dumps(extra_pnginfo[x]))

            filename_with_batch_num = filename.replace("%batch_num%", str(batch_number))
            file = f"{filename_with_batch_num}_{counter:05}_.png"

            # Encode image to Base64 and save to separate .txt file
            with open(os.path.join(full_output_folder, f"{file}"), "wb") as txt_file:
                with io.BytesIO() as buffer:
                    img.save(buffer, format="PNG", pnginfo=metadata)
                    image_data = buffer.getvalue()
                    encrypted_data = encrypt_data(image_data, key)
                    txt_file.write(encrypted_data)

            
            
            pbar = comfy.utils.ProgressBar(images.shape[0])
            step = 0
            for image in images:
                i = 255. * image.cpu().numpy()
                img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
                pbar.update_absolute(step, images.shape[0], ("PNG", img, None))
                step += 1

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type,
            })
            counter += 1

        return { "ui": { "images": results } }






class PreviewImage_Nosave:
    @classmethod
    def INPUT_TYPES(s):
        return { "required": 
                { "images": ("IMAGE", ),}
            }
    
    RETURN_TYPES = ()
    FUNCTION = "preview"

    OUTPUT_NODE = True

    CATEGORY = "BetterImage"

    def preview(self, images):
        pbar = comfy.utils.ProgressBar(images.shape[0])
        step = 0
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            pbar.update_absolute(step, images.shape[0], ("PNG", img, None))
            step += 1

        return {}
    
    def IS_CHANGED(s, images):
        return time.time()














###########################################################################################################




