import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

ROW_SIZE = 5
COLUMN_SIZE = 5


class Application(tk.Frame):

    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        master.geometry("1280x720")
        master.configure(bg='black')
        master.protocol("WM_DELETE_WINDOW", self._quit)

        # Base Frame Settings
        self.config(bg='black')
        self.result = None
        self.comment = ''
        self.code = ''
        self.x = None
        self.y = None
        self.scale = 1
        self.canvas = None
        self.edit_cmd = None
        self.can_edit = True

        self.button_quit = tk.Button(master=self.master)
        self.button_save_quit = tk.Button(master=self.master)
        self.button_pass = tk.Button(master=self.master)
        self.button_edit = tk.Button(master=self.master)
        self.button_fail = tk.Button(master=self.master)
        self.entry_comment = tk.Entry(master=self.master)
        self.label_comment = tk.Label(master=self.master)
        self.label_top = tk.Label(master=self.master)

    def create_widgets(self):

        fg = 'black'
        bg = 'white'
        relief = 'flat'
        v = tk.StringVar()

        # Configuration
        self.button_quit.config(text='Exit', bg=bg, fg=fg, relief=relief, command=self._quit)
        self.button_save_quit.config(text='Save and Exit', bg=bg, fg=fg, relief=relief, command=self.save_and_exit)
        self.button_pass.config(text='Pass', command=self._pass, bg=bg, fg=fg, relief=relief)
        self.button_fail.config(text='Fail', command=self._fail, bg=bg, fg=fg, relief=relief)
        self.button_edit.config(text='Edit', command=self.edit, bg=bg, fg=fg, relief=relief)
        self.entry_comment.config(textvariable=v)
        self.label_comment.config(text="Comment: ", bg='black', fg='white')
        self.label_top.config(text=self.code, bg='black', fg='white', font=16)

        # Griding
        self.grid(rowspan=ROW_SIZE, columnspan=COLUMN_SIZE, stick="news", padx=5, pady=5)
        self.button_quit.grid(column=4, row=4, sticky='news', padx=5, pady=2)
        self.button_save_quit.grid(column=4, row=3, sticky='news', padx=5, pady=2)
        self.button_pass.grid(column=1, row=4, stick='news', padx=5, pady=2)
        self.button_fail.grid(column=3, row=4, sticky='news', padx=5, pady=2)
        self.button_edit.grid(column=2, row=4, sticky='news', padx=5, pady=2)
        self.entry_comment.grid(column=1, row=3, columnspan=3, sticky='news', padx=5, pady=2)
        self.label_comment.grid(column=0, row=3, sticky='e')
        self.label_top.grid(column=1, row=1, sticky='n', columnspan=4, rowspan=1)

        # Event Bindings
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<ButtonRelease-1>", self.stop_move)
        self.bind("<B1-Motion>", self.on_motion)
        self.label_top.bind("<ButtonPress-1>", self.start_move)
        self.label_top.bind("<ButtonRelease-1>", self.stop_move)
        self.label_top.bind("<B1-Motion>", self.on_motion)

        # Miscellaneous Settings
        self.winfo_toplevel().title("QC Tool")
        self.entry_comment.focus_set()
        ttk.Sizegrip(self.master).grid(column=999, row=999, sticky='se')

        for i in range(0, COLUMN_SIZE):
            self.columnconfigure(i, weight=1)
        for j in range(0, ROW_SIZE):
            self.rowconfigure(j, weight=1)

        if not self.can_edit:
            self.button_edit.config(state='disabled')

    def create_figure(self, fig, col=0, row=0, span=COLUMN_SIZE):
        canvas = FigureCanvasTkAgg(fig, self.master)
        canvas.show()
        canvas.get_tk_widget().grid(column=col, row=row, columnspan=span, sticky='news', padx=25, pady=25)
        self.canvas = canvas._tkcanvas
        self.canvas.bind("<ButtonPress-1>", self.start_move)
        self.canvas.bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.bind("<B1-Motion>", self.on_motion)

    def _quit(self):
        if self.result:
            if messagebox.askyesno("Warning!", "Exit without saving?"):
                self.result = None
                self.comment = "Exited without saving"
                self.master.quit()
        else:
            self.master.quit()
            self.comment = "Exited without saving"

    def save_and_exit(self):
        if self.result is None:
            messagebox.showerror("Error", "Result not selected!")
        else:
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
        self.button_edit.config(bg='yellow', fg='black')
        self.button_fail.config(bg='white', fg='black')
        self.button_pass.config(bg='white', fg='black')
        self.edit_cmd()
        self.result = 'edit'

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


def run_qc_interface(figure, code, edit_cmd=None, edit=True):

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.minsize(width=640, height=480)
    app = Application(master=root)
    app.code = code
    app.edit_cmd = edit_cmd
    app.can_edit = edit
    app.create_widgets()
    app.create_figure(figure)
    app.mainloop()
    result = app.result
    comment = app.comment
    root.destroy()

    return result, comment
