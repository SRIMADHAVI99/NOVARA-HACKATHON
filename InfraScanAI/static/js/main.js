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
function setCoords(lat, lon, label, isFallback = false) {
    const latInput = document.getElementById('latitude');
    const lonInput = document.getElementById('longitude');
    const locationText = document.getElementById('locationText');
    const coordsText = document.getElementById('coordsText');
    const btn = document.getElementById('locationBtn');

    latInput.value = lat;
    lonInput.value = lon;
    coordsText.textContent = `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
    locationText.textContent = label || "GPS Location Captured";

    if (isFallback) {
        btn.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> Demo Location';
        btn.className = 'btn btn-outline';
        btn.style.borderColor = 'var(--warning-color)';
        btn.style.color = 'var(--warning-color)';
        btn.style.background = '#fef3c7';
    } else {
        btn.innerHTML = '<i class="fa-solid fa-check"></i> GPS Detected';
        btn.className = 'btn btn-primary';
        btn.style.background = 'var(--success-color)';
        btn.style.borderColor = 'var(--success-color)';
        btn.style.color = 'white';
    }
    btn.disabled = false;
}

function getLocation() {
    const btn = document.getElementById('locationBtn');

    if (navigator.geolocation) {
        btn.innerHTML = '<span class="loader" style="width: 16px; height: 16px; border-width: 2px;"></span> Detecting...';
        btn.disabled = true;
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                let addressLabel = "Live GPS Location Captured";

                try {
                    const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lon}`);
                    const data = await response.json();
                    if (data && data.display_name) {
                        addressLabel = data.display_name.split(',').slice(0, 3).join(',');
                    }
                } catch (err) {
                    console.error("Reverse geocoding failed:", err);
                }

                setCoords(lat, lon, addressLabel, false);
            },
            (error) => {
                console.warn("GPS Geolocation unavailable. Applying explicit demo fallback coordinates.", error);
                setCoords(37.7749, -122.4194, "Fallback location — GPS unavailable", true);
            },
            { timeout: 5000 }
        );
    } else {
        setCoords(37.7749, -122.4194, "Fallback location — GPS unavailable", true);
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
