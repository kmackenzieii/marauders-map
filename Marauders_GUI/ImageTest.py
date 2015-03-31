import  tkinter
from tkinter import *
from glob import glob

class ImageFrame(Frame):

    def __init__(self, master=None):
        Frame.__init__(self, master)
        self.images = glob("*.gif")
        self.cur = 0
        # label showing the image
        self.image = PhotoImage()
        imagelabel = Label(self, image=self.image)
        imagelabel.grid(row=1, column=1)
        # button cycling through the images
        #button = Button(self, text="NEXT", command=self.show_next)
        #button.grid(row=2, column=1)
        # layout and show first image
        self.grid()
        self.show_next()

    def show_next(self):
       self.cur = (self.cur + 1) % len(self.images)
       self.image.configure(file=self.images[self.cur])

ImageFrame().mainloop()