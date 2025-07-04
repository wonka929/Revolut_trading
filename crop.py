from PIL import Image, ImageOps
import glob
import os

filePaths = glob.glob(os.getcwd() + "/*.png") #search for all png images in the folder

for filePath in filePaths:
	try:
		image=Image.open(filePath)
		image.load()
		imageSize = image.size
		
		# remove alpha channel
		invert_im = image.convert("RGB") 
		
		# invert image (so that white is 0)
		invert_im = ImageOps.invert(invert_im)
		imageBox = invert_im.getbbox()
		
		cropped=image.crop(imageBox)
		cropped.save(filePath)
	except:
		continue
