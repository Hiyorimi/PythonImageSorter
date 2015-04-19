# ImageSorter.py
# By Kurt D kurtd5105@gmail.com
# Description: An image sorter created with Tkinter and PIL that will cycle through
#			   images in the current directory, and allow you to select check boxes
#			   of folders in the current directory that you wish to sort the image
#			   to. It also allows you to create new folders. You cycle through with
#			   the enter key, and if you do not select folders, nothing will be done
#			   to the image. If you select 1 or more folders, the image will be
#			   sorted to those folders and removed from the current folder, provided
#			   that the file copied over correctly.
#
# Version: 0.98
# Planned: Scroll support for non-Windows platforms, Variable size windows.

import PIL.Image
import PIL.ImageTk
from Tkinter import *
from glob import glob
import os
import shutil

MAX_WIDTH = 1366
MAX_HEIGHT = 768

# ImagePreview
# Description: Class that contains the image preview window and contains tools to 
#			   resize and change the image.

class ImagePreview:
	def __init__(self, root):
		self.imageName = "None"
		self.imageWindow = Frame(root, width=MAX_WIDTH, height=MAX_HEIGHT, borderwidth=1, relief=SUNKEN)
		self.imageWindow.configure(width=MAX_WIDTH, height=MAX_HEIGHT)
		self.imageContainer = Label(self.imageWindow, image=None, text="Press Enter to continue.", height=51)

	# Changes the image in the window to the given filename
	def changeImage(self, filename):
		self.imageContainer.destroy()

		self.imageName = filename
		displayImage = None

		try:
			# Try to use PIL to create the image for Tkinter
			displayImage = PIL.Image.open(filename)
		except:
			# If the file is not found then it was removed or there are no more images to display
			self.imageContainer = Label(self.imageWindow, image=None, text="No image to display.", height=51)

		# If there is an image, resize it if needed with Bilinear filtering (Antialias is expensive) and then remake the image container
		if displayImage != None:
			displayImage = self.scaleImage(displayImage)
			displayPhoto = PIL.ImageTk.PhotoImage(displayImage)

			# Set the image container
			self.imageContainer = Label(self.imageWindow, image=displayPhoto, text=None, height=MAX_HEIGHT)
			self.imageContainer.image = displayPhoto

		self.imageContainer.pack()

	# Scales the image if necessary
	def scaleImage(self, image):
		imageSize = image.size

		if imageSize[0] > MAX_WIDTH or imageSize[1] > MAX_HEIGHT:
			# Calculate the scaling multipliers
			scaleXDiff = float(MAX_WIDTH)/imageSize[0]
			scaleYDiff = float(MAX_HEIGHT)/imageSize[1]

			# Whichever dimension needs the most scaling becomes the scaling constant for proportional scaling
			if scaleXDiff < scaleYDiff:
				scale = scaleXDiff
			else:
				scale = scaleYDiff

			image = image.resize(((int(imageSize[0] * scale)), int(imageSize[1] * scale)), PIL.Image.BILINEAR)

		return image

	def pack(self):
		self.imageWindow.pack(fill=BOTH, expand=1, pady=0)
		self.imageContainer.pack()

	def getImageName(self):
		return self.imageName

# FolderSelector
# Description: Class that contains the folder checkbuttons in frames, for addition to a Tkinter canvas.

class FolderSelector:
	def __init__(self, root, name):
		self.name = name
		self.checked = IntVar()
		self.checkFrame = Frame(root)
		self.checkButton = Checkbutton(self.checkFrame, text=self.name, variable=self.checked)

	# Returns the name and status of the checkbutton
	def getStatus(self):
		return (self.name, self.checked.get() == 1)

	def setStatus(self, status):
		self.checked.set(status)

	def getFrame(self):
		return self.checkFrame

	def getButton(self):
		return self.checkButton

	def pack(self):
		self.checkFrame.pack(fill=BOTH, expand=1)
		self.checkButton.pack(side="left")

# FolderList
# Description: Class that contains the list of folders, including the canvas that the FolderSelectors
#			   get drawn on. Allows for a scrolling list of FolderSelectors for when there are many
#			   folders.

class FolderList:
	def __init__(self, root, folderManifest):
		self.folderWindow = Frame(root, width=MAX_WIDTH, height=0)
		self.FOLDER_HEIGHT = 25

		# Create a canvas to be scrolled along with a scrollbar
		self.createCanvas()
		self.folderManifest = folderManifest
		self.folders = []
		for folder in self.folderManifest:
			self.folders.append(FolderSelector(self.folderCanvas, folder))

	def createCanvas(self):
		self.folderCanvas = Canvas(self.folderWindow, width = MAX_WIDTH)
		self.scrollbar = Scrollbar(self.folderWindow, orient="vertical", command=self.folderCanvas.yview)
		self.folderCanvas.bind('<Configure>', self.configureScroll)
		self.folderCanvas.configure(yscrollcommand=self.scrollbar.set)

	def destroyCanvas(self):
		self.scrollbar.destroy()
		self.folderCanvas.destroy()
		self.scrollbar = None
		self.folderCanvas = None

	def getButtonStatus(self):
		return [folderSelection.getStatus() for folderSelection in self.folders]

	def resetButtons(self):
		for folder in self.folders:
			folder.setStatus(0)

	def refreshFolders(self, addedFolder):
		self.destroyCanvas()
		self.createCanvas()
		self.folderManifest.append(addedFolder)
		self.folderManifest.sort()
		self.folders = []
		for folder in self.folderManifest:
			self.folders.append(FolderSelector(self.folderCanvas, folder))
		self.pack()

	# Packs the folder window, scrollbar, canvas and all of the folder check buttons into the canvas
	def pack(self):
		self.folderWindow.pack(pady=0)
		self.scrollbar.pack(side="right", fill="y")
		self.folderCanvas.pack(side="left")
		self.rows = 1

		x = -150
		y = self.FOLDER_HEIGHT/2
		if self.folders[0] != None:
			prevLetter = self.folders[0].getStatus()[0][0]
		for folder in self.folders:
			currLetter = folder.getStatus()[0][0]
			folder.pack()

			if x + 300 > MAX_WIDTH or currLetter > prevLetter:
				x = 0
				y = y + self.FOLDER_HEIGHT
				self.rows += 1
			else:
				x += 150

			prevLetter = currLetter
			self.folderCanvas.create_window((x, y), window=folder.getFrame(), anchor="w")
		self.folderCanvas.configure(yscrollcommand=self.scrollbar.set)

	def configureScroll(self, event):
		# Set the scroll area to either the canvas height or to the height needed for the correct amount of rows
		size = self.folderCanvas.winfo_reqwidth(), self.folderCanvas.winfo_reqheight()
		if len(self.folders) > 0:
			size = size[0], (self.rows + 1)*self.FOLDER_HEIGHT
		self.folderCanvas.config(scrollregion="0 0 {} {}".format(size[0], size[1]))

	def onScroll(self, event):
		# on osx dont divide or negate, future feature
		self.folderCanvas.yview_scroll(-event.delta/120, "units")

# FolderCreator
# Description: Window that contains the widgets to create a folder.

class FolderCreator:
	def __init__(self, root, folderList):
		self.folderList = folderList
		self.folderCreatorWindow = Frame(root, borderwidth=1, relief=SUNKEN)
		self.folderInput = StringVar()
		self.infoLabel = Label(self.folderCreatorWindow, text="New folder name:")
		self.folderEntry = Entry(self.folderCreatorWindow, textvariable=self.folderInput, width=203)
		self.createButton = Button(self.folderCreatorWindow, text="Create", command=lambda:self.createFolder())

	def createFolder(self):
		# Gets the folder from the entry in the text box
		folder = self.folderInput.get()
		# If there was input
		if len(self.folderInput.get()) > 0:
			# If the folder doesn't exist try creating it
			if not os.path.isdir(folder):
				try:
					os.mkdir(os.getcwd() + "\\" + folder)
					self.folderList.refreshFolders(folder)
				except:
					pass
			# Remove the text from the folder entry
			self.folderEntry.delete(0, END)

	def pack(self):
		self.folderCreatorWindow.pack(side="bottom")
		self.infoLabel.pack(side="left")
		self.folderEntry.pack(side="left", fill="x", expand=1)
		self.createButton.pack(side="left")

# ImageSorterApp
# Description: Creates the app for the user.

class ImageSorterApp:
	def __init__(self):
		self.root = Tk()
		# Turn off scaling and lock the window size
		self.root.resizable(width=False, height=False)
		self.root.minsize(width=MAX_WIDTH, height=MAX_HEIGHT+200)
		self.root.maxsize(width=MAX_WIDTH, height=MAX_HEIGHT+200)
		self.root.title("Image Sorter")
		# Bind the enter key to switching the image
		self.root.bind("<Return>", self.cycleImage)
		self.generateImageManifest()
		self.generateFolderManifest()
		self.cwd = os.getcwd() + "\\"
		self.setupLayout()
		self.packLayout()
		self.root.bind("<MouseWheel>", self.folderWindow.onScroll)

		self.root.mainloop()		
		
	# Sets up the layout objects
	def setupLayout(self):
		self.imageWindow = ImagePreview(self.root)
		self.folderWindow = FolderList(self.root, self.folderManifest)
		self.createFolderWindow = FolderCreator(self.root, self.folderWindow)
		self.windowRefs = [self.imageWindow, self.createFolderWindow, self.folderWindow]

	# Packs the layout objects
	def packLayout(self):
		for window in self.windowRefs:
			window.pack()
		self.folderWindow.pack()

	# Creates a list containing the image names of all jpeg, jpg and png files
	def generateImageManifest(self):
		self.imageManifest = glob("*.jpeg") + glob("*.jpg") + glob("*.png") + glob("*.gif")

	# Creates a list containing the folder names of all the subfolders
	def generateFolderManifest(self):
		self.folderManifest = [folder for folder in os.listdir(".") if os.path.isdir(folder)]
		self.folderManifest.sort()

	# Moves the image to the selected folders
	def transferImage(self, imageName):
		removeFile = None
		# If there is a valid image name
		if imageName != "None" and imageName != None:
			# Sets up the dirs to be copied to by taking the button status from each folder button
			copyDirs = [folder[0] for folder in self.folderWindow.getButtonStatus() if folder[1] == True]
			# Copy over the image to every directory
			for dirName in copyDirs:
				shutil.copy2(self.cwd + imageName, self.cwd + dirName)
				# Verify that the size of the image remained the same
				if os.stat(self.cwd + imageName).st_size != os.stat(self.cwd + dirName + "\\" + imageName).st_size:
					removeFile = False
				else:
					# If the file was copied to one folder it may be removed now
					if removeFile == None:
						removeFile = True
		
		if removeFile == None:
			return False
		return removeFile

	# Changes the image to the next image in the manifest and removes it from the manifest
	def cycleImage(self, event):
		imageName = self.imageWindow.getImageName()
		# Transfers the file if possible and stores the success of the transfers
		removeFile = self.transferImage(imageName)

		try:
			self.imageWindow.changeImage(self.imageManifest.pop())
		except:
			# Can't pop from empty list so pass None
			self.imageWindow.changeImage(None)

		self.folderWindow.resetButtons()

		# Remove the file if the transfer was successful
		if removeFile:
			os.remove(self.cwd + imageName)

if __name__ == '__main__':
	app = ImageSorterApp()
