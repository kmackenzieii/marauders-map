#!/usr/bin/python2
# -*- coding: utf-8 -*-
from math import sqrt, floor, ceil
import os, time, sys, yaml, kirk
import tkinter.constants as C
from tkinter import Tk, Frame, Button, Label, PhotoImage, TOP, \
    FLAT, BOTH, filedialog, Canvas, Image
from PIL import ImageTk


class FlatButton(Button):
    def __init__(self, master=None, cnf={}, **kw):
        Button.__init__(self, master, cnf, **kw)
        self.config(
            compound=TOP,
            relief=FLAT,
            bd=0,
            bg="#b91d47",  # dark-red
            fg="white",
            activebackground="#b91d47",  # dark-red
            activeforeground="white",
            highlightthickness=0
        )

    def set_color(self, color):
        self.configure(
            bg=color,
            fg="white",
            activebackground=color,
            activeforeground="white"
        )


class Marauders(Frame):
    doc = None
    framestack = []
    icons = {}
    path = ''

    def __init__(self, parent):
        Frame.__init__(self, parent, background="white")
        self.parent = parent
        self.pack(fill=BOTH, expand=1)

        self.path = os.path.dirname(os.path.realpath(sys.argv[0]))
        with open(self.path + '/Marauders.yaml', 'r') as f:
            self.doc = yaml.load(f)
        self.show_items(self.doc)

    def show_items(self, items, upper=[]):
        """
        Creates a new page on the stack, automatically adds a back button when there are
        pages on the stack already

        :param items: list the items to display
        :param upper: list previous levels' ids
        :return: None
        """
        num = 0

        # create a new frame
        wrap = Frame(self, bg="black")
        # when there were previous frames, hide the top one and add a back button for the new one
        if len(self.framestack):
            self.hide_top()

            back = FlatButton(
                wrap,
                text='Back…',
                image=self.get_icon("arrow.left"),
                command=self.go_back,
            )

            exitbtn = FlatButton(
                wrap,
                text='Exit…',
                image=self.get_icon("exit"),
                command=self.app_exit,
            )

            back.set_color("#00a300")  # green
            exitbtn.set_color("#00a300")  # green

            back.grid(row=0, column=0, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            exitbtn.grid(row=0, column=3, padx=1, pady=1, sticky=C.W + C.E + C.N + C.S)
            num += 1

        # add the new frame to the stack and display it
        self.framestack.append(wrap)
        self.show_top()


        # calculate tile distribution
        all = len(items) + num
        rows = floor(sqrt(all))
        cols = ceil(all / rows)

        # make cells autoscale
        for x in range(int(cols)):
            wrap.columnconfigure(x, weight=1)

        for y in range(int(rows)):
            wrap.rowconfigure(y, weight=1)

        # display all given buttons
        for item in items:
            act = upper + [item['name']]

            if 'icon' in item:
                image = self.get_icon(item['icon'])
            else:
                image = self.get_icon('scrabble.' + item['label'][1:1].lower())

            btn = FlatButton(
                wrap,
                text=item['label'],
                image=image
            )

            if 'items' in item:
                # this is a deeper level
                btn.configure(command=lambda act=act, item=item:
                self.show_items(item['items'], act), text=item['label'] + '…')
                btn.set_color("#2b5797")  # dark-blue


            else:
                # this is an action
                btn.configure(command=lambda act=act: self.go_action(act), )

            if 'color' in item:
                btn.set_color(item['color'])

            # add button to the grid
            btn.grid(
                row=int(floor(num / cols)),
                column=int(num % cols),
                padx=1,
                pady=1,
                sticky=C.W + C.E + C.N + C.S
            )
            num += 1

    def get_icon(self, name):
        """
        Loads the given icon and saves a reference

        :param name: string
        :return:
        """
        if name in self.icons:
            return self.icons[name]

        ico = self.path + '/ico/' + name + '.gif'

        # In case icon cannot be found display the cancel icon
        if not os.path.isfile(ico):
            ico = self.path + '/ico/cancel.gif'

        self.icons[name] = PhotoImage(file=ico)
        return self.icons[name]

    def hide_top(self):
        """
        hide the top page, and returns
        """
        self.framestack[len(self.framestack) - 1].pack_forget()

    def show_top(self):
        """
        show the top page, and returns 
        """
        self.framestack[len(self.framestack) - 1].pack(fill=BOTH, expand=1)

    def capture(self):
      
        width = kirk.width
        height = kirk.height
        box_size = kirk.box_size

        img = Image.PhotoImage(Image.open(kirk.File))
        w = Canvas(root, width=width, height=height)
        w.pack()
        w.create_image(0, 0, image=img, anchor="nw")

        for x in range(1, width // box_size):
            w.create_line(box_size * x, 0, box_size * x, height)
        for y in range(1, height // box_size):
            w.create_line(0, box_size * y, width, box_size * y)

        # function to be called when mouse is clicked
        #def printcoords(event):
            #outputting x and y coords to console
            #print(event.x, event.y)
            #piconnect(event.x // box_size, event.y // box_size)
            #print("DONE")

        #mouseclick event
        #w.bind("<Button 1>", printcoords)


    def destroy_top(self):
        """
        destroy the top page and returns
        """
        self.framestack[len(self.framestack) - 1].destroy()
        self.framestack.pop()

    def destroy_all(self):
        """
        destroy all pages except the first Frame and goes back to start
        """
        while len(self.framestack) > 1:
            self.destroy_top()

    def go_action(self, actions):
        """
        execute the action script
        :param actions:
        :return:
        """
        # hide the menu and show a delay screen
        self.hide_top()
        self.display()
        delay = Frame(self, bg="white")
        delay.pack(fill=BOTH, expand=1)
        label = Label(delay, text="Executing...", fg="white", bg="#2d89ef", font="Sans 30")
        label.pack(fill=BOTH, expand=1)
        self.parent.update()

        self.display()

        time.sleep(.25)

        # remove delay screen and show menu again
        delay.destroy()
        self.destroy_all()
        self.show_top()

    def go_back(self):
        """
        destroy the current frame and reshow the one below,
        returns
        """
        self.destroy_top()
        self.show_top()

    def app_exit(self):

        # Kills application
        self.quit()


def main():
    root = Tk()
    root.geometry("520x440")
    root.wm_title('Marauders Map')
    if len(sys.argv) > 1 and sys.argv[1] == 'fs':
        root.wm_attributes('- fullscreen', True)
    app = Marauders(root)

    root.mainloop()


if __name__ == '__main__':
    main()