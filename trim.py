from PIL import Image, ImageOps
import glob
import os

# Trim all png images with white background in a folder
# Usage "python PNGWhiteTrim.py ../someFolder"

filePaths = glob.glob(os.getcwd() + "/*.png") #search for all png images in the folder

for filePath in filePaths:
    image=Image.open(filePath)
    image.load()
    imageSize = image.size
    
    # remove alpha channel
    invert_im = image.convert("RGB") 
    
    # invert image (so that white is 0)
    invert_im = ImageOps.invert(invert_im)
    imageBox = invert_im.getbbox()
    
    cropped=image.crop(imageBox)
    print(filePath, "Size:", imageSize, "New Size:", imageBox)
    cropped.save(filePath)
