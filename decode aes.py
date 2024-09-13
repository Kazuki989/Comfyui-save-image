from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import io
import os
import glob
from PIL import Image, PngImagePlugin


# Ensure the key is exactly 16 bytes (AES-128) by padding or truncating
key = "QWERasdf87654321".encode('utf-8') # 16 bytes key for AES-128
input_folder = "F:\\Downloads\\.tmp\\ComfyUI\\output"
output_folder = "F:\\Downloads\\.tmp\\ComfyUI\\output"  # Adjust the output folder path as needed


def decrypt_aes_image(input_file, output_file):
    """Decrypts an AES-encrypted image and saves it as a new image file.

    Args:
        input_file (str): The path to the input AES-encrypted file.
        output_file (str): The path to the output image file.
    """
    with open(input_file, 'rb') as f:
        encrypted_data = f.read()

    try:
        # Decrypt the data and open image
        cipher = AES.new(key, AES.MODE_ECB)
        ImageBytes = unpad(cipher.decrypt(encrypted_data), AES.block_size)
        image = Image.open(io.BytesIO(ImageBytes))

        # Prepare Metadata
        metadata_dict = image.info
        png_info = PngImagePlugin.PngInfo()
        # Add metadata to the PngInfo ob ject
        for key_, value in metadata_dict.items():
            png_info.add_text(key_, value)
        
        # Save image With Metadata
        image.save(output_file, pnginfo=png_info)
        print(f"Saved decrypted image to {output_file}")

    except (ValueError, KeyError) as e:
        print(f"Passing: {input_file}: {e}")

def main(input_folder):
    """Finds all .enc files in the input folder, decrypts them, and saves the images in the output folder.

    Args:
        input_folder (str): The folder where .enc files are located.
        output_folder (str): The folder where decrypted images will be saved.
    """

    # Find all .enc files in the input folder
    enc_files = glob.glob(os.path.join(input_folder, '*.png'))

    for enc_file in enc_files:
        # Define the output file path based on the input file name
        file_name = os.path.basename(enc_file)
        output_file = os.path.join(output_folder, file_name)

        # Decrypt the .enc file
        decrypt_aes_image(enc_file, input_folder)


main(input_folder, output_folder)
