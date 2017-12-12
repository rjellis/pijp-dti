import tkinter as tk
from tkinter import messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.result = None
        self.comment = ''
        self.path = ''
        master.columnconfigure(0, weight=1)
        master.rowconfigure(0, weight=1)
        self.grid(stick="news")

    def create_widgets(self):
        self.winfo_toplevel().title("QC Tool")
        self.button_quit = tk.Button(master=self.master, text='Exit', command=self._quit)
        self.button_pass = tk.Button(master=self.master, text='Pass', command=self._pass, highlightcolor='green')
        self.button_fail = tk.Button(master=self.master, text='Fail', command=self._fail, highlightcolor='red')
        self.button_path = tk.Button(master=self.master, text='Copy Path to Clipboard', command=self._get_path)
        self.button_comment = tk.Button(master=self.master, text='Save Comment', command=self._save_comment)

        v = tk.StringVar()
        self.entry_comment = tk.Entry(master=self.master, width=100, textvariable=v)
        self.label_comment = tk.Label(master=self.master, text="Comment: ")
        self.label_path = tk.Label(master=self.master, text="Path: ")

        self.text_path = tk.Text(master=self.master, width=100, height=1)
        self.text_path.insert('1.0', self.path)

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

        if self.result is None:
            if messagebox.askyesno("Warning!", "Result not selected. Exit anyway?"):
                self.quit()
        else:
            self.quit()
            self.destroy()

    def _pass(self):
        self.button_pass.config(bg='green', fg='white')
        self.button_fail.config(bg='#d9d9d9', fg='black')
        self.result = 'pass'

    def _fail(self):
        self.button_fail.config(bg='red', fg='white')
        self.button_pass.config(bg='#d9d9d9', fg='black')
        self.result = 'fail'

    def _get_path(self):
        self.master.clipboard_clear()
        self.master.clipboard_append(self.text_path.get('1.0', 'end-1c'))
        self.button_path.config(text='Copied!', bg='green', fg='white')

    def _save_comment(self):
        self.button_comment.config(text='Saved!', bg='green', fg='white')
        self.comment = self.entry_comment.get()


def run_qc_interface(figure, path=None):
    root = tk.Tk()
    app = Application(master=root)
    app.path = path
    app.create_widgets()
    app.create_figure(figure)
    app.mainloop()
    result = app.result
    comment = app.comment
    app.destroy()

    return result, comment
