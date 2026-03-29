// Pre-fill user data
document.addEventListener('DOMContentLoaded', () => {
    const stored = localStorage.getItem('citizenData');
    if (stored) {
        const data = JSON.parse(stored);
        if (document.getElementById('name')) document.getElementById('name').value = data.name || '';
        if (document.getElementById('email')) document.getElementById('email').value = data.email || '';
        if (document.getElementById('phone')) document.getElementById('phone').value = data.phone || '';
    } else {
        // If not logged in, redirect to login
        if (window.location.pathname === '/report') {
            window.location.href = '/citizen_login';
        }
    }
});

// DOM Elements
const dropArea = document.getElementById('dropArea');
const imageInput = document.getElementById('imageInput');
const imagePreview = document.getElementById('imagePreview');
const previewContainer = document.getElementById('previewContainer');
const uploadIcon = document.getElementById('uploadIcon');
const uploadText = document.getElementById('uploadText');
const reportForm = document.getElementById('reportForm');
const submitBtn = document.getElementById('submitBtn');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorMsg = document.getElementById('errorMsg');
const errorText = document.getElementById('errorText');

// Image Preview and Drag & Drop
if (dropArea && imageInput) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.style.borderColor = 'var(--primary-color)';
            dropArea.style.background = '#e0e7ff';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, () => {
            dropArea.style.borderColor = 'var(--border-color)';
            dropArea.style.background = 'white';
        }, false);
    });

    dropArea.addEventListener('drop', handleDrop, false);
    imageInput.addEventListener('change', handleFiles, false);
}

function handleDrop(e) {
    let dt = e.dataTransfer;
    let files = dt.files;
    imageInput.files = files; // Assign files to input
    handleFiles();
}

function handleFiles() {
    if (imageInput.files && imageInput.files[0]) {
        let reader = new FileReader();
        reader.onload = function(e) {
            imagePreview.src = e.target.result;
            previewContainer.style.display = 'block';
            uploadIcon.style.display = 'none';
            uploadText.style.display = 'none';
            dropArea.style.padding = '1rem';
        }
        reader.readAsDataURL(imageInput.files[0]);
        if(errorMsg) errorMsg.style.display = 'none';
    }
}

function resetImage() {
    imageInput.value = '';
    previewContainer.style.display = 'none';
    uploadIcon.style.display = 'block';
    uploadText.style.display = 'block';
    dropArea.style.padding = '2rem';
}

// Geolocation
function getLocation() {
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    const locationText = document.getElementById('locationText');
    const coordsText = document.getElementById('coordsText');
    const btn = document.getElementById('locationBtn');

    if (navigator.geolocation) {
        btn.innerHTML = '<span class="loader" style="width: 16px; height: 16px; border-width: 2px;"></span> Detecting...';
        btn.disabled = true;
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                latInput.value = lat;
                lonInput.value = lon;
                coordsText.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;

                try {
                    // Reverse geocoding using Nominatim
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                    const data = await response.json();
                    
                    if (data && data.display_name) {
                        locationText.textContent = data.display_name.split(',').slice(0, 3).join(',');
                    } else {
                        locationText.textContent = "Location Founded";
                    }
                } catch (err) {
                    console.error("Reverse geocoding failed:", err);
                    locationText.textContent = "Location Founded";
                }

                btn.innerHTML = '<i class="fa-solid fa-check"></i> Detected';
                btn.classList.replace('btn-outline', 'btn-primary');
                btn.style.background = 'var(--success-color)';
                btn.style.borderColor = 'var(--success-color)';
                btn.style.color = 'white';
            },
            (error) => {
                alert("Error getting location. Please allow location access or try again.");
                btn.innerHTML = '<i class="fa-solid fa-location-crosshairs"></i> Detect Location';
                btn.disabled = false;
            }
        );
    } else {
        alert("Geolocation is not supported by this browser.");
    }
}

// Global state for completed report
let currentReportId = null;

// Form Submission
async function submitReport(e) {
    e.preventDefault();
    
    // Check if location is fetched
    if (!document.getElementById('latitude').value || !document.getElementById('longitude').value) {
        errorText.textContent = "Please capture your GPS location before submitting.";
        errorMsg.style.display = 'block';
        return;
    }

    if (!imageInput.files || !imageInput.files[0]) {
        errorText.textContent = "Please upload an image.";
        errorMsg.style.display = 'block';
        return;
    }

    submitBtn.style.display = 'none';
    loadingIndicator.style.display = 'block';
    errorMsg.style.display = 'none';

    const formData = new FormData(reportForm);

    try {
        const response = await fetch('/api/report', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            // Introduce artificial delay to look like rigorous AI processing
            setTimeout(() => {
                window.location.href = `/result/${data.report_id}`;
            }, 3000); // 3 seconds delay for AI effect
        } else {
            throw new Error(data.error || 'Submission failed');
        }
    } catch (err) {
        loadingIndicator.style.display = 'none';
        submitBtn.style.display = 'block';
        errorText.textContent = err.message;
        errorMsg.style.display = 'block';
    }
}
