eel.expose(close_window);

function close_window() {
    window.close();
}

document.addEventListener('DOMContentLoaded', function () {
    const pages = document.querySelectorAll('.page');
    const navButtons = document.querySelectorAll('.nav-btn, .back-btn, #enter-app-btn');
    const browseBtn = document.getElementById('browse-btn');
    const sourceFolderInput = document.getElementById('source-folder-input');
    const uwNetIDInput = document.getElementById('uw-net-id-input')
    const runAutomationBtn = document.getElementById('run-automation-btn');
    const seriesCheckboxContainer = document.getElementById('series-checkbox-container');

    function showPage(pageId) {
        pages.forEach(page => {
            page.classList.remove('active');
        });
        document.getElementById(pageId).classList.add('active');
    }

    navButtons.forEach(button => {
        button.addEventListener('click', () => {
            const pageId = button.getAttribute('data-page') || 'app-page';
            showPage(pageId);
        });
    });

    const seriesOptions = [
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
    ];

    seriesOptions.forEach(option => {
        const div = document.createElement('div');
        div.className = 'series-item';
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.id = `series-${option.replace(/ /g, '_')}`;
        checkbox.value = option;
        const label = document.createElement('label');
        label.htmlFor = checkbox.id;
        label.textContent = option;
        div.appendChild(checkbox);
        div.appendChild(label);
        seriesCheckboxContainer.appendChild(div);
    });
    
    browseBtn.addEventListener('click', async () => {
        const folderPath = await eel.select_source_folder()();
        if (folderPath) {
            sourceFolderInput.value = folderPath;
        }
    });

    runAutomationBtn.addEventListener('click', () => {
        const uwNetID = uwNetIDInput.value;
        const sourceDir = sourceFolderInput.value;
        const selectedSeries = [];
        seriesCheckboxContainer.querySelectorAll('input[type="checkbox"]:checked').forEach(cb => {
            selectedSeries.push(cb.value);
        });

        if (!uwNetID) {
            alert("Please type in your UW Net ID.");
            return;
        }

        if (!sourceDir) {
            alert("Please select a source folder.");
            return;
        }
        if (selectedSeries.length === 0) {
            alert("Please select at least one series to parse.");
            return;
        }

        runAutomationBtn.disabled = true;
        update_status("Starting processing...");
        document.getElementById('parse-progress').value = 0;
        document.getElementById('clean-progress').value = 0;
        document.getElementById('upload-progress').value = 0;
        document.getElementById('parse-progress-label').textContent = 'Parsing Series Progress';
        document.getElementById('clean-progress-label').textContent = 'Cleaning Previous UW Net ID Folder Progress'
        document.getElementById('upload-progress-label').textContent = 'Uploading to OSCAR Progress';

        eel.start_processing(uwNetID, sourceDir, selectedSeries);
    });

    eel.expose(update_progress);
    function update_progress(bar, value, total) {
        const progressBar = document.getElementById(`${bar}-progress`);
        progressBar.max = total;
        progressBar.value = value;
    }

    eel.expose(update_progress_label);
    function update_progress_label(bar, text) {
        document.getElementById(`${bar}-progress-label`).textContent = text;
    }

    eel.expose(update_status);
    function update_status(message) {
        document.getElementById('status-message').textContent = `Status: ${message}`;
    }
    
    eel.expose(processing_finished);
    function processing_finished() {
        runAutomationBtn.disabled = false;
    }
});