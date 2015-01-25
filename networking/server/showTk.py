# showTk.py
#
# by Kevin Cazabon, Dec 2005
# kevin@cazabon.com

import Image, Tkinter, ImageTk

def sizeToMax(im, maxSize):
    imAspect = float(im.size[0])/float(im.size[1])
    outAspect = float(maxSize[0])/float(maxSize[1])

    if imAspect >= outAspect:
        #set to maxWidth x maxWidth/imAspect
        return im.resize((maxSize[0], int((float(maxSize[0])/imAspect) + 0.5)), Image.BICUBIC)
    else:
        #set to maxHeight*imAspect x maxHeight
        return im.resize((int((float(maxSize[1])*imAspect) + 0.5), maxSize[1]), Image.BICUBIC)
    

class showTk:
    def __init__(self, parent = None, im = None, maxSize = None):
        # show an image in a Tk window.  This can be part of a Tk GUI, or stand-alone.
        
        # parent = None or a Tk window that's already made
        # im = a filename or an open PIL image
        # maxSize = tuple of maximum horiz/vertical size for the display
        
        # create the main window as a Tk() or TopLevel()
        if parent == None:
            self.main = Tkinter.Tk()
            self.mainloopRequired = True
        else:
            self.main = Tkinter.Toplevel(parent)
            self.mainloopRequired = False
            
        self.maxSize = maxSize
    
        self.label = Tkinter.Label(self.main)
        self.label.pack()
        
        if im != None:
            self.update(im, maxSize)
            
    def mainloop(self):
        if self.mainloopRequired:
            self.main.mainloop()
        
    def update(self, im = None, maxSize = None):
        # update the image to a new one
        # im = a filename or an open PIL image, or None to blank it out
        # maxSize = tuple of maximum horiz/vertical size for the display
        
        # if a filename is passed in, open the image file
        if type(im) == type("string"):
            try:
                im = Image.open(im)
            except Exception, reason:
                return False, "Could not open image: %s" %reason
        
        # size the image if required - default to the maxSize given at init if not over-ridden
        if self.maxSize != None and maxSize == None:
            maxSize = self.maxSize
            
        if maxSize != None and im != None:
            try:
                im = sizeToMax(im, maxSize)
            except Exception, reason:
                return False, "Could not resize image to maxSize: %s" %reason
            
        
        # delete the current image so there's no resource conflict
        self.label.configure(image = None)
        self.label.update_idletasks()
        
        # update the display with a new image
        if im != None:
            try:
                self.im = ImageTk.PhotoImage(im)
            except Exception, reason:
                return False, "Could not make PhotoImage of im: %s" %reason
            
            self.label.configure(image = self.im)
            
            self.label.update_idletasks()
        
        return True, "Update OK"

        
     
if __name__ == "__main__":
    import time
    
    window = showTk(im = "c:\\temp\\test.tif", maxSize = (400,600))
    
    time.sleep(5)    # window will block during sleep, sorry
    window.update(im = "c:\\temp\\test2.tif")
    
    window.mainloop()    # you have to call this if it's the main GUI window,
                        # so it enters the local event processing loop, but
                        # it's safe to call in any circumstance.
    
        
