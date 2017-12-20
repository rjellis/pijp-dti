import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Application(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        master.geometry("1280x720")
        master.configure(bg='black')

        self.config(bg='black')
        self.result = None
        self.comment = ''
        self.code = ''
        self.x = None
        self.y = None
        self.scale = 1
        self.canvas = None

        self.grid(rowspan=4, columnspan=4, stick="news", padx=5, pady=5)

    def create_widgets(self):
        self.winfo_toplevel().title("QC Tool")
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)
        ttk.Sizegrip(self.master).grid(column=999, row=999, sticky='se')

        self.button_quit = tk.Button(master=self.master, text='Exit', bg='white', fg='black',
                                     relief='flat', command=self._quit)
        self.button_pass = tk.Button(master=self.master, text='Pass', command=self._pass, highlightcolor='green',
                                     bg='white', fg='black', relief='flat')
        self.button_fail = tk.Button(master=self.master, text='Fail', command=self._fail, highlightcolor='red',
                                     bg='white', fg='black', relief='flat')
        self.button_comment = tk.Button(master=self.master, text='Save Comment', command=self.save_comment,
                                        bg='white', fg='black', relief='flat')
        self.button_edit = tk.Button(master=self.master, text='Edit', command=self.edit,
                                        bg='white', fg='black', relief='flat')

        v = tk.StringVar()
        self.entry_comment = tk.Entry(master=self.master, width=100, textvariable=v)
        self.label_comment = tk.Label(master=self.master, text="Comment: ", bg='black', fg='white')
        self.label_top = tk.Label(master=self.master, text=self.code, bg='black', fg='white', font=16)
        self.label_top.bind("<ButtonPress-1>", self.start_move)
        self.label_top.bind("<ButtonRelease-1>", self.stop_move)
        self.label_top.bind("<B1-Motion>", self.on_motion)
        
        self.label_top.grid(column=0, row=0, sticky='n', columnspan=4, rowspan=1)
        self.label_comment.grid(column=0, row=2, sticky='e')
        self.entry_comment.grid(column=1, row=2, columnspan=2, sticky='w', padx=5, pady=2)
        self.entry_comment.focus_set()
        self.button_comment.grid(column=3, row=2, sticky='news', padx=5, pady=2)
        self.button_fail.grid(column=1, row=3, sticky='news', padx=5, pady=2)
        self.button_edit.grid(column=0, row=3, sticky='e', padx=5, pady=2)
        self.button_pass.grid(column=2, row=3, stick='news', padx=5, pady=2)
        self.button_quit.grid(column=3, row=3, sticky='news', padx=5, pady=2)

        for i in range(0, 3):
            self.columnconfigure(i, weight=1)
        for j in range(0, 3):
            self.rowconfigure(j, weight=1)

    def create_figure(self, fig, col=0, row=0, span=4):
        canvas = FigureCanvasTkAgg(fig, self.master)
        canvas.show()
        canvas.get_tk_widget().grid(column=col, row=row, columnspan=span, sticky='news', padx=25, pady=25)
        self.canvas = canvas._tkcanvas
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)

    def _quit(self):
        if self.result is None:
            if messagebox.askyesno("Warning!", "Result not selected. Exit anyway?"):
                self.master.quit()
        else:
            self.save_comment()
            self.master.quit()

    def _pass(self):
        self.button_pass.config(bg='pale green', fg='dark green')
        self.button_fail.config(bg='white', fg='black')
        self.button_edit.config(bg='white', fg='black')
        self.result = 'pass'

    def _fail(self):
        self.button_fail.config(bg='indian red', fg='black')
        self.button_pass.config(bg='white', fg='black')
        self.button_edit.config(bg='white', fg='black')
        self.result = 'fail'

    def edit(self):
        self.button_edit.config(bg='pale green', fg='dark green')
        self.button_fail.config(bg='white', fg='black')
        self.button_pass.config(bg='white', fg='black')
        editted = filedialog.askopenfilename(title='Select final mask')
        self.result = editted

    def save_comment(self):
        self.button_comment.config(text='Comment Saved!', state='disabled')
        self.comment = self.entry_comment.get()
        self.button_comment.after(750, self.reset_comment_button)


    def reset_comment_button(self):
        self.button_comment.config(text='Save Comment', bg='white', fg='black', state='normal')

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def on_motion(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.master.winfo_x() + deltax
        y = self.master.winfo_y() + deltay
        self.master.geometry("+%s+%s" % (x, y))


def qc_tool(figure, code):

    root = tk.Tk()
    root.overrideredirect(True)
    root.attributes('-topmost', True)
    root.minsize(width=854, height=480)
    app = Application(master=root)
    app.code = code
    app.create_widgets()
    app.create_figure(figure)
    app.mainloop()
    result = app.result
    comment = app.comment
    root.destroy()

    return result, comment
