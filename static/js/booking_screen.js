document.addEventListener('DOMContentLoaded', function() {
    const bookingApp = document.getElementById('booking-app');
    if (!bookingApp) return;

    // Initialize data from attributes
    const slots = JSON.parse(bookingApp.dataset.slots || '[]');
    const screenCode = bookingApp.dataset.screenCode;
    const currencySymbol = bookingApp.dataset.currencySymbol;
    const pricePerMinute = parseFloat(bookingApp.dataset.pricePerMinute);
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;

    let maxAvailablePlays = 0;
    let availabilityData = null;

    // Helper functions
    function updateSlotVisibility() {
        const contentType = document.querySelector('input[name="content_type"]:checked')?.value || 'image';

        document.querySelectorAll('.slot-radio').forEach(input => {
            const type = input.dataset.type;
            const parentLabel = input.parentElement;
            if (type === contentType) {
                parentLabel.style.display = 'block';
            } else {
                parentLabel.style.display = 'none';
                if (input.checked) {
                    input.checked = false;
                }
            }
        });

        const checkedSlot = document.querySelector(`input[name="slot_duration"]:checked`);
        if (!checkedSlot || checkedSlot.dataset.type !== contentType) {
            const firstVisibleSlot = document.querySelector(`input[name="slot_duration"][data-type="${contentType}"]`);
            if (firstVisibleSlot) {
                firstVisibleSlot.checked = true;
            }
        }
    }

    function updateRadioStyles() {
        document.querySelectorAll('input[name="content_type"]').forEach(input => {
            const label = input.closest('label');
            const indicator = label.querySelector('.content-type-indicator');
            if (input.checked) {
                label.classList.add('border-primary-500', 'bg-primary-50');
                if (indicator) indicator.classList.add('bg-primary-500', 'border-primary-500');
            } else {
                label.classList.remove('border-primary-500', 'bg-primary-50');
                if (indicator) indicator.classList.remove('bg-primary-500', 'border-primary-500');
            }
        });

        document.querySelectorAll('input[name="period_id"]').forEach(input => {
            const label = input.closest('label');
            if (input.checked) {
                label.classList.add('border-primary-500', 'bg-primary-50');
            } else {
                label.classList.remove('border-primary-500', 'bg-primary-50');
            }
        });

        document.querySelectorAll('.slot-radio').forEach(input => {
            const label = input.nextElementSibling;
            if (input.checked) {
                label.classList.add('border-primary-500', 'bg-primary-50');
            } else {
                label.classList.remove('border-primary-500', 'bg-primary-50');
            }
        });
    }

    function updatePlaysPerDay() {
        const numPlays = parseInt(document.getElementById('num_plays').value) || 0;
        const numDays = parseInt(document.getElementById('num_days_display').textContent) || 1;
        const playsPerDay = Math.ceil(numPlays / numDays);
        document.getElementById('plays_per_day').textContent = playsPerDay;
    }

    function updatePrice() {
        const periodMultiplier = parseFloat(document.querySelector('input[name="period_id"]:checked')?.dataset.multiplier || 1);
        const numPlays = parseInt(document.getElementById('num_plays').value) || 0;

        const basePrice = parseFloat(document.querySelector('input[name="slot_duration"]:checked')?.dataset.price || 0);
        const pricePerPlay = basePrice * periodMultiplier;
        const total = pricePerPlay * numPlays;

        document.getElementById('pricePerPlay').textContent = pricePerPlay.toFixed(2) + currencySymbol;
        document.getElementById('displayNumPlays').textContent = numPlays;
        document.getElementById('totalPrice').textContent = total.toFixed(2) + currencySymbol;
    }

    async function fetchAvailability() {
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;

        if (!startDate || !endDate) return;

        const contentType = document.querySelector('input[name="content_type"]:checked')?.value || 'image';
        const slotDuration = parseInt(document.querySelector('input[name="slot_duration"]:checked')?.value || 10);
        const periodId = document.querySelector('input[name="period_id"]:checked')?.value || '';

        document.getElementById('loading_indicator').classList.remove('hidden');
        document.getElementById('availability_section').classList.remove('hidden');

        try {
            const response = await fetch(`/book/${screenCode}/availability`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': csrfToken
                },
                body: JSON.stringify({
                    start_date: startDate,
                    end_date: endDate,
                    content_type: contentType,
                    slot_duration: slotDuration,
                    period_id: periodId || null
                })
            });

            const data = await response.json();

            if (data.error) {
                console.error('Availability error:', data.error);
                fallbackCalculation(startDate, endDate);
            } else {
                availabilityData = data;
                maxAvailablePlays = data.availability?.available_plays || 100;

                document.getElementById('num_days_display').textContent = data.availability?.num_days || 0;
                document.getElementById('available_plays_display').textContent = maxAvailablePlays;
                document.getElementById('total_seconds_display').textContent = data.availability?.total_available_seconds || 0;
                document.getElementById('max_plays_text').textContent = maxAvailablePlays;

                const recommendedPlays = Math.min(data.recommended_plays || 20, maxAvailablePlays);
                const numPlaysInput = document.getElementById('num_plays');
                numPlaysInput.value = recommendedPlays;
                numPlaysInput.max = maxAvailablePlays;
                document.getElementById('calculated_plays').value = recommendedPlays;

                document.getElementById('plays_section').classList.remove('hidden');
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('submitHint').classList.add('hidden');

                updatePlaysPerDay();
                updatePrice();
            }
        } catch (error) {
            console.error('Error fetching availability:', error);
            fallbackCalculation(startDate, endDate);
        }

        document.getElementById('loading_indicator').classList.add('hidden');
    }

    function fallbackCalculation(startDate, endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const numDays = Math.ceil(Math.abs(end - start) / (1000 * 60 * 60 * 24)) + 1;

        maxAvailablePlays = numDays * 100;

        document.getElementById('num_days_display').textContent = numDays;
        document.getElementById('available_plays_display').textContent = maxAvailablePlays;
        document.getElementById('total_seconds_display').textContent = numDays * 3600;
        document.getElementById('max_plays_text').textContent = maxAvailablePlays;

        const recommendedPlays = Math.min(numDays * 20, maxAvailablePlays);
        const numPlaysInput = document.getElementById('num_plays');
        numPlaysInput.value = recommendedPlays;
        numPlaysInput.max = maxAvailablePlays;
        document.getElementById('calculated_plays').value = recommendedPlays;

        document.getElementById('plays_section').classList.remove('hidden');
        document.getElementById('submitBtn').disabled = false;
        document.getElementById('submitHint').classList.add('hidden');

        updatePlaysPerDay();
        updatePrice();
    }

    function onStateChange() {
        updateSlotVisibility();
        updateRadioStyles();
        if (document.getElementById('start_date').value && document.getElementById('end_date').value) {
            fetchAvailability();
        }
        updatePrice();
    }

    function onDatesChange() {
        const startDate = document.getElementById('start_date').value;
        const endDate = document.getElementById('end_date').value;

        if (startDate && endDate) {
            if (new Date(endDate) < new Date(startDate)) {
                document.getElementById('end_date').value = startDate;
            }
            fetchAvailability();
        } else {
            document.getElementById('availability_section').classList.add('hidden');
            document.getElementById('plays_section').classList.add('hidden');
            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitHint').classList.remove('hidden');
        }
    }

    function validateAndUpdatePrice() {
        const numPlaysInput = document.getElementById('num_plays');
        let numPlays = parseInt(numPlaysInput.value) || 1;

        if (numPlays < 1) numPlays = 1;
        if (numPlays > maxAvailablePlays && maxAvailablePlays > 0) numPlays = maxAvailablePlays;

        numPlaysInput.value = numPlays;
        document.getElementById('calculated_plays').value = numPlays;

        updatePlaysPerDay();
        updatePrice();
    }

    function changePlayCount(delta) {
        const input = document.getElementById('num_plays');
        let newValue = parseInt(input.value) + delta;

        if (newValue < 1) newValue = 1;
        if (newValue > maxAvailablePlays && maxAvailablePlays > 0) newValue = maxAvailablePlays;

        input.value = newValue;
        document.getElementById('calculated_plays').value = newValue;

        updatePlaysPerDay();
        updatePrice();
    }

    function previewFile(input) {
        const file = input.files[0];
        if (file) {
            document.getElementById('uploadZone').classList.add('hidden');
            document.getElementById('contentPreviewSection').classList.remove('hidden');
            document.getElementById('fileName').textContent = file.name;

            const previewImage = document.getElementById('previewImage');
            const previewVideo = document.getElementById('previewVideo');

            if (file.type.startsWith('image/')) {
                previewImage.classList.remove('hidden');
                previewVideo.classList.add('hidden');
                previewImage.src = URL.createObjectURL(file);
            } else if (file.type.startsWith('video/')) {
                previewVideo.classList.remove('hidden');
                previewImage.classList.add('hidden');
                previewVideo.src = URL.createObjectURL(file);
            }
        }
    }

    function changeFile() {
        document.getElementById('uploadZone').classList.remove('hidden');
        document.getElementById('contentPreviewSection').classList.add('hidden');
        document.getElementById('fileInput').value = '';
        document.getElementById('previewImage').src = '';
        document.getElementById('previewVideo').src = '';
    }

    // Attach Event Listeners

    // Content Type
    document.querySelectorAll('input[name="content_type"]').forEach(el => {
        el.addEventListener('change', onStateChange);
    });

    // Slot Duration
    document.querySelectorAll('input[name="slot_duration"]').forEach(el => {
        el.addEventListener('change', onStateChange);
    });

    // Period ID
    document.querySelectorAll('input[name="period_id"]').forEach(el => {
        el.addEventListener('change', onStateChange);
    });

    // Dates
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');

    if(startDateInput) startDateInput.addEventListener('change', onDatesChange);
    if(endDateInput) endDateInput.addEventListener('change', onDatesChange);
    if(startTimeInput) startTimeInput.addEventListener('change', onDatesChange);
    if(endTimeInput) endTimeInput.addEventListener('change', onDatesChange);

    // Play Count Buttons
    const minusBtn = document.getElementById('decrease-plays-btn');
    const plusBtn = document.getElementById('increase-plays-btn');
    if (minusBtn) minusBtn.addEventListener('click', () => changePlayCount(-10));
    if (plusBtn) plusBtn.addEventListener('click', () => changePlayCount(10));

    // Play Count Input
    const numPlaysInput = document.getElementById('num_plays');
    if (numPlaysInput) numPlaysInput.addEventListener('change', validateAndUpdatePrice);

    // File Input
    const fileInput = document.getElementById('fileInput');
    if (fileInput) fileInput.addEventListener('change', function() { previewFile(this); });

    // Change File Button
    const changeFileBtn = document.getElementById('change-file-btn');
    if (changeFileBtn) changeFileBtn.addEventListener('click', changeFile);


    // Initial Setup
    updateSlotVisibility();
    updateRadioStyles();

    // Set dates
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (startDateInput && endDateInput) {
        const todayStr = new Date().toISOString().split('T')[0];
        startDateInput.min = todayStr;
        endDateInput.min = todayStr;
    }
});
