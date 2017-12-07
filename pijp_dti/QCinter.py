import tkinter as Tk

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.backends.tkagg as tkagg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import nibabel as nib

from pijp_dti import dtiQC


class Application(Tk.Frame):
    def __init__(self, master=None):
        Tk.Frame.__init__(self, master)
        self.result = None
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.grid(stick="news")
        self.create_widgets()

    def create_widgets(self):
        self.button_quit = Tk.Button(master=self.master, text='Exit', command=self._quit)
        self.button_pass = Tk.Button(master=self.master, text='Pass', command=self._pass, highlightcolor='green')
        self.button_fail = Tk.Button(master=self.master, text='Fail', command=self._fail, highlightcolor='red')
        self.button_path = Tk.Button(master=self.master, text='Copy Path', command=self._get_path)
        self.button_comment = Tk.Button(master=self.master, text='Save Comment', command=self._save_comment)

        v = Tk.StringVar()
        self.entry_comment = Tk.Entry(master=self.master, width=50, textvariable=v)

        self.label_comment = Tk.Label(master=self.master, text="Comment: ")
        self.label_path = Tk.Label(master=self.master, text="Path: ")

        self.text_path = Tk.Text(master=self.master, width=50, height=1)
        self.text_path.insert('1.0', "/home/users/sample/path/to/image.png")

        self.label_comment.grid(column=0, row=1, sticky='e')
        self.entry_comment.grid(column=1, row=1, columnspan=2, sticky='w')
        self.button_comment.grid(column=3, row=1, sticky='news')
        self.label_path.grid(column=0, row=2, sticky='e')
        self.text_path.grid(column=1, row=2, columnspan=2, sticky='w')
        self.button_path.grid(column=3, row=2, sticky='news')
        self.button_fail.grid(column=1, row=3, sticky='news')
        self.button_pass.grid(column=2, row=3, stick='news')
        self.button_quit.grid(column=3, row=3, sticky='news')

        for i in range(0, 3):
            self.columnconfigure(i, weight=1)
        for j in range(0, 3):
            self.rowconfigure(j, weight=1)

    def create_figure(self, fig, col=0, row=0, span=4):

        canvas = FigureCanvasTkAgg(fig, self.master)
        canvas.show()
        canvas.get_tk_widget().grid(column=col, row=row, columnspan=span, sticky='news', padx=25, pady=25)

    def _quit(self):
        self.quit()
        self.destroy()

    def _pass(self):
        self.button_pass.config(bg='green', fg='white')
        self.button_fail.config(bg='#d9d9d9', fg='black')
        self.result = 0
        print("Pass! ", self.result)

    def _fail(self):
        self.button_fail.config(bg='red', fg='white')
        self.button_pass.config(bg='#d9d9d9', fg='black')
        self.result = 1
        print("FAIL!", self.result)

    def _get_path(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.text_path.get('1.0', 'end-1c'))
        self.button_path.config(text='Copied!', bg='green', fg='white')

    def _save_comment(self):
        self.button_comment.config(text='Saved!', bg='green', fg='white')


root = Tk.Tk()
app = Application(master=root)
app.mainloop()
app.destroy()

