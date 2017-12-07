import time

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_agg import FigureCanvasAgg


import tkinter as Tk




class Application(Tk.Frame):

    def __init__(self, master=None):
        Tk.Frame.__init__(self, master)
        self.result = None
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.grid(stick="news")
        self.createWidgets()


    def createWidgets(self):
        self.buttonQuit = Tk.Button(master=self.master, text='Exit', command=self._quit)
        self.buttonPass = Tk.Button(master=self.master, text='Pass', command=self._pass, highlightcolor='green',
                                    anchor='se')
        self.buttonFail = Tk.Button(master=self.master, text='Fail', command=self._fail, highlightcolor='red')
        self.buttonPath= Tk.Button(master=self.master, text='Copy Path', command=self._get_path)
        self.buttonComment = Tk.Button(master=self.master, text='Save Comment', command=self._save_comment)

        v = Tk.StringVar()
        v.set(None)
        self.entryComment = Tk.Entry(master=self.master, width=50, textvariable=v)

        self.labelComment = Tk.Label(master=self.master, text="Comment: ")
        self.labelPath = Tk.Label(master=self.master, text="Path: " )

        self.textPath = Tk.Text(master=self.master, width=50, height=1)
        self.textPath.insert('1.0', "/home/users/sample/path/to/image.png")

        self.buttonPass.grid(column=2, row=2, stick='w')
        self.buttonFail.grid(column=1, row=2, sticky='e')
        self.buttonQuit.grid(column=3, row=2, sticky='se')
        self.labelPath.grid(column=0, row=1, sticky='ne')
        self.textPath.grid(column=1, row=1, sticky= 'news')
        self.buttonPath.grid(column=2, row=1, sticky= 'sw')
        self.entryComment.grid(column=1, row=0, sticky='news')
        self.labelComment.grid(column=0, row=0, sticky='ne')
        self.buttonComment.grid(column=2, row=0, sticky='sw')

        for i in range(0, 3):
            self.columnconfigure(i, weight=1)
        for j in range(0, 2):
            self.rowconfigure(j, weight=1)

    def _quit(self):
        self.quit()
        self.destroy()

    def _pass(self):
        self.buttonPass.config(bg='green', fg='white')
        self.buttonFail.config(bg = '#d9d9d9', fg='black')
        self.result=0
        print("Pass! ", self.result)
    def _fail(self):
        self.buttonFail.config(bg='red', fg='white')
        self.buttonPass.config(bg = '#d9d9d9', fg='black')
        self.result = 1
        print("FAIL!", self.result)

    def _get_path(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.textPath.get('1.0', 'end'))
        self.buttonPath.config(text='Copied!', bg='green', fg='white')


    def _save_comment(self):
        self.buttonComment.config(text='Saved!', bg='green', fg='white')



root = Tk.Tk()

app = Application(master=root)
app.mainloop()
app.destroy()

def draw_figure(canvas, figure, loc=(0, 0)):
    """ Draw a matplotlib figure onto a Tk canvas

    loc: location of top-left corner of figure on canvas in pixels.
    Inspired by matplotlib source: lib/matplotlib/backends/backend_tkagg.py
    """
    figure_canvas_agg = FigureCanvasAgg(figure)
    figure_canvas_agg.draw()
    figure_x, figure_y, figure_w, figure_h = figure.bbox.bounds
    figure_w, figure_h = int(figure_w), int(figure_h)
    photo = tk.PhotoImage(master=canvas, width=figure_w, height=figure_h)

    # Position: convert from top-left anchor to center anchor
    canvas.create_image(loc[0] + figure_w/2, loc[1] + figure_h/2, image=photo)

    # Unfortunately, there's no accessor for the pointer to the native renderer
    tkagg.blit(photo, figure_canvas_agg.get_renderer()._renderer, colormode=2)

    # Return a handle which contains a reference to the photo object
    # which must be kept live or else the picture disappears
    return photo


