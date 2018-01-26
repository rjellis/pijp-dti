import os
import subprocess
import shutil

import numpy as np
import nibabel as nib
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from pijp import util
from pijp_dti.nifti_io import rescale

ROW_SIZE = 7
COLUMN_SIZE = 3


class Application(tk.Frame):

    def __init__(self, code, img, auto_mask, final_mask, step, master):
        tk.Frame.__init__(self, master)

        master.columnconfigure(0, weight=1)
        master.protocol("WM_DELETE_WINDOW", self.wm_quit)
        for i in range(0, ROW_SIZE):
            master.rowconfigure(i, weight=1)

        self.code = code
        self.img = img
        self.auto_mask = auto_mask
        self.final_mask = final_mask
        self.step = step
        self.default_bg = 'black'
        self.default_fg = 'white'
        self.default_button_bg = 'LightCyan4'
        self.default_button_fg = 'white'

        # Matplotlib stuff
        self.index = 0
        self.image_dat = nib.load(self.img).get_data()
        self.mask_dat = nib.load(self.final_mask).get_data()
        self.masked = None
        self.fig = plt.figure()
        self.fig.set_facecolor(self.default_bg)
        self.fig.tight_layout()
        self.projection = None
        self.alpha = 0.5

        # Base Frame Settings
        self.result = None
        self.comment = ''
        self.x = None
        self.y = None
        self.scale = 1

        # Widget Initialization
        self.canvas = tk.Canvas(master=self.master)
        self.button_quit = tk.Button(master=self.master)
        self.button_submit = tk.Button(master=self.master)
        self.button_pass = tk.Button(master=self.master)
        self.button_edit = tk.Button(master=self.master)
        self.button_fail = tk.Button(master=self.master)
        self.button_open = tk.Button(master=self.master)
        self.button_skip = tk.Button(master=self.master)
        self.button_reset = tk.Button(master=self.master)
        self.entry_comment = tk.Entry(master=self.master)
        self.label_step = tk.Label(master=self.master)
        self.label_top = tk.Label(master=self.master)
        self.label_slice = tk.Label(master=self.master)
        self.slider = tk.Scale(master=self.master)

    def create_widgets(self):

        v = tk.StringVar(value='Enter a comment:')

        # Configuration
        self.master.config(background=self.default_bg)
        self.button_open.config(fg=self.default_fg, bg=self.default_bg,
                                text='Open in FSLView', command=self.open_mask_editor)
        self.button_reset.config(fg='red4', bg='salmon',
                                 highlightbackground='red4', highlightthickness=3,
                                 text='Reset Mask', command=self.reset_mask)
        self.button_pass.config(fg=self.default_button_fg, bg=self.default_button_bg,
                                activebackground='lightgreen', activeforeground='white',
                                text='Pass', command=self._pass,)
        self.button_fail.config(fg=self.default_button_fg, bg=self.default_button_bg,
                                activebackground='indian red', activeforeground='white',
                                text='Fail', command=self._fail)
        self.button_edit.config(fg=self.default_button_fg, bg=self.default_button_bg,
                                activebackground='lightgoldenrod', activeforeground='black',
                                text='Edited', command=self.edit)
        self.button_submit.config(fg='green', bg=self.default_bg,
                                  highlightbackground='green',
                                  text='Submit', command=self.submit)
        self.button_quit.config(fg='red', bg=self.default_bg,
                                highlightbackground='red',
                                text='Quit', command=self._quit)
        self.button_skip.config(fg='goldenrod', bg=self.default_bg,
                                highlightbackground='goldenrod',
                                text='Skip', command=self.skip)
        self.entry_comment.config(textvariable=v, foreground='gray')
        self.label_top.config(fg=self.default_fg, bg=self.default_bg, text=self.code, font=16)
        self.label_step.config(fg='lightgreen', bg=self.default_bg, text=self.step)
        self.label_slice.config(fg='lightgreen', bg=self.default_bg, text='Slice {}'.format(self.index))
        self.slider.config(fg=self.default_fg, bg=self.default_bg, from_=0, to=1, resolution=0.1, orient='horizontal',
                           command=self.change_alpha, sliderrelief='flat', label='Opacity')
        self.slider.set(self.alpha)

        if self.step == 'SegQC':
            self.button_pass.config(text='Pass Segmentation')
            self.button_fail.config(text='Fail Segmentation')
            self.button_edit.config(state='disabled')
            self.button_reset.config(state='disabled')
        if self.step == 'WarpQC':
            self.button_pass.config(text='Pass Warping')
            self.button_fail.config(text='Fail Warping')
            self.button_edit.config(state='disabled')
            self.button_reset.config(state='disabled')
        if self.step == 'MaskQC':
            self.button_pass.config(text='Pass Auto Mask')
            self.button_fail.config(text='Fail Auto Mask')
            self.button_edit.config(state='normal')
            if not masks_are_same(self.auto_mask, self.final_mask):
                self.edit()

        # Griding
        self.grid(rowspan=ROW_SIZE, columnspan=COLUMN_SIZE, padx=5, pady=5, ipadx=10, ipady=10)
        self.label_slice.grid(column=0, row=0, sticky='news', padx=5, pady=5)
        self.label_top.grid(column=1, row=0, sticky='ew', padx=5, pady=5, columnspan=2)
        self.label_step.grid(column=3, row=0, sticky='ew', padx=5, pady=5, columnspan=1)
        self.button_open.grid(column=2, row=1, sticky='ew', pady=0, ipadx=5, ipady=10, columnspan=2)
        self.button_reset.grid(column=1, row=1, sticky='w', padx=0, ipadx=0, ipady=0, columnspan=1)
        self.button_pass.grid(column=2, row=2, stick='ew', pady=0, ipadx=5, ipady=10, columnspan=2)
        self.button_edit.grid(column=2, row=3, sticky='ew', pady=0, ipadx=5, ipady=10, columnspan=2)
        self.button_fail.grid(column=2, row=4, sticky='ew', pady=0, ipadx=5, ipady=10, columnspan=2)
        self.entry_comment.grid(column=1, row=5, sticky='sew', padx=5, pady=10, columnspan=3)
        self.button_submit.grid(column=1, row=6, sticky='ew', padx=5, pady=0, ipady=10, ipadx=10, columnspan=1)
        self.button_skip.grid(column=2, row=6,  sticky='ew', padx=5, pady=0, ipady=10, ipadx=10, columnspan=1)
        self.button_quit.grid(column=3, row=6, sticky='ew', padx=5, pady=0, ipady=10, ipadx=20, columnspan=1)
        self.slider.grid(column=0, row=8, sticky='w', columnspan=1, padx=20, pady=5)

        # Event Bindings
        self.entry_comment.bind("<Key>", self.change_comment_text_color_and_clear)
        self.master.bind_all("<Button-4>", self.scroll_fig_forward)
        self.master.bind_all("<Button-5>", self.scroll_fig_backward)
        self.slider.bind("<ButtonRelease-1>", self.refresh_fig)

        # Miscellaneous Settings
        self.winfo_toplevel().title("QC Tool")
        ttk.Sizegrip(self.master).grid(column=999, row=999, sticky='se')

        for i in range(0, COLUMN_SIZE):
            self.columnconfigure(i, weight=1)
        for j in range(0, ROW_SIZE):
            self.rowconfigure(j, weight=1)

    def create_figure(self, col=0, row=1, cspan=1, rspan=7):
        self.canvas = FigureCanvasTkAgg(self.fig, self.master)
        self.canvas.show()
        self.canvas.get_tk_widget().grid(column=col, row=row, columnspan=cspan, rowspan=rspan, sticky='news', padx=25,
                                         pady=25)
        self.canvas.get_tk_widget().bind("<ButtonPress-1>", self.start_move)
        self.canvas.get_tk_widget().bind("<ButtonRelease-1>", self.stop_move)
        self.canvas.get_tk_widget().bind("<B1-Motion>", self.on_motion)
        self.canvas = self.canvas._tkcanvas

    def draw_fig(self):
        self.image_dat = rescale(self.image_dat)
        self.image_dat = np.stack((self.image_dat, self.image_dat, self.image_dat), axis=-1)
        self.masked = mask_image(self.image_dat, self.mask_dat, hue=[1, 0, 0], alpha=self.alpha)
        self.index = self.masked.shape[2]//2
        self.projection = plt.imshow(np.rot90(self.masked[:, :, self.index, :], 1), interpolation=None)
        self.label_slice.config(text='Slice {}'.format(self.index))
        self.fig.tight_layout()

    def _pass(self):
        if not masks_are_same(self.auto_mask, self.final_mask) and self.step == 'MaskQC':
            messagebox.showerror("Error", "Edits detected!")
        else:
            self.result = 'pass'
            self.button_pass.config(bg='green', fg='white')
            self.button_fail.config(bg=self.default_button_bg, fg=self.default_button_fg)
            self.button_edit.config(bg=self.default_button_bg, fg=self.default_button_fg)

    def _fail(self):
        if not masks_are_same(self.auto_mask, self.final_mask) and self.step == 'MaskQC':
            messagebox.showerror("Error", "Edits detected!")
        else:
            self.result = 'fail'
            self.button_fail.config(bg='red', fg='white')
            self.button_pass.config(bg=self.default_button_bg, fg=self.default_button_fg)
            self.button_edit.config(bg=self.default_button_bg, fg=self.default_button_fg)

    def edit(self):
        if masks_are_same(self.auto_mask, self.final_mask):
            if messagebox.askyesno("QC Tool", "No edits detected!\nWould you like to open FSLView?",
                                   parent=self.master):
                self.open_mask_editor()
        else:
            self.result = 'edit'
            self.button_edit.config(bg='goldenrod', fg='black')
            self.button_fail.config(bg=self.default_button_bg, fg=self.default_button_fg)
            self.button_pass.config(bg=self.default_button_bg, fg=self.default_button_fg)

    def _quit(self):
        if self.result:
            if messagebox.askokcancel("QC Tool", "Quit without submitting?", parent=self.master):
                self.result = "cancelled"
                self.comment = "Exited"
                self.master.quit()
        else:
            self.master.quit()
            self.result = "cancelled"
            self.comment = "Exited"

    def submit(self):
        if self.result is None:
            messagebox.showerror("Error", "Result not selected!", parent=self.master)

        else:
            if messagebox.askokcancel("QC Tool", "Are you sure you want to submit?", parent=self.master):
                if self.comment != 'Enter a comment:':
                    self.comment = self.entry_comment.get()
                self.master.quit()

    def skip(self):
        if messagebox.askokcancel("QC Tool", "Are you sure you want to skip?"):
            self.result = 'skipped'
            self.master.quit()

    def wm_quit(self):
        if self.result:
            if messagebox.askyesno("QC Tool", "Save result before exiting?", parent=self.master):
                self.master.quit()
            else:
                self.result = "cancelled"
                self.comment = "Exited"
                self.master.quit()
        else:
            self.result = "cancelled"
            self.comment = "Exited"
            self.master.quit()

    def open_mask_editor(self):
        p = open_mask_editor(self.img, self.final_mask, self.step)
        p.wait()
        self.refresh_fig()

    def reset_mask(self):
        if messagebox.askokcancel("QC Tool", "Are you sure you want to reset the mask?\nAll edits will be lost.",
                                  icon="warning", parent=self.master):
                shutil.copyfile(self.auto_mask, self.final_mask)
                self.button_fail.config(bg=self.default_button_bg, fg=self.default_button_fg)
                self.button_pass.config(bg=self.default_button_bg, fg=self.default_button_fg)
                self.button_edit.config(bg=self.default_button_bg, fg=self.default_button_fg)
                self.result = None
                self.refresh_fig()

    def refresh_fig(self, event=None):
        self.mask_dat = nib.load(self.final_mask).get_data()
        self.image_dat = nib.load(self.img).get_data()
        self.image_dat = rescale(self.image_dat)
        self.image_dat = np.stack((self.image_dat, self.image_dat, self.image_dat), axis=-1)
        self.masked = mask_image(self.image_dat, self.mask_dat, hue=[1, 0, 0], alpha=self.alpha)
        self.projection.set_data(np.rot90(self.masked[:, :, self.index, :], 1))
        self.fig.canvas.draw()

    def change_alpha(self, event):
        self.alpha = self.slider.get()

    def scroll_fig_forward(self, event):
        self.index += 1
        if self.index >= self.masked.shape[2]:
            self.index = 0
        self.projection.set_data(np.rot90(self.masked[:, :, self.index, :], 1))
        self.fig.canvas.draw()
        self.label_slice.config(text='Slice {}'.format(self.index))

    def scroll_fig_backward(self, event):
        self.index -= 1
        if self.index <= 0:
            self.index = self.masked.shape[2] - 1
        self.projection.set_data(np.rot90(self.masked[:, :, self.index, :], 1))
        self.fig.canvas.draw()
        self.label_slice.config(text='Slice {}'.format(self.index))

    def change_comment_text_color_and_clear(self, event):
        self.entry_comment.config(foreground='black')
        if self.entry_comment.get() == 'Enter a comment:':
            self.entry_comment.delete(0, 'end')

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


def center_window(master):
    master.update_idletasks()
    x = master.winfo_width()
    y = master.winfo_height()
    w = master.winfo_screenwidth()
    h = master.winfo_screenheight()
    x_off = int(w/2 - x/2)
    y_off = int(h/2 - y/2)
    master.geometry("{:d}x{:d}{:+d}{:+d}".format(0, 0, x_off, y_off))


def get_mask_editor():
    mask_editor = util.configuration['fslview']
    if not os.path.exists(mask_editor):
        raise Exception("fslview not found")
    return mask_editor


def open_mask_editor(img, mask, step):
        mask_editor = get_mask_editor()
        if step == 'WarpQC':
            cmap = 'Random-Rainbow'
        else:
            cmap = 'Red'

        cmd = "{mask_editor} -m single {img} {overlay} -t 0.5 -l {cmap}".format(mask_editor=mask_editor, img=img,
                                                                                overlay=mask, cmap=cmap)
        args = cmd.split()
        return subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def masks_are_same(auto_mask, final_mask):
    auto_mask_dat = nib.load(auto_mask).get_data()
    final_mask_dat = nib.load(final_mask).get_data()

    return np.array_equal(auto_mask_dat, final_mask_dat)


def mask_image(img, mask, hue, alpha=1):
    """
    overlay a binary mask on an image
    Args:
        img (ndarray):
        mask (ndarray): boolean or binary array to overlay on img
        hue (list or tuple or ndarray shape [3]): RBG 3-vector
        alpha (float): alpha level of overlay
    Returns:
        ndarray : masked img
    """
    factor = np.multiply(hue, alpha)
    img[mask.astype('bool'), ..., 0] = (1 - alpha) * img[mask.astype('bool'), ..., 0] + factor[0]
    img[mask.astype('bool'), ..., 1] = (1 - alpha) * img[mask.astype('bool'), ..., 1] + factor[1]
    img[mask.astype('bool'), ..., 2] = (1 - alpha) * img[mask.astype('bool'), ..., 2] + factor[2]
    return img


def run_qc_interface(code, img, auto_mask, final_mask, step):
    """Opens a GUI for reviewing an image with an overlay
    Args:
        code (string): The code of the case being reviewed
        img (string): The path to the base Nifti image
        auto_mask (string): The path to the overlaid Nifti image
        final_mask (string): The path to the copied auto_mask (allows for editing)
        step (string): The step of QC being run
    Returns:
        result (string): The result selected in the UI (pass, fail, edit, cancelled)
        comment (string): The text entered in the UI's comment entry box
    """
    root = tk.Tk()
    root.minsize(1280, 720)
    center_window(root)
    app = Application(code, img, auto_mask, final_mask, step, root)
    app.create_widgets()
    app.create_figure()
    app.draw_fig()
    app.mainloop()
    result = app.result
    comment = app.comment
    if comment == 'Enter a comment:':
        comment = None
    root.destroy()
    return result, comment
