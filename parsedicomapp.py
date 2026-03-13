import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import cleanup
import parsedicom
import uploadtooscar
import logging
import sv_ttk
from PIL import Image, ImageTk

logging.basicConfig(level=logging.INFO)

class App(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=15)
        self.pack(fill="both", expand=True)
        self.root = root
        self.root.title("AASK")

        self.source_dir = tk.StringVar()
        self.worker_thread = tk.StringVar()
        self.uw_id = tk.StringVar()

        self.dark_mode_enabled = tk.BooleanVar(value=False)

        # Keep track of current frame
        self.current_frame = None

        # Show first pane
        self.show_pane1()
    
    def show_pane1(self):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self)
        self.current_frame.pack(fill="both", expand=True)

        # Load image
        image = Image.open("AASK.png")
        image = image.resize((600, 300))
        tk_image = ImageTk.PhotoImage(image)

        # Keep reference so it's not garbage collected
        self.current_frame.img = tk_image

        # Image Label
        img_label = tk.Label(self.current_frame, image=tk_image)
        img_label.pack(pady=0)

        # Next Button
        next_btn = tk.Button(self.current_frame, text="Next →", command=self.show_pane2)
        next_btn.pack(pady=0)

    def show_pane2(self):
        if self.current_frame:
            self.current_frame.destroy()

        self.current_frame = tk.Frame(self)
        self.current_frame.pack(fill="both", expand=True)

        self.create_widgets()
    
    def reset_progress_bar_widgets(self):
        self.progress_series_selection["value"] = 0
        self.progress_prepare_oscar["value"] = 0
        self.progress_upload_to_oscar["value"] = 0
        self.progress_series_selection_label.after(0, self.progress_series_selection_label.config, {'text': "Parsing Series" })
        self.progress_prepare_oscar_label.after(0, self.progress_prepare_oscar_label.config, {'text': "Emptying Previous OSCAR Folder" })
        self.progress_upload_to_oscar_label.after(0, self.progress_upload_to_oscar_label.config, {'text': "Uploading to OSCAR" })

    def create_widgets(self):
        """
        Creates widgets for Tkinter GUI
        """
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X)

        title_label = ttk.Label(header_frame, text="AASK", font=("Arial", 16, "bold"))
        title_label.pack(side=tk.LEFT)
        
        theme_toggle = ttk.Checkbutton(
            header_frame, 
            text="Dark Mode", 
            variable=self.dark_mode_enabled,
            command=self.toggle_theme,
            style="Switch.TCheckbutton"
        )
        theme_toggle.pack(side=tk.RIGHT)

        main_frame = tk.Frame(self.root, padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        id_frame = tk.LabelFrame(main_frame, text="1. Type in your UW Net ID", padx=5, pady=5)
        id_frame.pack(pady=5, fill=tk.X, expand=True)
        tk.Entry(id_frame, textvariable=self.uw_id, width=45).grid(row=0, column=1, sticky=tk.EW)
        id_frame.columnconfigure(1, weight=1)

        folder_frame = tk.LabelFrame(main_frame, text="2. Select Folder", padx=5, pady=5)
        folder_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(folder_frame, text="Source Folder:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        tk.Entry(folder_frame, textvariable=self.source_dir, width=45).grid(row=0, column=1, sticky=tk.EW)
        tk.Button(folder_frame, text="Browse...", command=self.browse_source).grid(row=0, column=2, padx=5)

        folder_frame.columnconfigure(1, weight=1)

        series_frame = tk.LabelFrame(main_frame, text="3. Select Series", padx=2, pady=1)
        series_frame.pack(fill=tk.BOTH, pady=5, expand=True)

        canvas = tk.Canvas(series_frame)
        scrollbar = tk.Scrollbar(series_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


        self.series_options = [
            "70 keV", "A/P 2.5", "Axial KUB", "THIN", "COR", "SAG", "VUE", "IODINE (WATER)", "STD", "std iMAR", 
            "LUNG", "MIP", "STD WC CAP", "COR WC", "SAG WC", "WC iMAR", "VUE", "MIP CHEST", 
            "STD WC ABD", "iMAR WC", "STD WO", "COR WO", "2.5 STD", "1.25 STD", "2.5 60keV", 
            "1.25 60keV", "120 keV", "STD WC CHEST", "WO iMAR", "STD CHEST", "COR CHEST", 
            "SAG CHEST", "STD WC A/P", "STD A/P", "STD WO CHEST", "2 X 1 STD ART CAP", 
            "1.0 STD ART", "COR ART", "SAG ART", "iMAR ART", "2.0 STD ART ABD/PEL", "iMAR ART", 
            "THIN ART", "THIN VEN", "THIN DELAY", "ART 50keV", "ART IODINE (WATER)", "VEN 70keV", 
            "VEN IODINE (WATER)", "COR VEN", "5 min 70 keV", "ART ABD", "ART iMAR", "WC ABD", 
            "5 MIN DELAY", "COR DELAY", "DELAY iMAR", "NONE", "5min 70keV", "ART", "STD VEN", 
            "SAG VEN", "5MIN", "STD WO HEAD", "BONE WO HEAD", "TRUE AXIAL HEAD", "SAG WO", 
            "0.6 X 0.5 HEAD", "BONE FACE", "STD FACE", "STD ART NECK/CHEST", "BONE C T SPINE FS", 
            "SAG BONE C T SPINE", "COR BONE C T SPINE", "STD ART NECK", "STD WC ABD/PEL", 
            "BONE L SPINE FS", "SAG BONE L SPINE", "COR BONE L SPINE", "0.6 X 0.5 WC ABD/PEL", 
            "STD DELAY ABD", "SAG DELAY", "CYSTO", "COR CYSTO", "SAG CYSTO", "0.6 X 0.5 DELAY"
        ]

        self.series_vars = []
        columns = 4

        for idx, option in enumerate(self.series_options):
            var = tk.BooleanVar()
            chk = tk.Checkbutton(scrollable_frame, text=option, variable=var)
            chk.grid(row=idx // columns, column=idx % columns, sticky='w', padx=2, pady=2)
            self.series_vars.append(var)

        control_frame = tk.LabelFrame(main_frame, text="4. Run Automation", padx=5, pady=5)
        control_frame.pack(fill=tk.X, pady=5)

        self.run_button = tk.Button(control_frame, text="▶ Run Automation", bg="#4CAF50", fg="black", command=self.start_processing)
        self.run_button.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)

        # Parsing series progress bar
        self.progress_series_selection = ttk.Progressbar(root, orient="horizontal", length=250, mode="determinate")
        self.progress_series_selection.pack()
        self.progress_series_selection_label = tk.Label(root, text="Parsing Series")
        self.progress_series_selection_label.pack(expand=True)

        # Preparing OSCAR for upload progress bar
        self.progress_prepare_oscar = ttk.Progressbar(root, orient="horizontal", length=250, mode="determinate")
        self.progress_prepare_oscar.pack()
        self.progress_prepare_oscar_label = tk.Label(root, text="Emptying Previous OSCAR Folder")
        self.progress_prepare_oscar_label.pack(expand=True)

        # Uploading to OSCAR progress bar
        self.progress_upload_to_oscar = ttk.Progressbar(root, orient="horizontal", length=250, mode="determinate")
        self.progress_upload_to_oscar.pack()
        self.progress_upload_to_oscar_label = tk.Label(root, text="Uploading to OSCAR")
        self.progress_upload_to_oscar_label.pack(expand=True)

    def toggle_theme(self):
        if self.dark_mode_enabled.get():
            sv_ttk.set_theme("dark")
        else:
            sv_ttk.set_theme("light")

    def get_selected_series_checkboxes(self):
        return [option for option, var in zip(self.series_options, self.series_vars) if var.get()]
        
    def browse_source(self):
        self.source_dir.set(os.path.normpath(filedialog.askdirectory(title="Select Source DICOM Folder")))

    def start_processing(self):
        if not self.source_dir.get():
            logging.error("Source folder not found")
            return

        self.run_button.config(state=tk.DISABLED)
        self.worker_thread = threading.Thread(target=self.run_file_operations)
        self.worker_thread.start()

    def run_file_operations(self):
        """
        Runs all steps after user clicks 'Run Automation'
        """
        try:
            source = self.source_dir.get()
            output = os.path.dirname(source)
            target = self.get_selected_series_checkboxes()
            uw_id = self.uw_id.get()

            # STEP 1: Run series selection and copy files to output directory next to source
            num_patients = parsedicom.run_parsing_process(source, output, target, self.progress_series_selection, self.progress_series_selection_label)
            logging.info(f"Done parsing the series selection and created {output} directory.")

            # STEP 2: Upload to OSCAR
            local_dir_to_upload = os.path.join(output, parsedicom.OUTPUT_FOLDER_NAME)
            uploadtooscar.upload_folder_sftp(uw_id, local_dir_to_upload, self.progress_upload_to_oscar, self.progress_upload_to_oscar_label, self.progress_prepare_oscar, self.progress_prepare_oscar_label)
            logging.info(f"Done uploading {num_patients} patient files to OSCAR.")

            # STEP 3: Clean up the previous directory for copying series and reset progress bars
            cleanup.remove_series_selection_output_dir(local_dir_to_upload)
            self.reset_progress_bar_widgets()
            logging.info(f"Done cleaning up {local_dir_to_upload} directory created for copying series selection.")

            self.root.after(0, self.processing_finished, f"Files for {num_patients} patients has been uploaded to OSCAR")
        except Exception as e:
            logging.error(str(e))

            # ERROR STEP 1: Clean up the directory created for copying series selection and reset progress bars
            local_dir_to_upload = os.path.join(output, parsedicom.OUTPUT_FOLDER_NAME)
            cleanup.remove_series_selection_output_dir(local_dir_to_upload)
            self.reset_progress_bar_widgets()
            logging.info(f"Done cleaning up {local_dir_to_upload} directory created for copying series selection")

            # ERROR STEP 2: Show error message to user
            self.root.after(0, self.processing_finished, 'Error: ' + str(e))

    def processing_finished(self, status):
        self.run_button.config(state=tk.NORMAL)
        messagebox.showinfo("Status", status)
        
if __name__ == "__main__":
    root = tk.Tk()
    sv_ttk.set_theme("light")
    app = App(root)
    root.mainloop()