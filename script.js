document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const introScreen = document.getElementById('intro-screen');
    const uploadScreen = document.getElementById('upload-screen');
    const editScreen = document.getElementById('edit-screen');
    
    const startBtn = document.getElementById('start-btn');
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('upload-preview-container');
    const previewImage = document.getElementById('preview-image');
    const changeImageBtn = document.getElementById('change-image-btn');
    const continueBtn = document.getElementById('continue-btn');
    
    const editPanel = document.getElementById('edit-panel');
    const resultsPanel = document.getElementById('results-panel');
    const instructionInput = document.getElementById('instruction');
    const guidanceScaleInput = document.getElementById('guidance-scale');
    const guidanceScaleValue = document.getElementById('guidance-scale-value');
    const inferenceStepsInput = document.getElementById('inference-steps');
    const inferenceStepsValue = document.getElementById('inference-steps-value');
    const backBtn = document.getElementById('back-btn');
    const generateBtn = document.getElementById('generate-btn');
    
    const loadingContainer = document.getElementById('loading-container');
    const resultsContent = document.getElementById('results-content');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const resultImage = document.getElementById('result-image');
    const ssimValue = document.getElementById('ssim-value');
    const psnrValue = document.getElementById('psnr-value');
    const downloadBtn = document.getElementById('download-btn');
    const newEditBtn = document.getElementById('new-edit-btn');
    
    // State
    let currentScreen = 'intro';
    let uploadedFilePath = null;
    let generationTaskId = null;
    let resultImagePath = null;
    let progressInterval = null;
    
    // Navigation Functions
    function showScreen(screenId) {
        // Hide all screens
        introScreen.classList.remove('active');
        uploadScreen.classList.remove('active');
        editScreen.classList.remove('active');
        
        // Show the requested screen
        if (screenId === 'intro') {
            introScreen.classList.add('active');
            currentScreen = 'intro';
        } else if (screenId === 'upload') {
            uploadScreen.classList.add('active');
            currentScreen = 'upload';
        } else if (screenId === 'edit') {
            editScreen.classList.add('active');
            currentScreen = 'edit';
        }
    }
    
    // Event Listeners
    startBtn.addEventListener('click', () => {
        showScreen('upload');
    });
    
    // File Upload
    dropArea.addEventListener('click', () => {
        fileInput.click();
    });
    
    dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('active');
    });
    
    dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('active');
    });
    
    dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('active');
        
        if (e.dataTransfer.files.length) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFileUpload(e.target.files[0]);
        }
    });
    
    changeImageBtn.addEventListener('click', () => {
        previewContainer.classList.add('hidden');
        dropArea.classList.remove('hidden');
        uploadedFilePath = null;
    });
    
    continueBtn.addEventListener('click', () => {
        if (uploadedFilePath) {
            showScreen('edit');
            validateForm();
        }
    });
    
    // Edit Screen
    guidanceScaleInput.addEventListener('input', (e) => {
        guidanceScaleValue.textContent = e.target.value;
    });
    
    inferenceStepsInput.addEventListener('input', (e) => {
        inferenceStepsValue.textContent = e.target.value;
    });
    
    instructionInput.addEventListener('input', validateForm);
    
    backBtn.addEventListener('click', () => {
        showScreen('upload');
    });
    
    generateBtn.addEventListener('click', startGeneration);
    
    // Results Screen
    downloadBtn.addEventListener('click', () => {
        if (resultImagePath) {
            const link = document.createElement('a');
            link.href = resultImagePath;
            link.download = 'redefined_image.png';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    });
    
    newEditBtn.addEventListener('click', resetToNewEdit);
    
    // File Upload Handler
    async function handleFileUpload(file) {
        if (!file.type.startsWith('image/')) {
            alert('Please upload an image file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                uploadedFilePath = data.file_path;
                previewImage.src = uploadedFilePath;
                dropArea.classList.add('hidden');
                previewContainer.classList.remove('hidden');
            } else {
                alert('Error uploading file: ' + data.message);
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error uploading file');
        }
    }
    
    // Validation
    function validateForm() {
        const instruction = instructionInput.value.trim();
        
        if (instruction && uploadedFilePath) {
            generateBtn.disabled = false;
        } else {
            generateBtn.disabled = true;
        }
    }
    
    // Generation
    async function startGeneration() {
        const instruction = instructionInput.value.trim();
        const guidanceScale = guidanceScaleInput.value;
        const inferenceSteps = inferenceStepsInput.value;
        
        if (!instruction || !uploadedFilePath) {
            return;
        }
        
        // Show loading UI
        resultsPanel.classList.remove('hidden');
        loadingContainer.classList.remove('hidden');
        resultsContent.classList.add('hidden');
        
        // Reset progress
        progressFill.style.width = '0%';
        progressText.textContent = 'Processing... 0%';
        
        const formData = new FormData();
        formData.append('file_path', uploadedFilePath);
        formData.append('instruction', instruction);
        formData.append('guidance_scale', guidanceScale);
        formData.append('num_inference_steps', inferenceSteps);
        
        try {
            const response = await fetch('/generate/', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.status === 'processing') {
                generationTaskId = data.task_id;
                startProgressChecking();
            } else {
                alert('Error starting generation: ' + data.message);
                resetUI();
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error starting generation');
            resetUI();
        }
    }
    
    // Progress Checking
    function startProgressChecking() {
        if (progressInterval) {
            clearInterval(progressInterval);
        }
        
        progressInterval = setInterval(checkProgress, 1000);
    }
    
    async function checkProgress() {
        if (!generationTaskId) {
            clearInterval(progressInterval);
            return;
        }
        
        try {
            const response = await fetch(`/progress/${generationTaskId}`);
            const data = await response.json();
            
            if (data.status === 'not_found') {
                clearInterval(progressInterval);
                alert('Generation task not found');
                resetUI();
                return;
            }
            
            // Update progress
            updateProgress(data.progress);
            
            if (data.status === 'completed') {
                clearInterval(progressInterval);
                resultImagePath = data.output_path;
                showResult(data);
            } else if (data.status === 'error') {
                clearInterval(progressInterval);
                alert('Error generating image: ' + data.error);
                resetUI();
            }
        } catch (error) {
            console.error('Error checking progress:', error);
        }
    }
    
    function updateProgress(progress) {
        progressFill.style.width = `${progress}%`;
        progressText.textContent = `Processing... ${progress}%`;
    }
    
    function showResult(data) {
        // Hide loading, show result
        loadingContainer.classList.add('hidden');
        resultsContent.classList.remove('hidden');
        
        // Update UI with result data
        resultImage.src = data.output_path;
        
        if (data.metrics) {
            ssimValue.textContent = data.metrics.ssim.toFixed(4);
            psnrValue.textContent = data.metrics.psnr.toFixed(2) + ' dB';
        }
        
        // Enable download button
        downloadBtn.disabled = false;
    }
    
    function resetUI() {
        resultsPanel.classList.add('hidden');
        loadingContainer.classList.remove('hidden');
        resultsContent.classList.add('hidden');
        
        if (progressInterval) {
            clearInterval(progressInterval);
            progressInterval = null;
        }
    }
    
    function resetToNewEdit() {
        // Reset the right panel
        resultsPanel.classList.add('hidden');
        loadingContainer.classList.remove('hidden');
        resultsContent.classList.add('hidden');
        
        // Optionally clear form inputs
        instructionInput.value = '';
        guidanceScaleInput.value = 12;
        guidanceScaleValue.textContent = '12';
        inferenceStepsInput.value = 50;
        inferenceStepsValue.textContent = '50';
        
        // Disable generate button
        generateBtn.disabled = true;
        
        // Restart from upload screen
        showScreen('upload');
    }

    // Start with intro screen
    showScreen('intro');
});
