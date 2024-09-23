import time
import folder_paths
from PIL import Image, ImageOps, ImageSequence
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
from Crypto.Util.Padding import pad, unpad
import torch


###########################################################################################################

class SaveImage_Encrypted:

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



###########################################################################################################


class PreviewImage_Nosave:
    @classmethod
    def INPUT_TYPES(s):
        return { "required": 
                { "images": ("IMAGE", ),}
            }
    
    FUNCTION = "preview"

    OUTPUT_NODE = True

    CATEGORY = "BetterImage"
    RETURN_TYPES = ("IMAGE",)

    def preview(self, images):
        pbar = comfy.utils.ProgressBar(images.shape[0])
        step = 0
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            pbar.update_absolute(step, images.shape[0], ("PNG", img, None))
            step += 1

        return (images,)
    

###########################################################################################################


class LoadImage_Encrypted:
    @classmethod
    def INPUT_TYPES(s):
        input_dir = folder_paths.get_input_directory()
        # List image files in the directory
        files = [
            os.path.relpath(os.path.join(root, f), input_dir)
            for root, _, files_in_dir in os.walk(input_dir, followlinks=True)
            for f in files_in_dir if os.path.isfile(os.path.join(root, f))
        ]
        return {"required": {
            "image": (sorted(files), {"image_upload": True})}}

    CATEGORY = "BetterImage"
    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"

    def load_image(self, image):
        image_path = folder_paths.get_annotated_filepath(image)

        ###
        try:
            with open(image_path, 'rb') as f:
                encrypted_data = f.read()
                f.close()
            key = "QWERasdf87654321".encode('utf-8')
            cipher = AES.new(key, AES.MODE_ECB)
            ImageBytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
            img = Image.open(io.BytesIO(ImageBytes))
        
        except Exception as e:
            print(f'load_image decryption exception: {e}')
            img = Image.open(image_path)
            pass

        
        output_images = []
        output_masks = []
        w, h = None, None

        excluded_formats = ['MPO']
        
        for i in ImageSequence.Iterator(img):
            i = ImageOps.exif_transpose(i)

            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")

            if len(output_images) == 0:
                w = image.size[0]
                h = image.size[1]
            
            if image.size[0] != w or image.size[1] != h:
                continue
            
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
            output_images.append(image)
            output_masks.append(mask.unsqueeze(0))

        if len(output_images) > 1 and img.format not in excluded_formats:
            output_image = torch.cat(output_images, dim=0)
            output_mask = torch.cat(output_masks, dim=0)
        else:
            output_image = output_images[0]
            output_mask = output_masks[0]

        return (output_image, output_mask)


###########################################################################################################




